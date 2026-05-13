import csv
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

import scripts.run_rq21_paired_benchmark as paired
from scripts.run_rq21_paired_benchmark import ConditionContext, PipelineError, RQ21PairedBenchmarkRunner


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


def build_cpu_counter_metrics(
    *,
    service_app_cpu_mcores: float,
    sidecar_cpu_mcores: float = 0.0,
    client_cpu_mcores: float = 0.0,
    available: bool = True,
    errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "available": available,
        "duration_seconds": 10.0,
        "summary": {
            "service_app_cpu_mcores": service_app_cpu_mcores,
            "sidecar_cpu_mcores": sidecar_cpu_mcores,
            "total_pod_cpu_mcores": service_app_cpu_mcores + sidecar_cpu_mcores,
            "client_cpu_mcores": client_cpu_mcores,
        },
        "errors": errors or [],
    }


def build_runner(records: list[dict[str, object]]) -> RQ21PairedBenchmarkRunner:
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    runner.completed_conditions = records
    runner.condition_names = {
        "plain": "chain_2svc_plain",
        "mtls": "chain_2svc_mtls",
    }
    runner.service_counts = {
        "plain": 2,
        "mtls": 2,
    }
    return runner


def build_condition_context(tmp_path: Path, key: str = "plain", service_count: int = 2) -> ConditionContext:
    condition_name = f"chain_{service_count}svc_{key}"
    return ConditionContext(
        key=key,
        condition_name=condition_name,
        source_config_path=tmp_path / "source.yaml",
        effective_config_path=tmp_path / "effective.yaml",
        service_namespace=f"{key}-svc",
        client_namespace=f"{key}-client",
        service_count=service_count,
        condition_dir=tmp_path / "condition",
        manifest_dir=tmp_path / "condition" / "manifests",
        benchmark_dir=tmp_path / "condition" / "benchmark",
        diagnostics_dir=tmp_path / "condition" / "diagnostics",
        resource_samples_path=tmp_path / "condition" / "resource_samples.csv",
    )


def make_container(name: str, cpu: str | None = None, memory: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"name": name}
    if cpu or memory:
        payload["resources"] = {
            "requests": {
                "cpu": cpu or "",
                "memory": memory or "",
            }
        }
    return payload


def make_pod(
    name: str,
    containers: list[str],
    init_containers: list[str] | None = None,
    node_name: str | None = None,
) -> dict[str, object]:
    return {
        "metadata": {"name": name},
        "spec": {
            "nodeName": node_name or "node-a",
            "containers": [{"name": container} for container in containers],
            "initContainers": [{"name": container} for container in (init_containers or [])],
        },
    }


def build_metric_gate_runner(tmp_path: Path) -> tuple[RQ21PairedBenchmarkRunner, ConditionContext]:
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    runner.args = Namespace(
        disable_resource_sampling=False,
        resource_metric_prime_timeout_seconds=1.0,
        resource_metric_prime_interval_seconds=0.01,
    )
    context = build_condition_context(tmp_path)
    runner.service_pods = lambda _context: [
        make_pod("service-1", ["inference"]),
        make_pod("service-2", ["inference"]),
    ]
    runner.client_pod = lambda _context: make_pod("benchmark-client", ["client"])
    return runner, context


def default_runner_args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "plain_config": "configs/rq2/2.1/rq2_1_chain2_plain.yaml",
        "mtls_config": "configs/rq2/2.1/rq2_1_chain2_mtls.yaml",
        "topology": "auto",
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
        "mesh_revision": "asm-1-29",
        "readiness_timeout": None,
        "smoke": False,
        "paired_passes": 1,
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


def test_default_chain2_configs_still_validate(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner(default_runner_args(tmp_path))

    runner.validate_configs()

    assert runner.selected_topology() == "chain2"
    assert runner.service_counts == {"plain": 2, "mtls": 2}


def test_chain5_configs_validate_as_optional_stress_topology(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner(
        default_runner_args(
            tmp_path,
            plain_config="configs/rq2/2.1/rq2_1_chain5_plain.yaml",
            mtls_config="configs/rq2/2.1/rq2_1_chain5_mtls.yaml",
            topology="chain5",
        )
    )

    runner.validate_configs()

    assert runner.selected_topology() == "chain5"
    assert runner.service_counts == {"plain": 5, "mtls": 5}
    assert runner.raw_configs["plain"]["kubernetes"]["client_resources"] == runner.raw_configs["mtls"]["kubernetes"]["client_resources"]
    assert runner.raw_configs["plain"]["kubernetes"]["client_resources"]["cpu_request"] == "100m"
    assert runner.raw_configs["plain"]["kubernetes"]["client_resources"]["cpu_limit"] == "1"


def test_rq21b_multinode_configs_validate_as_chain2_sensitivity(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner(
        default_runner_args(
            tmp_path,
            plain_config="configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml",
            mtls_config="configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml",
            topology="chain2",
            nodepool="rq21bpool",
            node_count=3,
        )
    )

    runner.validate_configs()

    assert runner.is_multinode is True
    assert runner.experiment_signature == "rq2_1b_multinode"
    assert runner.artifact_dir.name.startswith("rq2_1b_multinode_")
    assert runner.condition_names == {
        "plain": "chain_2svc_plain_multinode",
        "mtls": "chain_2svc_mtls_multinode",
    }


def test_rq21b_multinode_configs_reject_single_benchmark_node(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner(
        default_runner_args(
            tmp_path,
            plain_config="configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml",
            mtls_config="configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml",
            topology="chain2",
            nodepool="rq21bpool",
            node_count=1,
        )
    )

    with pytest.raises(PipelineError, match="--node-count 3"):
        runner.validate_configs()


def test_rq21b_runtime_placement_validation_requires_distinct_nodes(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    context = build_condition_context(tmp_path, key="plain", service_count=2)
    context.effective_config_path.write_text(
        """
kubernetes:
  placement:
    strategy: multi_node_anti_affinity
    require_dedicated_client_node: true
    min_nodes: 3
""".lstrip(),
        encoding="utf-8",
    )

    errors, summary = runner.runtime_placement_validation(
        context,
        [
            make_pod("service-1", ["inference"], node_name="node-a"),
            make_pod("service-2", ["inference"], node_name="node-b"),
        ],
        make_pod("benchmark-client", ["client"], node_name="node-c"),
    )

    assert errors == []
    assert summary["strategy"] == "multi_node_anti_affinity"
    assert summary["service_pod_nodes"] == ["node-a", "node-b"]
    assert summary["client_node"] == "node-c"
    assert summary["dedicated_client_node"] is True

    errors, summary = runner.runtime_placement_validation(
        context,
        [
            make_pod("service-1", ["inference"], node_name="node-a"),
            make_pod("service-2", ["inference"], node_name="node-a"),
        ],
        make_pod("benchmark-client", ["client"], node_name="node-a"),
    )

    assert any("not on distinct nodes" in error for error in errors)
    assert any("not on a dedicated node" in error for error in errors)
    assert summary["dedicated_client_node"] is False


def test_wait_for_resource_metrics_ready_accepts_expected_service_and_client_containers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner, context = build_metric_gate_runner(tmp_path)

    def fake_run_command(args, **_kwargs):
        namespace = args[-1]
        stdout = {
            "plain-svc": "\n".join(
                [
                    "service-1 inference 100m 200Mi",
                    "service-2 inference 110m 210Mi",
                ]
            ),
            "plain-client": "benchmark-client client 10m 20Mi",
        }[namespace]
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(paired, "run_command", fake_run_command)

    status = runner.wait_for_resource_metrics_ready(context)

    assert status is not None
    assert status["ready"] is True
    assert status["missing"] == {}
    assert (context.condition_dir / "resource_metric_prime_status.json").exists()


def test_wait_for_resource_metrics_ready_fails_before_benchmark_when_condition_metrics_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner, context = build_metric_gate_runner(tmp_path)
    runner.args.resource_metric_prime_timeout_seconds = 0.01

    def fake_run_command(args, **_kwargs):
        namespace = args[-1]
        stdout = "benchmark-client client 10m 20Mi" if namespace == "plain-client" else ""
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(paired, "run_command", fake_run_command)

    with pytest.raises(PipelineError, match="Timed out waiting for resource metrics"):
        runner.wait_for_resource_metrics_ready(context)

    status = (context.condition_dir / "resource_metric_prime_status.json").read_text(encoding="utf-8")
    assert "plain-svc" in status
    assert "service-1" in status
    assert "service-2" in status


def test_write_file_into_pod_retries_transient_kubelet_exec_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    runner.args = Namespace(client_pod="benchmark-client")
    context = build_condition_context(tmp_path)
    calls: list[list[str]] = []
    sleeps: list[int] = []
    exec_attempts = 0

    def fake_run_command(args, **_kwargs):
        nonlocal exec_attempts
        calls.append(args)
        if args[:2] == ["kubectl", "exec"]:
            exec_attempts += 1
            if exec_attempts == 1:
                raise PipelineError(
                    'Command failed: kubectl exec -n plain-client benchmark-client -- python -c ...\n'
                    'proxy error from localhost:9443 while dialing 10.224.0.5:10250'
                )
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(paired, "run_command", fake_run_command)
    monkeypatch.setattr(paired.time, "sleep", lambda seconds: sleeps.append(seconds))

    runner.write_file_into_pod(context, "/tmp/config.yaml", "x: 1\n")

    assert exec_attempts == 2
    assert sleeps == [5]
    assert any(call[:3] == ["kubectl", "wait", "--for=condition=Ready"] for call in calls)


def test_expected_resource_metric_containers_includes_native_istio_sidecar_for_mtls(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    context = build_condition_context(tmp_path, key="mtls")
    runner.service_pods = lambda _context: [
        make_pod("service-1", ["inference"], ["istio-proxy"]),
        make_pod("service-2", ["inference"], ["istio-proxy"]),
    ]
    runner.client_pod = lambda _context: make_pod("benchmark-client", ["client"])

    expected = runner.expected_resource_metric_containers(context)

    assert expected["mtls-svc"]["service-1"] == ["inference", "istio-proxy"]
    assert expected["mtls-svc"]["service-2"] == ["inference", "istio-proxy"]
    assert expected["mtls-client"]["benchmark-client"] == ["client"]


def test_chain5_resource_metric_expectations_include_all_mtls_sidecars(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    context = build_condition_context(tmp_path, key="mtls", service_count=5)
    runner.service_pods = lambda _context: [
        make_pod(f"service-{index}", ["inference"], ["istio-proxy"])
        for index in range(1, 6)
    ]
    runner.client_pod = lambda _context: make_pod("benchmark-client", ["client"])

    expected = runner.expected_resource_metric_containers(context)

    assert set(expected["mtls-svc"]) == {f"service-{index}" for index in range(1, 6)}
    for index in range(1, 6):
        assert expected["mtls-svc"][f"service-{index}"] == ["inference", "istio-proxy"]


def test_pod_request_totals_counts_native_init_sidecar_requests():
    pod = {
        "metadata": {"name": "service-1"},
        "spec": {
            "containers": [make_container("inference", "1", "1Gi")],
            "initContainers": [make_container("istio-proxy", "100m", "128Mi")],
        },
    }

    totals = paired.pod_request_totals(pod)

    assert totals["app_cpu_mcores_total"] == 1000.0
    assert totals["sidecar_cpu_mcores_total"] == 100.0
    assert totals["pod_cpu_mcores_total"] == 1100.0
    assert totals["app_memory_mib_total"] == 1024.0
    assert totals["sidecar_memory_mib_total"] == 128.0
    assert totals["pod_memory_mib_total"] == 1152.0


def test_mtls_authorization_policy_validation_requires_only_service1_principal(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    config_path = tmp_path / "mtls.yaml"
    config_path.write_text(
        """
kubernetes:
    mesh:
      service_accounts:
        "1": rq21-chain2-svc1
      authorization_policy:
        enabled: true
        name: downstream-service1-only
        source_segment_index: "1"
        downstream_segment_index: "2"
""".lstrip(),
        encoding="utf-8",
    )
    runner.source_paths = {"mtls": config_path}
    runner.effective_config_paths = {"mtls": config_path}
    context = build_condition_context(tmp_path, key="mtls")
    policy = {
        "metadata": {"name": "downstream-service1-only"},
        "spec": {
            "selector": {
                "matchLabels": {
                    "condition": "chain_2svc_mtls",
                    "segment-index": "2",
                    "workload-role": "service",
                }
            },
            "action": "ALLOW",
            "rules": [
                {
                    "from": [
                        {
                            "source": {
                                "principals": [
                                    "cluster.local/ns/mtls-svc/sa/rq21-chain2-svc1",
                                    "cluster.local/ns/mtls-svc/sa/unexpected",
                                ]
                            }
                        }
                    ]
                }
            ],
        },
    }

    errors, summary = runner.validate_mtls_authorization_policy(context, [policy])

    assert errors
    assert summary["selects_downstream_service2"] is True
    assert summary["allows_only_service1_principal"] is False


def test_chain5_mtls_manifest_generation_emits_per_hop_identity_policies(tmp_path: Path):
    output_dir = tmp_path / "manifests"
    completed = subprocess.run(
        [
            sys.executable,
            "k8s/aks/generate_aks_manifests.py",
            "--config",
            "configs/rq2/2.1/rq2_1_chain5_mtls.yaml",
            "--output-dir",
            str(output_dir),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    docs = paired.load_manifest_documents(output_dir)
    service_accounts = [doc for doc in docs if doc.get("kind") == "ServiceAccount"]
    peer_auths = [doc for doc in docs if doc.get("kind") == "PeerAuthentication"]
    authz = [doc for doc in docs if doc.get("kind") == "AuthorizationPolicy"]
    workload_specs = []
    for doc in docs:
        if doc.get("kind") == "Deployment":
            workload_specs.append(((doc.get("spec") or {}).get("template") or {}).get("spec") or {})
        if doc.get("kind") == "Pod":
            workload_specs.append(doc.get("spec") or {})

    assert {
        (doc.get("metadata") or {}).get("name")
        for doc in service_accounts
    } == {
        "rq21-chain5-svc1",
        "rq21-chain5-svc2",
        "rq21-chain5-svc3",
        "rq21-chain5-svc4",
        "rq21-chain5-svc5",
    }
    assert workload_specs
    for spec in workload_specs:
        assert (spec.get("nodeSelector") or {}) == {
            "agentpool": "rq15pool",
            "workload": "benchmark",
        }
        assert any(
            paired.toleration_matches_taint(item, "workload=benchmark:NoSchedule")
            for item in (spec.get("tolerations") or [])
        )
    strict_segments = {
        ((doc.get("spec") or {}).get("selector") or {}).get("matchLabels", {}).get("segment-index")
        for doc in peer_auths
        if ((doc.get("spec") or {}).get("mtls") or {}).get("mode") == "STRICT"
    }
    assert strict_segments == {"2", "3", "4", "5"}

    by_segment = {
        ((doc.get("spec") or {}).get("selector") or {}).get("matchLabels", {}).get("segment-index"): doc
        for doc in authz
    }
    assert set(by_segment) == {"2", "3", "4", "5"}
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    chain5_config = Path(__file__).resolve().parents[1] / "configs/rq2/2.1/rq2_1_chain5_mtls.yaml"
    runner.source_paths = {"mtls": chain5_config}
    runner.effective_config_paths = {"mtls": chain5_config}
    context = build_condition_context(tmp_path, key="mtls", service_count=5)
    context.service_namespace = "rq21-chain5-mtls"
    authz_errors, authz_summary = runner.validate_mtls_authorization_policies(context, authz)
    peer_errors, peer_summary = runner.validate_mtls_peer_authentications(context, peer_auths)
    assert authz_errors == []
    assert authz_summary["expected_policy_count"] == 4
    assert peer_errors == []
    assert peer_summary["observed_strict_segments"] == ["2", "3", "4", "5"]
    for downstream in range(2, 6):
        policy = by_segment[str(downstream)]
        principals = paired.RQ21PairedBenchmarkRunner.__new__(
            paired.RQ21PairedBenchmarkRunner
        ).authorization_policy_principals(policy)
        assert principals == [
            f"cluster.local/ns/rq21-chain5-mtls/sa/rq21-chain5-svc{downstream - 1}"
        ]


def test_rq21b_multinode_manifest_generation_emits_anti_affinity(tmp_path: Path):
    output_dir = tmp_path / "manifests"
    completed = subprocess.run(
        [
            sys.executable,
            "k8s/aks/generate_aks_manifests.py",
            "--config",
            "configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml",
            "--nodepool",
            "rq21bpool",
            "--output-dir",
            str(output_dir),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    docs = paired.load_manifest_documents(output_dir)
    workload_specs = []
    for doc in docs:
        if doc.get("kind") == "Deployment":
            workload_specs.append(((doc.get("spec") or {}).get("template") or {}).get("spec") or {})
        if doc.get("kind") == "Pod":
            workload_specs.append(doc.get("spec") or {})

    assert workload_specs
    for spec in workload_specs:
        assert (spec.get("nodeSelector") or {}) == {
            "agentpool": "rq21bpool",
            "workload": "benchmark",
        }
        required_terms = (
            ((spec.get("affinity") or {}).get("podAntiAffinity") or {})
            .get("requiredDuringSchedulingIgnoredDuringExecution")
            or []
        )
        assert required_terms
        assert any(
            paired.toleration_matches_taint(item, "workload=benchmark:NoSchedule")
            for item in (spec.get("tolerations") or [])
        )


def test_parse_rejects_infrastructure_destroy_without_provision(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_rq21_paired_benchmark.py", "--destroy-infrastructure-on-success"],
    )

    with pytest.raises(SystemExit):
        paired.parse_args()


def test_operational_capture_rejects_avoidable_istio_colocation_for_isolated_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    context = build_condition_context(tmp_path, key="mtls")
    context.diagnostics_dir.mkdir(parents=True)
    context.manifest_dir.mkdir(parents=True)
    context.effective_config_path.write_text(
        """
kubernetes:
  placement:
    require_control_plane_isolation: true
""".lstrip(),
        encoding="utf-8",
    )

    service_pod = {
        "metadata": {
            "name": "service-1",
            "labels": {"condition": context.condition_name, "workload-role": "service"},
        },
        "spec": {
            "nodeName": "benchmark-node",
            "containers": [make_container("inference", "1", "1Gi")],
        },
        "status": {"phase": "Running", "conditions": []},
    }
    client_pod = {
        "metadata": {"name": "benchmark-client"},
        "spec": {
            "nodeName": "benchmark-node",
            "containers": [make_container("client", "100m", "1Gi")],
        },
        "status": {"phase": "Running", "conditions": []},
    }

    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    runner.args = Namespace(isolated_node_pools=True, benchmark_taint="workload=benchmark:NoSchedule")
    runner.mesh_revision = "asm-1-29"
    runner.service_pods = lambda _context: [service_pod]
    runner.client_pod = lambda _context: client_pod
    runner.namespace_pod_events = lambda _namespace: {}
    runner.node_allocatable = lambda _node_name: {"cpu_mcores": 8000.0, "memory_mib": 32768.0}
    monkeypatch.setattr(
        paired,
        "mesh_control_plane_pods",
        lambda: [
            {
                "namespace": "aks-istio-system",
                "pod_name": "istiod-asm-1-29-abc",
                "node_name": "benchmark-node",
                "phase": "Running",
                "labels": {"app": "istiod"},
                "owner_references": [{"kind": "ReplicaSet", "name": "istiod-asm-1-29"}],
            }
        ],
    )

    with pytest.raises(PipelineError, match="Isolated-pool RQ2.1 contract violated"):
        runner.capture_operational_overhead(context)

    payload = json.loads((context.diagnostics_dir / "operational_overhead.json").read_text(encoding="utf-8"))
    assert payload["control_plane_colocation"]["violates_isolated_pool_contract"] is True


def test_prepare_infrastructure_can_provision_push_enable_mesh_and_destroy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []

    class FakeLifecycleRunner:
        def __init__(self, args):
            self.args = args
            self.acr_name = args.acr_name
            self.mesh = {"revision": args.mesh_revision}
            self.state = Namespace(artifact_dir=Path(args.results_root) / "fake_preflight")

        def prepare_artifact_dirs(self):
            self.state.artifact_dir.mkdir(parents=True, exist_ok=True)

        def maybe_provision_cluster(self):
            calls.append("provision")
            self.args.resource_group = "rg-from-terraform"
            self.args.cluster_name = "cluster-from-terraform"
            self.args.node_vm_size = "Standard_D8s_v3"
            self.acr_name = "testacr"

        def resolve_image_reference(self):
            calls.append("resolve_image")
            payload = {
                "reason": "configured digest missing from provisioned ACR",
                "pinned_ref": "testacr.azurecr.io/thesis-inference@sha256:abcdef",
            }
            (self.state.artifact_dir / "image_resolution.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            return "testacr.azurecr.io/thesis-inference@sha256:abcdef"

        def prepare_effective_config(self, *, resolve_live_revision, image_ref):
            calls.append("prepare_effective_config")
            assert resolve_live_revision is True
            assert image_ref == "testacr.azurecr.io/thesis-inference@sha256:abcdef"
            self.mesh["revision"] = "asm-1-29"

        def ensure_managed_istio(self):
            calls.append("ensure_mesh")

        def _terraform_init(self):
            calls.append("terraform_init")

        def _terraform_var_args(self):
            return [
                "-var=resource_group_name=rg-from-terraform",
                "-var=acr_name=testacr",
            ]

    destroy_commands: list[list[str]] = []

    def fake_run_command(args, **_kwargs):
        destroy_commands.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(paired, "RQ21PreflightRunner", FakeLifecycleRunner)
    monkeypatch.setattr(paired, "run_command", fake_run_command)

    args = default_runner_args(
        tmp_path,
        provision=True,
        destroy_infrastructure_on_success=True,
    )
    runner = RQ21PairedBenchmarkRunner(args)
    runner.prepare_artifact_dirs()
    runner.prepare_infrastructure()
    runner.destroy_infrastructure("test")

    assert calls[:4] == ["provision", "resolve_image", "prepare_effective_config", "ensure_mesh"]
    assert calls[-1] == "terraform_init"
    assert runner.infrastructure_provisioned is True
    assert runner.infrastructure_destroyed is True
    assert runner.effective_image_ref == "testacr.azurecr.io/thesis-inference@sha256:abcdef"
    assert runner.args.resource_group == "rg-from-terraform"
    assert destroy_commands[0][:4] == ["terraform", "destroy", "-auto-approve", "-input=false"]
    assert (runner.artifact_dir / "image_reference.txt").read_text(encoding="utf-8").strip() == runner.effective_image_ref


def test_summarize_resource_samples_aggregates_passes_and_total_pod_metrics(tmp_path: Path):
    plain_pass1 = tmp_path / "plain-pass1.csv"
    plain_pass2 = tmp_path / "plain-pass2.csv"
    mtls_pass1 = tmp_path / "mtls-pass1.csv"
    write_resource_csv(
        plain_pass1,
        [
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
            {"timestamp": "t1", "namespace": "plain-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )
    write_resource_csv(
        plain_pass2,
        [
            {"timestamp": "t2", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "300m", "memory_usage": "400Mi"},
            {"timestamp": "t2", "namespace": "plain-client", "container_name": "client", "cpu_usage": "30m", "memory_usage": "40Mi"},
        ],
    )
    write_resource_csv(
        mtls_pass1,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "150m", "memory_usage": "250Mi"},
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
            {"timestamp": "t1", "namespace": "mtls-client", "container_name": "client", "cpu_usage": "12m", "memory_usage": "22Mi"},
        ],
    )

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass1),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
            "cpu_counter_metrics": build_cpu_counter_metrics(
                service_app_cpu_mcores=180.0,
                client_cpu_mcores=10.0,
            ),
        },
        {
            "pass": 2,
            "execution_index": 2,
            "condition_key": "plain",
            "resource_samples": str(plain_pass2),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
            "cpu_counter_metrics": build_cpu_counter_metrics(
                service_app_cpu_mcores=220.0,
                client_cpu_mcores=30.0,
            ),
        },
        {
            "pass": 1,
            "execution_index": 3,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass1),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
            "cpu_counter_metrics": build_cpu_counter_metrics(
                service_app_cpu_mcores=190.0,
                sidecar_cpu_mcores=25.0,
                client_cpu_mcores=12.0,
            ),
        },
    ])

    summary = runner.summarize_resource_samples()

    plain = summary["by_condition"]["plain"]
    mtls = summary["by_condition"]["mtls"]
    comparison = summary["comparison"]

    assert plain["available"] is True
    assert plain["sample_count"] == 2
    assert plain["cpu_measurement_count"] == 2
    assert plain["passes_covered"] == [1, 2]
    assert plain["sidecar_sample_row_count"] == 0
    assert plain["sidecar_metrics_available"] is False
    assert plain["service_app_cpu_mcores_mean"] == 200.0
    assert plain["total_pod_cpu_mcores_mean"] == 200.0
    assert plain["service_app_memory_mib_mean"] == 300.0
    assert plain["total_pod_memory_mib_mean"] == 300.0

    assert mtls["available"] is True
    assert mtls["sample_count"] == 1
    assert mtls["cpu_measurement_count"] == 1
    assert mtls["passes_covered"] == [1]
    assert mtls["sidecar_sample_row_count"] == 1
    assert mtls["sidecar_metrics_available"] is True
    assert mtls["service_app_cpu_mcores_mean"] == 190.0
    assert mtls["sidecar_cpu_mcores_mean"] == 25.0
    assert mtls["total_pod_cpu_mcores_mean"] == 215.0
    assert mtls["service_app_memory_mib_mean"] == 250.0
    assert mtls["sidecar_memory_mib_mean"] == 50.0
    assert mtls["total_pod_memory_mib_mean"] == 300.0

    assert comparison["sidecar_cpu_mcores_mean_overhead"] == 25.0
    assert comparison["total_pod_cpu_mcores_mean_overhead"] == 15.0
    assert comparison["total_pod_memory_mib_mean_overhead"] == 0.0


def test_summarize_resource_samples_fails_closed_when_cpu_counter_measurement_is_incomplete(tmp_path: Path):
    plain_pass = tmp_path / "plain.csv"
    mtls_pass = tmp_path / "mtls.csv"
    write_resource_csv(
        plain_pass,
        [
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
        ],
    )
    write_resource_csv(
        mtls_pass,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "150m", "memory_usage": "250Mi"},
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
        ],
    )

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
            "resource_cpu_measurement": str(tmp_path / "plain-cpu.json"),
            "cpu_counter_metrics": build_cpu_counter_metrics(
                service_app_cpu_mcores=100.0,
                available=False,
                errors=[{"reason": "kubelet summary request failed"}],
            ),
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
            "cpu_counter_metrics": build_cpu_counter_metrics(
                service_app_cpu_mcores=190.0,
                sidecar_cpu_mcores=25.0,
            ),
        },
    ])

    summary = runner.summarize_resource_samples()
    plain = summary["by_condition"]["plain"]

    assert plain["available"] is False
    assert plain["failures"][0]["reason"] == "container CPU counter measurement was incomplete"
    assert plain["failures"][0]["cpu_counter_errors"] == [{"reason": "kubelet summary request failed"}]


def test_summarize_cpu_counter_window_converts_container_deltas_to_mcores(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    context = build_condition_context(tmp_path, key="mtls")

    start_snapshot = {
        "captured_at": "2026-01-01T00:00:00+00:00",
        "containers": [
            {
                "namespace": "mtls-svc",
                "pod_name": "service-1",
                "container_name": "inference",
                "role": "service_app",
                "usage_core_nanoseconds": 1_000_000_000,
            },
            {
                "namespace": "mtls-svc",
                "pod_name": "service-1",
                "container_name": "istio-proxy",
                "role": "sidecar",
                "usage_core_nanoseconds": 500_000_000,
            },
            {
                "namespace": "mtls-client",
                "pod_name": "benchmark-client",
                "container_name": "client",
                "role": "client",
                "usage_core_nanoseconds": 200_000_000,
            },
        ],
        "errors": [],
    }
    end_snapshot = {
        "captured_at": "2026-01-01T00:00:10+00:00",
        "containers": [
            {
                "namespace": "mtls-svc",
                "pod_name": "service-1",
                "container_name": "inference",
                "role": "service_app",
                "usage_core_nanoseconds": 3_000_000_000,
            },
            {
                "namespace": "mtls-svc",
                "pod_name": "service-1",
                "container_name": "istio-proxy",
                "role": "sidecar",
                "usage_core_nanoseconds": 750_000_000,
            },
            {
                "namespace": "mtls-client",
                "pod_name": "benchmark-client",
                "container_name": "client",
                "role": "client",
                "usage_core_nanoseconds": 300_000_000,
            },
        ],
        "errors": [],
    }

    measurement = runner.summarize_cpu_counter_window(
        context,
        paired.datetime(2026, 1, 1, tzinfo=paired.timezone.utc),
        paired.datetime(2026, 1, 1, 0, 0, 10, tzinfo=paired.timezone.utc),
        10.0,
        start_snapshot,
        end_snapshot,
    )

    assert measurement["available"] is True
    assert measurement["summary"]["service_app_cpu_mcores"] == 200.0
    assert measurement["summary"]["sidecar_cpu_mcores"] == 25.0
    assert measurement["summary"]["total_pod_cpu_mcores"] == 225.0
    assert measurement["summary"]["client_cpu_mcores"] == 10.0
    assert (tmp_path / "condition" / "resource_cpu_measurement.json").exists()


def test_summarize_resource_samples_fails_closed_on_missing_service_namespace_rows(tmp_path: Path):
    missing_plain = tmp_path / "plain-missing.csv"
    mtls_pass1 = tmp_path / "mtls-pass1.csv"
    write_resource_csv(
        missing_plain,
        [
            {"timestamp": "t1", "namespace": "plain-client", "container_name": "client", "cpu_usage": "10m", "memory_usage": "20Mi"},
        ],
    )
    write_resource_csv(
        mtls_pass1,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "150m", "memory_usage": "250Mi"},
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
        ],
    )

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(missing_plain),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass1),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
        },
    ])

    summary = runner.summarize_resource_samples()
    blockers = runner.resource_summary_blockers(summary)

    plain = summary["by_condition"]["plain"]
    assert plain["available"] is False
    assert plain["reason"] == "one or more required resource sample artifacts were incomplete"
    assert plain["failures"][0]["reason"] == "resource sample CSV had no service-namespace rows for the benchmarked condition"
    assert blockers == [
        "plain: one or more required resource sample artifacts were incomplete",
        "plain pass 1 exec 1: resource sample CSV had no service-namespace rows for the benchmarked condition",
    ]


def test_summarize_resource_samples_fails_mtls_when_sidecar_rows_are_missing(tmp_path: Path):
    plain_pass = tmp_path / "plain.csv"
    mtls_pass = tmp_path / "mtls-no-sidecar.csv"
    write_resource_csv(
        plain_pass,
        [
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
        ],
    )
    write_resource_csv(
        mtls_pass,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "150m", "memory_usage": "250Mi"},
        ],
    )

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
        },
    ])

    summary = runner.summarize_resource_samples()
    mtls = summary["by_condition"]["mtls"]

    assert mtls["available"] is False
    assert mtls["sidecar_sample_row_count"] == 0
    assert mtls["sidecar_metrics_available"] is False
    assert mtls["failures"][0]["reason"] == "mTLS resource sample CSV had zero istio-proxy rows"


def test_summarize_resource_samples_fails_chain5_mtls_when_any_service_sidecar_sample_is_missing(tmp_path: Path):
    plain_pass = tmp_path / "plain.csv"
    mtls_pass = tmp_path / "mtls-missing-one-sidecar.csv"
    write_resource_csv(
        plain_pass,
        [
            {
                "timestamp": "t1",
                "namespace": "plain-svc",
                "pod_name": f"plain-service-{index}",
                "container_name": "inference",
                "cpu_usage": "100m",
                "memory_usage": "200Mi",
            }
            for index in range(1, 6)
        ],
    )
    mtls_rows = []
    for index in range(1, 6):
        mtls_rows.append(
            {
                "timestamp": "t1",
                "namespace": "mtls-svc",
                "pod_name": f"mtls-service-{index}",
                "container_name": "inference",
                "cpu_usage": "150m",
                "memory_usage": "250Mi",
            }
        )
        if index != 5:
            mtls_rows.append(
                {
                    "timestamp": "t1",
                    "namespace": "mtls-svc",
                    "pod_name": f"mtls-service-{index}",
                    "container_name": "istio-proxy",
                    "cpu_usage": "25m",
                    "memory_usage": "50Mi",
                }
            )
    write_resource_csv(mtls_pass, mtls_rows)

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
            "operational_overhead": {
                "service_pods": [
                    {"pod_name": f"mtls-service-{index}", "sidecar_present": True}
                    for index in range(1, 6)
                ]
            },
        },
    ])
    runner.service_counts = {"plain": 5, "mtls": 5}
    runner.condition_names = {"plain": "chain_5svc_plain", "mtls": "chain_5svc_mtls"}

    summary = runner.summarize_resource_samples()
    mtls = summary["by_condition"]["mtls"]

    assert mtls["available"] is False
    assert mtls["sidecar_sample_row_count"] == 4
    assert mtls["failures"][0]["reason"] == (
        "mTLS resource sample CSV missing istio-proxy rows for one or more service pods"
    )
    assert mtls["failures"][0]["missing_sidecar_pods"] == ["mtls-service-5"]


def test_summarize_resource_samples_fails_plain_when_sidecar_rows_appear(tmp_path: Path):
    plain_pass = tmp_path / "plain-sidecar.csv"
    mtls_pass = tmp_path / "mtls.csv"
    write_resource_csv(
        plain_pass,
        [
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "inference", "cpu_usage": "100m", "memory_usage": "200Mi"},
            {"timestamp": "t1", "namespace": "plain-svc", "container_name": "istio-proxy", "cpu_usage": "20m", "memory_usage": "40Mi"},
        ],
    )
    write_resource_csv(
        mtls_pass,
        [
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "inference", "cpu_usage": "150m", "memory_usage": "250Mi"},
            {"timestamp": "t1", "namespace": "mtls-svc", "container_name": "istio-proxy", "cpu_usage": "25m", "memory_usage": "50Mi"},
        ],
    )

    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
        },
    ])

    summary = runner.summarize_resource_samples()
    plain = summary["by_condition"]["plain"]

    assert plain["available"] is False
    assert plain["sidecar_sample_row_count"] == 1
    assert plain["sidecar_metrics_available"] is True
    assert plain["failures"][0]["reason"] == "plain resource sample CSV contained istio-proxy rows"


def test_summarize_resource_samples_fails_chain5_plain_when_sidecar_rows_appear(tmp_path: Path):
    plain_pass = tmp_path / "chain5-plain-sidecar.csv"
    mtls_pass = tmp_path / "chain5-mtls.csv"
    write_resource_csv(
        plain_pass,
        [
            {
                "timestamp": "t1",
                "namespace": "plain-svc",
                "pod_name": "plain-service-1",
                "container_name": "inference",
                "cpu_usage": "100m",
                "memory_usage": "200Mi",
            },
            {
                "timestamp": "t1",
                "namespace": "plain-svc",
                "pod_name": "plain-service-1",
                "container_name": "istio-proxy",
                "cpu_usage": "20m",
                "memory_usage": "40Mi",
            },
        ],
    )
    write_resource_csv(
        mtls_pass,
        [
            {
                "timestamp": "t1",
                "namespace": "mtls-svc",
                "pod_name": f"mtls-service-{index}",
                "container_name": "inference",
                "cpu_usage": "150m",
                "memory_usage": "250Mi",
            }
            for index in range(1, 6)
        ]
        + [
            {
                "timestamp": "t1",
                "namespace": "mtls-svc",
                "pod_name": f"mtls-service-{index}",
                "container_name": "istio-proxy",
                "cpu_usage": "25m",
                "memory_usage": "50Mi",
            }
            for index in range(1, 6)
        ],
    )
    runner = build_runner([
        {
            "pass": 1,
            "execution_index": 1,
            "condition_key": "plain",
            "resource_samples": str(plain_pass),
            "service_namespace": "plain-svc",
            "client_namespace": "plain-client",
        },
        {
            "pass": 1,
            "execution_index": 2,
            "condition_key": "mtls",
            "resource_samples": str(mtls_pass),
            "service_namespace": "mtls-svc",
            "client_namespace": "mtls-client",
            "operational_overhead": {
                "service_pods": [
                    {"pod_name": f"mtls-service-{index}", "sidecar_present": True}
                    for index in range(1, 6)
                ]
            },
        },
    ])
    runner.service_counts = {"plain": 5, "mtls": 5}
    runner.condition_names = {"plain": "chain_5svc_plain", "mtls": "chain_5svc_mtls"}

    summary = runner.summarize_resource_samples()

    assert summary["by_condition"]["plain"]["available"] is False
    assert summary["by_condition"]["plain"]["failures"][0]["reason"] == (
        "plain resource sample CSV contained istio-proxy rows"
    )


def test_run_condition_once_records_mtls_security_preflight_before_benchmark(tmp_path: Path):
    runner = RQ21PairedBenchmarkRunner.__new__(RQ21PairedBenchmarkRunner)
    runner.args = Namespace(
        preserve_namespaces=True,
        cleanup_on_failure=False,
        disable_resource_sampling=False,
    )
    runner.completed_conditions = []
    runner.resources_deployed = False
    runner.current_context = None
    context = build_condition_context(tmp_path, key="mtls")

    preflight_artifact = tmp_path / "preflight"
    preflight_artifact.mkdir()
    (preflight_artifact / "rq21_preflight_metadata.json").write_text(
        json.dumps(
            {
                "preflight_passed": True,
                "enforcement_validation": {
                    "passed": True,
                    "authorization_policy_expected_principal": "cluster.local/ns/mtls-svc/sa/rq21-chain2-svc1",
                    "full_chain_probe": {"succeeded": True},
                    "non_mesh_direct_denial_probe": {"blocked_as_expected": True},
                },
            }
        ),
        encoding="utf-8",
    )
    calls: list[str] = []

    runner.condition_context = lambda *_args: context
    runner.generate_manifests = lambda _context: {"passed": True}
    runner.apply_manifests = lambda _context: calls.append("apply")
    runner.wait_for_ready = lambda _context: calls.append("ready")
    runner.validate_mtls_runtime = lambda _context: {"passed": True}
    runner.run_mtls_security_preflight = lambda _context: calls.append("security") or preflight_artifact
    runner.capture_operational_overhead = lambda _context: {"summary": {}}
    runner.run_condition_benchmark = lambda _context, _pass: calls.append("benchmark")
    runner.gather_diagnostics = lambda _context: calls.append("diagnostics")

    runner.run_condition_once("mtls", 1, 2)

    assert calls.index("security") < calls.index("benchmark")
    record = runner.completed_conditions[0]
    assert record["security_preflight_artifact"] == str(preflight_artifact)
    assert record["security_validation_passed"] is True
    assert record["security_validation"]["full_chain_positive_probe_passed"] is True
    assert record["security_validation"]["non_mesh_direct_denial_probe_passed"] is True


def test_write_aggregated_results_merges_overall_passes_and_paired_deltas(tmp_path: Path):
    runner = build_runner([])
    runner.merged_dir = tmp_path
    rows = [
        {
            "paired_pass": "1",
            "condition_key": "plain",
            "condition": "chain_2svc_plain",
            "end_to_end_ms": "10",
            "total_compute_ms": "8",
            "non_compute_overhead_ms": "2",
            "hop_1_forward_ms": "4",
            "hop_2_forward_ms": "0",
        },
        {
            "paired_pass": "1",
            "condition_key": "plain",
            "condition": "chain_2svc_plain",
            "end_to_end_ms": "12",
            "total_compute_ms": "9",
            "non_compute_overhead_ms": "3",
            "hop_1_forward_ms": "5",
            "hop_2_forward_ms": "0",
        },
        {
            "paired_pass": "1",
            "condition_key": "mtls",
            "condition": "chain_2svc_mtls",
            "end_to_end_ms": "15",
            "total_compute_ms": "9",
            "non_compute_overhead_ms": "6",
            "hop_1_forward_ms": "6",
            "hop_2_forward_ms": "0",
        },
        {
            "paired_pass": "1",
            "condition_key": "mtls",
            "condition": "chain_2svc_mtls",
            "end_to_end_ms": "17",
            "total_compute_ms": "10",
            "non_compute_overhead_ms": "7",
            "hop_1_forward_ms": "7",
            "hop_2_forward_ms": "0",
        },
    ]
    summary = {
        "smoke": False,
        "image_ref": "example.azurecr.io/thesis-inference@sha256:abc",
        "mesh_revision": "asm-1-29",
        "execution_plan": {"paired_passes": 1},
        "conditions": [{"condition_key": "plain"}, {"condition_key": "mtls"}],
        "requirements": {"resource_metrics_complete": True, "blocking_issues": []},
        "latency": {
            "comparison": {
                "mean_latency_overhead_ms": 5.0,
                "mean_latency_overhead_pct": 45.4545454545,
                "p95_latency_overhead_ms": 5.0,
            }
        },
        "resources": {
            "by_condition": {
                "plain": {"available": True, "sample_count": 1, "total_pod_cpu_mcores_mean": 100.0},
                "mtls": {"available": True, "sample_count": 1, "total_pod_cpu_mcores_mean": 120.0},
            },
            "comparison": {"total_pod_cpu_mcores_mean_overhead": 20.0},
        },
        "operational": {
            "by_condition": {
                "plain": {"available": True, "deployment_complexity": {"kubernetes_object_count": 8}},
                "mtls": {"available": True, "deployment_complexity": {"kubernetes_object_count": 13}},
            },
            "comparison": {"service_schedule_to_ready_seconds_overhead": 3.0},
        },
    }

    aggregate = runner.write_aggregated_results(summary, rows)

    assert aggregate["overall_by_condition"]["plain"]["latency"]["end_to_end_ms"]["mean"] == 11.0
    assert aggregate["overall_by_condition"]["mtls"]["latency"]["end_to_end_ms"]["mean"] == 16.0
    assert aggregate["paired_pass_deltas"][0]["mean_latency_overhead_ms"] == 5.0
    assert aggregate["paired_pass_deltas"][0]["non_compute_overhead_delta_ms"] == 4.0
    assert (tmp_path / "aggregated_results.json").exists()
    assert (tmp_path / "aggregated_results.csv").exists()
    assert (tmp_path / "aggregated_results.md").exists()
    persisted = json.loads((tmp_path / "aggregated_results.json").read_text(encoding="utf-8"))
    assert persisted["run"]["total_iteration_rows"] == 4


def test_chain5_activation_and_forwarding_reporting_includes_all_five_hops():
    runner = build_runner([])
    runner.condition_names = {"plain": "chain_5svc_plain", "mtls": "chain_5svc_mtls"}
    runner.service_counts = {"plain": 5, "mtls": 5}
    rows = []
    for key, offset in (("plain", 0), ("mtls", 100)):
        row = {
            "condition_key": key,
            "condition": f"chain_5svc_{key}",
            "end_to_end_ms": str(10 + offset),
            "total_compute_ms": "8",
            "non_compute_overhead_ms": "2",
            "total_activation_bytes": str(1500 + offset),
        }
        for hop in range(1, 6):
            row[f"hop_{hop}_activation_bytes"] = str((hop * 100) + offset)
            row[f"hop_{hop}_forward_ms"] = str(hop + offset)
        rows.append(row)

    summary = runner.summarize_latency(rows)

    mtls = summary["by_condition"]["mtls"]
    comparison = summary["comparison"]
    for hop in range(1, 6):
        assert mtls[f"hop_{hop}_activation_bytes_mean"] == (hop * 100) + 100
        assert mtls[f"hop_{hop}_forward_ms_mean"] == hop + 100
        assert comparison[f"hop_{hop}_activation_bytes_mean_delta"] == 100
        assert comparison[f"hop_{hop}_forward_ms_mean_delta"] == 100


def test_summarize_operational_overhead_computes_startup_and_complexity_deltas():
    runner = build_runner([
        {
            "pass": 1,
            "condition_key": "plain",
            "operational_overhead": {
                "summary": {
                    "service_pod_count": 2,
                    "service_scheduling_delay_seconds_mean": 1.0,
                    "service_schedule_to_ready_seconds_mean": 4.0,
                    "service_app_started_delay_seconds_mean": 2.0,
                    "service_sidecar_started_delay_seconds_mean": None,
                    "service_failed_scheduling_event_count": 0,
                    "benchmark_requested_cpu_mcores_total": 3000.0,
                    "benchmark_requested_memory_mib_total": 3072.0,
                    "node_request_headroom_cpu_mcores": 5000.0,
                    "node_request_headroom_memory_mib": 9000.0,
                },
                "deployment_complexity": {
                    "aks_enablement_step_count": 0,
                    "kubernetes_object_count": 5,
                    "always_on_control_plane_pod_count": 0,
                    "per_workload_injected_container_count": 0.0,
                    "total_injected_container_count": 0,
                },
                "operational_complexity": {
                    "mesh_revision": None,
                    "sidecar_readiness_failure_count": 0,
                    "sidecar_restart_total": 0,
                },
            },
        },
        {
            "pass": 1,
            "condition_key": "mtls",
            "operational_overhead": {
                "summary": {
                    "service_pod_count": 2,
                    "service_scheduling_delay_seconds_mean": 1.5,
                    "service_schedule_to_ready_seconds_mean": 6.5,
                    "service_app_started_delay_seconds_mean": 2.5,
                    "service_sidecar_started_delay_seconds_mean": 3.0,
                    "service_failed_scheduling_event_count": 1,
                    "benchmark_requested_cpu_mcores_total": 3200.0,
                    "benchmark_requested_memory_mib_total": 3584.0,
                    "node_request_headroom_cpu_mcores": 4800.0,
                    "node_request_headroom_memory_mib": 8488.0,
                },
                "deployment_complexity": {
                    "aks_enablement_step_count": 1,
                    "kubernetes_object_count": 9,
                    "always_on_control_plane_pod_count": 4,
                    "per_workload_injected_container_count": 1.0,
                    "total_injected_container_count": 2,
                },
                "operational_complexity": {
                    "mesh_revision": "asm-1-29",
                    "sidecar_readiness_failure_count": 0,
                    "sidecar_restart_total": 0,
                },
            },
        },
    ])

    summary = runner.summarize_operational_overhead()
    plain = summary["by_condition"]["plain"]
    mtls = summary["by_condition"]["mtls"]
    comparison = summary["comparison"]

    assert plain["available"] is True
    assert mtls["available"] is True
    assert plain["service_schedule_to_ready_seconds_mean"] == 4.0
    assert mtls["service_sidecar_started_delay_seconds_mean"] == 3.0
    assert comparison["service_scheduling_delay_seconds_overhead"] == 0.5
    assert comparison["service_schedule_to_ready_seconds_overhead"] == 2.5
    assert comparison["benchmark_requested_cpu_mcores_overhead"] == 200.0
    assert comparison["deployment_complexity_delta"] == {
        "additional_aks_enablement_step_count": 1,
        "additional_kubernetes_object_count": 4,
        "additional_service_account_count": 0,
        "additional_peer_authentication_count": 0,
        "additional_authorization_policy_count": 0,
        "additional_always_on_control_plane_pod_count": 4,
        "additional_injected_container_count": 2,
    }
