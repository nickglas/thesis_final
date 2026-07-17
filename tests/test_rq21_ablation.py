import csv
import json
from argparse import Namespace
from pathlib import Path

import pytest

import scripts.run_rq21_paired_benchmark as paired
from scripts.run_rq21_ablation import RQ21AblationRunner


def default_ablation_args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "c0_config": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_plain_nonmesh.yaml",
        "c1_config": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_default_no_authz.yaml",
        "c2_config": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_strict_mtls_no_authz.yaml",
        "c3_config": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_strict_mtls_authz.yaml",
        "results_root": str(tmp_path),
        "client_pod": "benchmark-client",
        "nodepool": "rq15pool",
        "provision": False,
        "provisioner": "terraform",
        "acr_name": "testacr",
        "push": False,
        "build": False,
        "image_ref": None,
        "image_tag": "test",
        "local_image": "thesis-inference:latest",
        "no_auto_push_missing_image": False,
        "resource_group": "rg-test",
        "cluster_name": "cluster-test",
        "location": "swedencentral",
        "node_count": 1,
        "node_vm_size": "Standard_D8s_v3",
        "isolated_node_pools": True,
        "system_nodepool": "systempool",
        "system_node_count": 1,
        "system_node_vm_size": "Standard_D2s_v3",
        "benchmark_taint": "workload=benchmark:NoSchedule",
        "skip_mesh_enable": False,
        "mesh_revision": None,
        "readiness_timeout": None,
        "smoke": False,
        "ablation_passes": 1,
        "order_seed": 42,
        "order": "seeded",
        "preserve_namespaces": False,
        "cleanup_on_failure": False,
        "destroy_infrastructure_on_success": False,
        "destroy_infrastructure_on_failure": False,
        "disable_resource_sampling": False,
        "resource_sample_interval_seconds": 5.0,
        "resource_sample_max_samples": 100000,
        "resource_metric_prime_timeout_seconds": 180.0,
        "resource_metric_prime_interval_seconds": 5.0,
        "generate_only": False,
    }
    values.update(overrides)
    return Namespace(**values)


def write_resource_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "namespace",
        "pod_name",
        "container_name",
        "container_role",
        "cpu_usage",
        "memory_usage",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def test_ablation_configs_validate_and_execution_plan_rotates(tmp_path: Path):
    runner = RQ21AblationRunner(default_ablation_args(tmp_path, order="fixed", ablation_passes=5))

    runner.validate_configs()

    assert runner.condition_names == {
        "c0": "chain_2svc_plain_nonmesh",
        "c1": "chain_2svc_mesh_default_no_authz",
        "c2": "chain_2svc_mesh_strict_mtls_no_authz",
        "c3": "chain_2svc_mesh_strict_mtls_authz",
    }
    assert runner.service_counts == {"c0": 2, "c1": 2, "c2": 2, "c3": 2}
    assert runner.execution_plan["passes"] == [
        {"pass": 1, "order": ["c0", "c1", "c2", "c3"]},
        {"pass": 2, "order": ["c1", "c2", "c3", "c0"]},
        {"pass": 3, "order": ["c2", "c3", "c0", "c1"]},
        {"pass": 4, "order": ["c3", "c0", "c1", "c2"]},
        {"pass": 5, "order": ["c0", "c1", "c2", "c3"]},
    ]
    assert runner.condition_mesh_enabled("c0") is False
    assert runner.condition_mesh_enabled("c1") is True
    assert runner.expected_policy_shape("c3") == {
        "mesh": True,
        "service_accounts": 2,
        "peer": 2,
        "strict": 1,
        "authz": 1,
    }


def test_ablation_generate_only_writes_static_validation_for_all_conditions(tmp_path: Path):
    runner = RQ21AblationRunner(
        default_ablation_args(
            tmp_path,
            generate_only=True,
            smoke=True,
            order="fixed",
        )
    )

    runner.run()

    expected_shapes = {
        "chain_2svc_plain_nonmesh": {"mesh": False, "service_accounts": 0, "peer": 0, "strict": 0, "authz": 0},
        "chain_2svc_mesh_default_no_authz": {"mesh": True, "service_accounts": 2, "peer": 0, "strict": 0, "authz": 0},
        "chain_2svc_mesh_strict_mtls_no_authz": {"mesh": True, "service_accounts": 2, "peer": 2, "strict": 1, "authz": 0},
        "chain_2svc_mesh_strict_mtls_authz": {"mesh": True, "service_accounts": 2, "peer": 2, "strict": 1, "authz": 1},
    }
    for condition_name, expected_shape in expected_shapes.items():
        payload = json.loads((runner.static_dir / f"{condition_name}.json").read_text(encoding="utf-8"))
        assert payload["passed"] is True
        assert payload["expected_shape"] == expected_shape
        assert payload["errors"] == []

    c1_docs = paired.load_manifest_documents(
        runner.condition_context("c1", 0, 0).manifest_dir
    )
    c3_docs = paired.load_manifest_documents(
        runner.condition_context("c3", 0, 0).manifest_dir
    )
    assert [doc for doc in c1_docs if doc.get("kind") == "PeerAuthentication"] == []
    assert [doc for doc in c1_docs if doc.get("kind") == "AuthorizationPolicy"] == []

    c3_authz = [doc for doc in c3_docs if doc.get("kind") == "AuthorizationPolicy"]
    assert len(c3_authz) == 1
    runner_context = runner.condition_context("c3", 0, 0)
    _, authz_summary = runner.validate_mtls_authorization_policies(runner_context, c3_authz)
    assert authz_summary["allows_only_service1_principal"] is True
    assert authz_summary["policies"][0]["expected_allowed_principal"] == (
        "cluster.local/ns/rq21-ab-c3-authz/sa/rq21-ab-c3-svc1"
    )


def test_ablation_resource_summary_treats_c1_as_mesh_condition(tmp_path: Path):
    c0_path = tmp_path / "c0.csv"
    c1_path = tmp_path / "c1.csv"
    write_resource_csv(
        c0_path,
        [
            {"timestamp": "t1", "namespace": "c0-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
            {"timestamp": "t1", "namespace": "c0-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )
    write_resource_csv(
        c1_path,
        [
            {"timestamp": "t1", "namespace": "c1-svc", "container_name": "inference", "cpu_usage": "120m", "memory_usage": "220Mi"},
            {"timestamp": "t1", "namespace": "c1-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
            {"timestamp": "t1", "namespace": "c1-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )

    runner = RQ21AblationRunner.__new__(RQ21AblationRunner)
    runner.completed_conditions = [
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "c0",
            "resource_samples": str(c0_path),
            "service_namespace": "c0-svc",
            "client_namespace": "c0-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "c1",
            "resource_samples": str(c1_path),
            "service_namespace": "c1-svc",
            "client_namespace": "c1-client",
        },
    ]

    c0 = runner._resource_summary_for_key("c0")
    c1 = runner._resource_summary_for_key("c1")

    assert c0["available"] is True
    assert c0["sidecar_metrics_available"] is False
    assert c1["available"] is True
    assert c1["sidecar_metrics_available"] is True
    assert c1["sidecar_cpu_mcores_mean"] == pytest.approx(25.0)
