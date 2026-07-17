import csv
import json
from argparse import Namespace
from pathlib import Path

import pytest

import scripts.run_rq21_paired_benchmark as paired
from scripts.run_rq21_mtls_split import RQ21MtlsSplitRunner


def default_split_args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "l1_plain_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l1_plain.yaml",
        "l1_mtls_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l1_mtls.yaml",
        "l2_plain_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l2_plain.yaml",
        "l2_mtls_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l2_mtls.yaml",
        "l3_plain_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l3_plain.yaml",
        "l3_mtls_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l3_mtls.yaml",
        "l4_plain_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l4_plain.yaml",
        "l4_mtls_config": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l4_mtls.yaml",
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
        "split_passes": 1,
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


def test_mtls_split_configs_validate_and_execution_plan_rotates(tmp_path: Path):
    runner = RQ21MtlsSplitRunner(default_split_args(tmp_path, order="fixed", split_passes=2))

    runner.validate_configs()

    assert runner.service_counts == {
        "l1_plain": 2,
        "l1_mtls": 2,
        "l2_plain": 2,
        "l2_mtls": 2,
        "l3_plain": 2,
        "l3_mtls": 2,
        "l4_plain": 2,
        "l4_mtls": 2,
    }
    assert runner.condition_names["l1_plain"] == "chain_2svc_split_l1_plain"
    assert runner.condition_names["l4_mtls"] == "chain_2svc_split_l4_mtls"
    assert runner.execution_plan["passes"] == [
        {
            "pass": 1,
            "split_order": ["l1", "l2", "l3", "l4"],
            "security_order": ["plain", "mtls"],
            "order": [
                "l1_plain",
                "l1_mtls",
                "l2_plain",
                "l2_mtls",
                "l3_plain",
                "l3_mtls",
                "l4_plain",
                "l4_mtls",
            ],
        },
        {
            "pass": 2,
            "split_order": ["l2", "l3", "l4", "l1"],
            "security_order": ["mtls", "plain"],
            "order": [
                "l2_mtls",
                "l2_plain",
                "l3_mtls",
                "l3_plain",
                "l4_mtls",
                "l4_plain",
                "l1_mtls",
                "l1_plain",
            ],
        },
    ]
    assert runner.expected_policy_shape("l1_plain") == {
        "mesh": False,
        "service_accounts": 0,
        "peer": 0,
        "strict": 0,
        "authz": 0,
    }
    assert runner.expected_policy_shape("l1_mtls") == {
        "mesh": True,
        "service_accounts": 2,
        "peer": 2,
        "strict": 1,
        "authz": 1,
    }


def test_mtls_split_generate_only_writes_static_validation_for_all_conditions(tmp_path: Path):
    runner = RQ21MtlsSplitRunner(
        default_split_args(
            tmp_path,
            generate_only=True,
            smoke=True,
            order="fixed",
        )
    )

    runner.run()

    for split_key in ("l1", "l2", "l3", "l4"):
        plain_name = f"chain_2svc_split_{split_key}_plain"
        mtls_name = f"chain_2svc_split_{split_key}_mtls"
        plain_payload = json.loads((runner.static_dir / f"{plain_name}.json").read_text(encoding="utf-8"))
        mtls_payload = json.loads((runner.static_dir / f"{mtls_name}.json").read_text(encoding="utf-8"))

        assert plain_payload["passed"] is True
        assert plain_payload["expected_shape"] == {
            "mesh": False,
            "service_accounts": 0,
            "peer": 0,
            "strict": 0,
            "authz": 0,
        }
        assert mtls_payload["passed"] is True
        assert mtls_payload["expected_shape"] == {
            "mesh": True,
            "service_accounts": 2,
            "peer": 2,
            "strict": 1,
            "authz": 1,
        }

    l3_docs = paired.load_manifest_documents(runner.condition_context("l3_mtls", 0, 0).manifest_dir)
    authz = [doc for doc in l3_docs if doc.get("kind") == "AuthorizationPolicy"]
    assert len(authz) == 1
    _, summary = runner.validate_mtls_authorization_policies(
        runner.condition_context("l3_mtls", 0, 0),
        authz,
    )
    assert summary["allows_only_service1_principal"] is True
    assert summary["policies"][0]["expected_allowed_principal"] == (
        "cluster.local/ns/rq21-ms-l3-mtls/sa/rq21-ms-l3-svc1"
    )


def test_mtls_split_latency_summary_reports_per_split_deltas():
    runner = RQ21MtlsSplitRunner.__new__(RQ21MtlsSplitRunner)
    runner.condition_keys = RQ21MtlsSplitRunner.condition_keys
    runner.split_keys = RQ21MtlsSplitRunner.split_keys
    runner.condition_names = {
        key: f"chain_2svc_split_{key}"
        for key in runner.condition_keys
    }
    rows = []
    values = {
        "l1_plain": (100.0, 802816),
        "l1_mtls": (106.0, 802816),
        "l2_plain": (90.0, 401408),
        "l2_mtls": (94.0, 401408),
        "l3_plain": (80.0, 200704),
        "l3_mtls": (83.0, 200704),
        "l4_plain": (70.0, 100352),
        "l4_mtls": (72.0, 100352),
    }
    for key, (latency, protected_bytes) in values.items():
        rows.append(
            {
                "condition_key": key,
                "condition": f"chain_2svc_split_{key}",
                "end_to_end_ms": str(latency),
                "non_compute_overhead_ms": "10",
                "total_compute_ms": "60",
                "total_activation_bytes": str(602112 + protected_bytes),
                "hop_1_activation_bytes": "602112",
                "hop_2_activation_bytes": str(protected_bytes),
                "hop_1_forward_ms": "1",
                "hop_2_forward_ms": "2",
            }
        )

    summary = runner.summarize_latency(rows)

    assert summary["by_split"]["l1"]["mean_latency_overhead_ms"] == pytest.approx(6.0)
    assert summary["by_split"]["l2"]["mean_latency_overhead_ms"] == pytest.approx(4.0)
    assert summary["by_split"]["l3"]["mean_latency_overhead_ms"] == pytest.approx(3.0)
    assert summary["by_split"]["l4"]["mean_latency_overhead_ms"] == pytest.approx(2.0)
    assert summary["by_split"]["l2"]["expected_protected_activation_bytes"] == 401408
    assert summary["by_condition"]["l2_plain"]["protected_hop_activation_bytes_mean"] == 401408.0
    assert summary["by_condition"]["l2_plain"]["total_activation_bytes_mean"] == 1003520.0


def test_mtls_split_resource_summary_requires_sidecars_only_for_mtls(tmp_path: Path):
    plain_path = tmp_path / "plain.csv"
    mtls_path = tmp_path / "mtls.csv"
    write_resource_csv(
        plain_path,
        [
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
            {"timestamp": "t1", "namespace": "plain-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )
    write_resource_csv(
        mtls_path,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "120m", "memory_usage": "220Mi"},
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
            {"timestamp": "t1", "namespace": "mtls-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )

    runner = RQ21MtlsSplitRunner.__new__(RQ21MtlsSplitRunner)
    runner.completed_conditions = [
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "l1_plain",
            "resource_samples": str(plain_path),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "l1_mtls",
            "resource_samples": str(mtls_path),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
        },
    ]

    plain = runner._resource_summary_for_key("l1_plain")
    mtls = runner._resource_summary_for_key("l1_mtls")

    assert plain["available"] is True
    assert plain["sidecar_metrics_available"] is False
    assert mtls["available"] is True
    assert mtls["sidecar_metrics_available"] is True
    assert mtls["sidecar_cpu_mcores_mean"] == pytest.approx(25.0)


def test_mtls_split_security_preflight_accepts_non_layer2_split(tmp_path: Path):
    runner = RQ21MtlsSplitRunner.__new__(RQ21MtlsSplitRunner)
    runner.expected_mtls_authorization_policies = lambda _context: [
        {"expected_principal": "cluster.local/ns/mtls-svc/sa/rq21-ms-l3-svc1"}
    ]
    runner.run_full_chain_probe = lambda _context: {
        "succeeded": True,
        "hop_count": 2,
        "hop_indexes": [1, 2],
    }
    runner.run_direct_probe = lambda _context, *, expected_blocked: {
        "passed": expected_blocked,
        "blocked": True,
        "ready": False,
        "target": "service2:50051",
        "returncode": 42,
    }
    context = paired.ConditionContext(
        key="l3_mtls",
        condition_name="chain_2svc_split_l3_mtls",
        source_config_path=tmp_path / "source.yaml",
        effective_config_path=tmp_path / "effective.yaml",
        service_namespace="mtls-svc",
        client_namespace="mtls-client",
        service_count=2,
        condition_dir=tmp_path / "condition",
        manifest_dir=tmp_path / "condition" / "manifests",
        benchmark_dir=tmp_path / "condition" / "benchmark",
        diagnostics_dir=tmp_path / "condition" / "diagnostics",
        resource_samples_path=tmp_path / "condition" / "resource_samples.csv",
    )

    artifact_dir = runner.run_mtls_security_preflight(context)
    metadata = json.loads((artifact_dir / "rq21_preflight_metadata.json").read_text(encoding="utf-8"))

    assert metadata["preflight_passed"] is True
    assert metadata["split_aware_preflight"] is True
    assert metadata["split_key"] == "l3"
    assert metadata["enforcement_validation"]["non_mesh_direct_denial_probe"]["blocked_as_expected"] is True
