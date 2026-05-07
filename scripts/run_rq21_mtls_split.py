from __future__ import annotations

import argparse
from collections import Counter
import csv
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import shutil
import sys
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.run_rq21_paired_benchmark as paired  # noqa: E402
from scripts.run_rq21_fully_controlled import (  # noqa: E402
    DEFAULT_BENCHMARK_NODE_TAINT,
    DEFAULT_CLIENT_POD,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_LOCATION,
    DEFAULT_NODE_COUNT,
    DEFAULT_NODE_VM_SIZE,
    DEFAULT_NODEPOOL,
    DEFAULT_RESOURCE_GROUP,
    DEFAULT_SYSTEM_NODE_COUNT,
    DEFAULT_SYSTEM_NODE_VM_SIZE,
    DEFAULT_SYSTEM_NODEPOOL,
    INFRA_DIR,
    PipelineError,
    RQ21PreflightRunner,
    default_kubeconfig_path,
    ensure_command,
    is_avoidable_istio_control_plane_pod,
    kubectl_json,
    kubectl_json_or_none,
    load_yaml,
    log,
    placement_requires_control_plane_isolation,
    placement_tolerations,
    run_command,
    toleration_matches_taint,
    utc_run_stamp,
    warn,
)


SPLIT_SPECS: dict[str, dict[str, Any]] = {
    "l1": {
        "label": "split_after_layer1",
        "split_points": ["layer1"],
        "protected_activation_bytes": 64 * 56 * 56 * 4,
    },
    "l2": {
        "label": "split_after_layer2",
        "split_points": ["layer2"],
        "protected_activation_bytes": 128 * 28 * 28 * 4,
    },
    "l3": {
        "label": "split_after_layer3",
        "split_points": ["layer3"],
        "protected_activation_bytes": 256 * 14 * 14 * 4,
    },
    "l4": {
        "label": "split_after_layer4",
        "split_points": ["layer4"],
        "protected_activation_bytes": 512 * 7 * 7 * 4,
        "compute_degenerate": True,
    },
}
SPLIT_KEYS = tuple(SPLIT_SPECS)
CONDITION_KEYS = tuple(
    f"{split_key}_{mode}"
    for split_key in SPLIT_KEYS
    for mode in ("plain", "mtls")
)
PROTECTED_HOP_INDEX = 2

CONDITION_CONFIGS = {
    "l1_plain": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l1_plain.yaml",
    "l1_mtls": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l1_mtls.yaml",
    "l2_plain": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l2_plain.yaml",
    "l2_mtls": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l2_mtls.yaml",
    "l3_plain": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l3_plain.yaml",
    "l3_mtls": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l3_mtls.yaml",
    "l4_plain": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l4_plain.yaml",
    "l4_mtls": "configs/rq2/2.1/mtls_split/rq2_1_mtls_split_l4_mtls.yaml",
}


def split_key_for_condition(key: str) -> str:
    return key.split("_", 1)[0]


def security_mode_for_condition(key: str) -> str:
    return key.rsplit("_", 1)[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "RQ2.1 split-point sensitivity runner. Runs four two-service split "
            "points, each as a matched plain versus managed-Istio mTLS/AuthZ pair."
        )
    )
    for key, default in CONDITION_CONFIGS.items():
        parser.add_argument(f"--{key.replace('_', '-')}-config", default=default)
    parser.add_argument("--results-root", default=str(REPO_ROOT / "results_exports"))
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD)
    parser.add_argument("--nodepool", default=DEFAULT_NODEPOOL)
    parser.add_argument("--provision", action="store_true")
    parser.add_argument("--provisioner", choices=["terraform"], default="terraform")
    parser.add_argument("--acr-name", default=None)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--image-ref", default=None)
    parser.add_argument("--image-tag", default=f"rq21-mtls-split-{utc_run_stamp().lower()}")
    parser.add_argument("--local-image", default="thesis-inference:latest")
    parser.add_argument("--no-auto-push-missing-image", action="store_true")
    parser.add_argument("--resource-group", default=DEFAULT_RESOURCE_GROUP)
    parser.add_argument("--cluster-name", default=DEFAULT_CLUSTER_NAME)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--node-count", type=int, default=DEFAULT_NODE_COUNT)
    parser.add_argument("--node-vm-size", default=DEFAULT_NODE_VM_SIZE)
    parser.set_defaults(isolated_node_pools=True)
    parser.add_argument("--isolated-node-pools", dest="isolated_node_pools", action="store_true")
    parser.add_argument("--single-node-pool", dest="isolated_node_pools", action="store_false")
    parser.add_argument("--system-nodepool", default=DEFAULT_SYSTEM_NODEPOOL)
    parser.add_argument("--system-node-count", type=int, default=DEFAULT_SYSTEM_NODE_COUNT)
    parser.add_argument("--system-node-vm-size", default=DEFAULT_SYSTEM_NODE_VM_SIZE)
    parser.add_argument("--benchmark-taint", default=DEFAULT_BENCHMARK_NODE_TAINT)
    parser.add_argument("--skip-mesh-enable", action="store_true")
    parser.add_argument("--mesh-revision", default=None)
    parser.add_argument("--readiness-timeout", type=int, default=None)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--split-passes", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=42)
    parser.add_argument(
        "--order",
        choices=["seeded", "fixed", "reverse"],
        default="seeded",
        help="Split order mode for pass 1; later passes rotate the split order.",
    )
    parser.add_argument("--preserve-namespaces", action="store_true")
    parser.add_argument("--cleanup-on-failure", action="store_true")
    parser.add_argument("--destroy-infrastructure-on-success", action="store_true")
    parser.add_argument("--destroy-infrastructure-on-failure", action="store_true")
    parser.add_argument("--disable-resource-sampling", action="store_true")
    parser.add_argument("--resource-sample-interval-seconds", type=float, default=5.0)
    parser.add_argument("--resource-sample-max-samples", type=int, default=100000)
    parser.add_argument("--resource-metric-prime-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--resource-metric-prime-interval-seconds", type=float, default=5.0)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    if args.build and not args.push:
        parser.error("--build requires --push")
    if args.image_ref and (args.push or args.build):
        parser.error("--image-ref cannot be combined with --push/--build")
    if (args.destroy_infrastructure_on_success or args.destroy_infrastructure_on_failure) and not args.provision:
        parser.error("infrastructure destroy flags require --provision")
    if args.split_passes < 1:
        parser.error("--split-passes must be at least 1")
    if args.resource_sample_interval_seconds < 0:
        parser.error("--resource-sample-interval-seconds must be non-negative")
    if args.resource_metric_prime_timeout_seconds <= 0:
        parser.error("--resource-metric-prime-timeout-seconds must be greater than 0")
    if args.resource_metric_prime_interval_seconds <= 0:
        parser.error("--resource-metric-prime-interval-seconds must be greater than 0")
    return args


class RQ21MtlsSplitRunner(paired.RQ21PairedBenchmarkRunner):
    condition_keys = CONDITION_KEYS
    split_keys = SPLIT_KEYS

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.repo_root = REPO_ROOT
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))
        self.source_paths = {
            key: (self.repo_root / getattr(args, f"{key}_config")).resolve()
            for key in self.condition_keys
        }
        self.raw_configs = {
            key: load_yaml(path)
            for key, path in self.source_paths.items()
        }
        self.condition_names = {
            key: str(paired.first_condition(config).get("name"))
            for key, config in self.raw_configs.items()
        }
        self.service_counts = {
            key: paired.service_count_for_condition(paired.first_condition(config))
            for key, config in self.raw_configs.items()
        }
        self.run_stamp = utc_run_stamp()
        self.artifact_dir = Path(args.results_root).resolve() / f"rq2_1_mtls_split_{self.run_stamp}"
        self.config_dir = self.artifact_dir / "effective_configs"
        self.conditions_root = self.artifact_dir / "conditions"
        self.merged_dir = self.artifact_dir / "merged"
        self.static_dir = self.artifact_dir / "static_validation"
        self.run_metadata_path = self.artifact_dir / "rq2_1_mtls_split_run_metadata.json"

        self.effective_config_paths: dict[str, Path] = {}
        self.effective_image_ref = ""
        self.mesh_revision = ""
        self.acr_name = args.acr_name or self._derive_acr_name()
        self.execution_plan = self._build_execution_plan()
        self.completed_conditions: list[dict[str, Any]] = []
        self.current_context: paired.ConditionContext | None = None
        self.resources_deployed = False
        self.lifecycle_runner: RQ21PreflightRunner | None = None
        self.infrastructure_provisioned = False
        self.infrastructure_destroyed = False

    def _derive_acr_name(self) -> str | None:
        for config in self.raw_configs.values():
            image = str((config.get("kubernetes") or {}).get("image") or "")
            if ".azurecr.io/" in image:
                return image.split(".azurecr.io/", 1)[0]
        return None

    def _primary_mtls_key(self) -> str:
        return "l2_mtls"

    def _build_execution_plan(self) -> dict[str, Any]:
        if self.args.order == "reverse":
            first_split_order = list(reversed(self.split_keys))
        else:
            first_split_order = list(self.split_keys)
            if self.args.order == "seeded":
                random.Random(self.args.order_seed).shuffle(first_split_order)

        passes = []
        for pass_index in range(1, self.args.split_passes + 1):
            offset = (pass_index - 1) % len(first_split_order)
            split_order = first_split_order[offset:] + first_split_order[:offset]
            security_order = ["plain", "mtls"] if pass_index % 2 == 1 else ["mtls", "plain"]
            order = [
                f"{split_key}_{mode}"
                for split_key in split_order
                for mode in security_order
            ]
            passes.append({
                "pass": pass_index,
                "split_order": split_order,
                "security_order": security_order,
                "order": order,
            })
        return {
            "order_mode": self.args.order,
            "order_seed": self.args.order_seed,
            "split_passes": self.args.split_passes,
            "split_keys": list(self.split_keys),
            "condition_keys": list(self.condition_keys),
            "protected_hop_index": PROTECTED_HOP_INDEX,
            "splits": {
                key: {
                    "label": spec["label"],
                    "split_points": spec["split_points"],
                    "protected_activation_bytes": spec["protected_activation_bytes"],
                    "compute_degenerate": bool(spec.get("compute_degenerate", False)),
                }
                for key, spec in SPLIT_SPECS.items()
            },
            "passes": passes,
        }

    def active_hop_indexes(self) -> list[int]:
        return [1, 2]

    def expected_downstream_segments(self, service_count: int | None = None) -> list[str]:
        return ["2"]

    def lifecycle_helper(self) -> RQ21PreflightRunner:
        if self.lifecycle_runner is None:
            lifecycle_root = self.artifact_dir / "lifecycle"
            lifecycle_manifest_dir = lifecycle_root / "manifests"
            self.lifecycle_runner = RQ21PreflightRunner(
                self._helper_args(
                    config_path=self.source_paths[self._primary_mtls_key()],
                    results_root=lifecycle_root,
                    manifest_output_dir=lifecycle_manifest_dir,
                    preserve_existing=True,
                )
            )
            self.lifecycle_runner.prepare_artifact_dirs()
        return self.lifecycle_runner

    def _configured_mtls_image_ref(self) -> str:
        return str(
            (self.raw_configs[self._primary_mtls_key()].get("kubernetes") or {}).get("image") or ""
        ).strip()

    def _configured_mesh_revision(self) -> str:
        return str(
            self.args.mesh_revision
            or ((self.raw_configs[self._primary_mtls_key()].get("kubernetes") or {}).get("mesh") or {}).get("revision")
            or ""
        ).strip()

    def verify_required_files(self) -> None:
        required_paths = [
            *self.source_paths.values(),
            self.repo_root / "run_k8s_experiment.py",
            self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py",
            self.repo_root / "scripts" / "run_rq21_fully_controlled.py",
            self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py",
        ]
        if self.args.provision:
            required_paths.extend([INFRA_DIR / "main.tf", INFRA_DIR / "variables.tf", INFRA_DIR / "outputs.tf"])
        for path in required_paths:
            if not path.exists():
                raise PipelineError(f"Required file is missing: {path}")

    def verify_host_prerequisites(self) -> None:
        ensure_command("python")
        if self.args.generate_only:
            return
        ensure_command("kubectl")
        ensure_command("az")
        if self.args.provision:
            ensure_command("terraform")
        if self.args.push:
            ensure_command("docker")

    def validate_configs(self) -> None:
        errors: list[str] = []
        expected_names = {
            key: f"chain_2svc_split_{split_key}_{mode}"
            for split_key in self.split_keys
            for mode in ("plain", "mtls")
            for key in (f"{split_key}_{mode}",)
        }
        for key, expected_name in expected_names.items():
            raw = self.raw_configs[key]
            condition = paired.first_condition(raw)
            if self.condition_names.get(key) != expected_name:
                errors.append(f"{key} config must contain condition {expected_name}")
            if paired.service_count_for_condition(condition) != 2:
                errors.append(f"{key} must be a two-service chain")
            expected_splits = list(SPLIT_SPECS[split_key_for_condition(key)]["split_points"])
            if list(condition.get("chain_split_points") or []) != expected_splits:
                errors.append(f"{key} must use chain_split_points={expected_splits}")

        for split_key in self.split_keys:
            plain = self.raw_configs[f"{split_key}_plain"]
            mtls = self.raw_configs[f"{split_key}_mtls"]
            if paired.first_condition(plain).get("chain_split_points") != paired.first_condition(mtls).get("chain_split_points"):
                errors.append(f"{split_key} plain and mTLS configs must use identical chain_split_points")

        for section in ("model", "benchmark", "grpc", "cpu_stabilisation", "carry_forward", "parity", "warmup_calibration"):
            values = [self.raw_configs[key].get(section) for key in self.condition_keys]
            if any(value != values[0] for value in values[1:]):
                errors.append(f"All split-sensitivity configs must match section '{section}'")

        benchmark = self.raw_configs[self.condition_keys[0]].get("benchmark") or {}
        if int(benchmark.get("rounds") or 0) != 1:
            errors.append("Split-sensitivity configs must set benchmark.rounds=1; use --split-passes for repeated passes")

        images = {
            str((self.raw_configs[key].get("kubernetes") or {}).get("image") or "")
            for key in self.condition_keys
        }
        if not self.args.image_ref and len(images) != 1:
            errors.append(f"All split-sensitivity configs must use the same image reference; found {sorted(images)}")

        namespaces: set[str] = set()
        client_namespaces: set[str] = set()
        revisions: set[str] = set()
        first_k8s = self.raw_configs[self.condition_keys[0]].get("kubernetes") or {}
        for key in self.condition_keys:
            raw_k8s = self.raw_configs[key].get("kubernetes") or {}
            mode = security_mode_for_condition(key)
            for section in ("resources", "client_resources", "placement", "service_name_template", "grpc_port", "max_message_bytes"):
                if raw_k8s.get(section) != first_k8s.get(section):
                    errors.append(f"All configs must match kubernetes.{section}; {key} differs")
            namespace = str(raw_k8s.get("namespace") or "")
            client_namespace = str(raw_k8s.get("client_namespace") or "")
            if not namespace or namespace in namespaces:
                errors.append(f"{key} service namespace must be non-empty and unique")
            if not client_namespace or client_namespace in client_namespaces:
                errors.append(f"{key} client namespace must be non-empty and unique")
            namespaces.add(namespace)
            client_namespaces.add(client_namespace)
            if namespace == client_namespace:
                errors.append(f"{key} must keep service and client namespaces separate")

            mesh = raw_k8s.get("mesh") or {}
            if mode == "plain":
                if raw_k8s.get("security_condition") != "plain":
                    errors.append(f"{key} must set kubernetes.security_condition=plain")
                if bool(isinstance(mesh, dict) and mesh.get("enabled", False)):
                    errors.append(f"{key} must not enable mesh")
                continue

            if raw_k8s.get("security_condition") != "mtls":
                errors.append(f"{key} must set kubernetes.security_condition=mtls")
            if not isinstance(mesh, dict) or not bool(mesh.get("enabled", False)):
                errors.append(f"{key} must enable kubernetes.mesh.enabled")
                continue
            if str(mesh.get("namespace") or namespace) != namespace:
                errors.append(f"{key} kubernetes.mesh.namespace must match kubernetes.namespace")
            if str(client_namespace) == str(namespace):
                errors.append(f"{key} must keep benchmark client outside the mesh namespace")
            revision = str(mesh.get("revision") or "").strip()
            if revision:
                revisions.add(revision)
            service_accounts = {
                str(account_key)
                for account_key, value in (mesh.get("service_accounts") or {}).items()
                if str(value or "").strip()
            }
            if service_accounts != {"1", "2"}:
                errors.append(f"{key} must define ServiceAccounts for segments 1 and 2; found {sorted(service_accounts)}")
            proxy_resources = mesh.get("proxy_resources") or {}
            for resource_key in ("cpu_request", "cpu_limit", "memory_request", "memory_limit"):
                if not str(proxy_resources.get(resource_key) or "").strip():
                    errors.append(f"{key} must set kubernetes.mesh.proxy_resources.{resource_key}")
            peer = mesh.get("peer_authentication") or {}
            strict_segments = {
                str(item.get("segment_index"))
                for item in peer.get("strict_workloads") or []
                if isinstance(item, dict) and str(item.get("mode") or "STRICT").upper() == "STRICT"
            }
            if not bool(peer.get("enabled", False)) or str(peer.get("namespace_mode") or "") != "PERMISSIVE":
                errors.append(f"{key} must enable PERMISSIVE namespace PeerAuthentication")
            if strict_segments != {"2"}:
                errors.append(f"{key} must target only service2 as STRICT; found {sorted(strict_segments)}")
            authz = mesh.get("authorization_policy") or {}
            if not bool(authz.get("enabled", False)):
                errors.append(f"{key} must enable AuthorizationPolicy")
            if str(authz.get("source_segment_index") or "") != "1" or str(authz.get("downstream_segment_index") or "") != "2":
                errors.append(f"{key} AuthorizationPolicy must be service1 -> service2")

        if len(revisions) != 1:
            errors.append(f"All mTLS configs must use one mesh revision; found {sorted(revisions)}")

        if bool(getattr(self.args, "isolated_node_pools", False)):
            if int(getattr(self.args, "node_count", DEFAULT_NODE_COUNT)) != 1:
                errors.append("Final isolated-pool RQ2.1 runs must use benchmark --node-count 1")
            if int(getattr(self.args, "system_node_count", DEFAULT_SYSTEM_NODE_COUNT)) != 1:
                errors.append("Final isolated-pool RQ2.1 runs must use --system-node-count 1")
            if str(getattr(self.args, "node_vm_size", DEFAULT_NODE_VM_SIZE)) != DEFAULT_NODE_VM_SIZE:
                errors.append(f"Final isolated-pool RQ2.1 runs must use benchmark --node-vm-size {DEFAULT_NODE_VM_SIZE}")
            if str(getattr(self.args, "system_node_vm_size", DEFAULT_SYSTEM_NODE_VM_SIZE)) != DEFAULT_SYSTEM_NODE_VM_SIZE:
                errors.append(f"Final isolated-pool RQ2.1 runs must use --system-node-vm-size {DEFAULT_SYSTEM_NODE_VM_SIZE}")
            for key in self.condition_keys:
                placement = (self.raw_configs[key].get("kubernetes") or {}).get("placement") or {}
                if str(placement.get("node_pool") or "") != str(self.args.nodepool):
                    errors.append(f"{key} kubernetes.placement.node_pool must be {self.args.nodepool}")
                if not placement_requires_control_plane_isolation(placement):
                    errors.append(f"{key} must require control-plane isolation")
                if not any(toleration_matches_taint(item, self.args.benchmark_taint) for item in placement_tolerations(placement)):
                    errors.append(f"{key} must tolerate benchmark taint {self.args.benchmark_taint}")
                explicit_selector = placement.get("node_selector") or {}
                if str(explicit_selector.get("workload") or "") != "benchmark":
                    errors.append(f"{key} kubernetes.placement.node_selector.workload must be benchmark")

        if errors:
            raise PipelineError("RQ2.1 mTLS split config validation failed:\n- " + "\n- ".join(errors))

    def write_effective_configs(self) -> None:
        for key in self.condition_keys:
            raw = deepcopy(self.raw_configs[key])
            raw.setdefault("kubernetes", {})
            raw["kubernetes"]["image"] = self.effective_image_ref
            raw["kubernetes"].setdefault("placement", {})
            raw["kubernetes"]["placement"]["node_pool"] = self.args.nodepool
            if self.args.readiness_timeout is not None:
                raw["kubernetes"]["readiness_timeout"] = float(self.args.readiness_timeout)
            mesh = raw["kubernetes"].get("mesh") or {}
            if isinstance(mesh, dict) and mesh.get("enabled", False):
                raw["kubernetes"].setdefault("mesh", {})
                raw["kubernetes"]["mesh"]["revision"] = self.mesh_revision
            if self.args.smoke:
                self._apply_smoke_profile(raw)
            condition_name = str(paired.first_condition(raw).get("name") or f"condition_{key}")
            path = self.config_dir / f"{condition_name}_effective.yaml"
            paired.save_yaml(path, raw)
            self.effective_config_paths[key] = path

    def condition_mesh_config(self, context: paired.ConditionContext) -> dict[str, Any]:
        config = load_yaml(context.effective_config_path)
        mesh = ((config.get("kubernetes") or {}).get("mesh") or {})
        return mesh if isinstance(mesh, dict) else {}

    def expected_mtls_authorization_policies(self, context: paired.ConditionContext) -> list[dict[str, str]]:
        mesh = self.condition_mesh_config(context)
        authz = mesh.get("authorization_policy") or {}
        if not isinstance(authz, dict) or not bool(authz.get("enabled", False)):
            return []
        service_accounts = mesh.get("service_accounts") or {}
        source_segment = str(authz.get("source_segment_index") or "1")
        downstream_segment = str(authz.get("downstream_segment_index") or "2")
        source_service_account = str(service_accounts.get(source_segment) or "")
        return [
            {
                "name": str(authz.get("name") or "service2-service1-only"),
                "source_segment_index": source_segment,
                "downstream_segment_index": downstream_segment,
                "expected_principal": f"cluster.local/ns/{context.service_namespace}/sa/{source_service_account}",
            }
        ]

    def expected_policy_shape(self, key: str) -> dict[str, Any]:
        if security_mode_for_condition(key) == "mtls":
            return {"mesh": True, "service_accounts": 2, "peer": 2, "strict": 1, "authz": 1}
        return {"mesh": False, "service_accounts": 0, "peer": 0, "strict": 0, "authz": 0}

    def static_manifest_validation(self, context: paired.ConditionContext) -> dict[str, Any]:
        docs = paired.load_manifest_documents(context.manifest_dir)
        errors: list[str] = []
        kinds = [str(doc.get("kind") or "") for doc in docs]
        expected = self.expected_policy_shape(context.key)
        namespaces = {
            str((doc.get("metadata") or {}).get("name")): doc
            for doc in docs
            if doc.get("kind") == "Namespace"
        }
        deployments = [doc for doc in docs if doc.get("kind") == "Deployment"]
        pod_docs = [doc for doc in docs if doc.get("kind") == "Pod"]
        raw_config = load_yaml(context.effective_config_path)
        placement = (raw_config.get("kubernetes") or {}).get("placement") or {}
        isolated_contract_required = (
            bool(getattr(self.args, "isolated_node_pools", False))
            or placement_requires_control_plane_isolation(placement)
        )
        if isolated_contract_required:
            explicit_selector = {str(k): str(v) for k, v in (placement.get("node_selector") or {}).items()}
            expected_selector = {"agentpool": self.args.nodepool, **explicit_selector}
            workload_specs: list[tuple[str, dict[str, Any]]] = []
            for deployment in deployments:
                name = str((deployment.get("metadata") or {}).get("name") or "unknown")
                spec = (((deployment.get("spec") or {}).get("template") or {}).get("spec") or {})
                workload_specs.append((f"Deployment/{name}", spec))
            for pod_doc in pod_docs:
                name = str((pod_doc.get("metadata") or {}).get("name") or "unknown")
                workload_specs.append((f"Pod/{name}", pod_doc.get("spec") or {}))
            for workload_name, spec in workload_specs:
                observed_selector = {str(k): str(v) for k, v in (spec.get("nodeSelector") or {}).items()}
                for selector_key, expected_value in expected_selector.items():
                    if observed_selector.get(selector_key) != expected_value:
                        errors.append(
                            f"{workload_name} must select benchmark node {selector_key}={expected_value}; "
                            f"found {observed_selector.get(selector_key)}"
                        )
                if not any(toleration_matches_taint(item, self.args.benchmark_taint) for item in (spec.get("tolerations") or [])):
                    errors.append(f"{workload_name} must tolerate benchmark taint {self.args.benchmark_taint}")

        service_labels = ((namespaces.get(context.service_namespace) or {}).get("metadata") or {}).get("labels") or {}
        client_labels = ((namespaces.get(context.client_namespace) or {}).get("metadata") or {}).get("labels") or {}
        if expected["mesh"]:
            if service_labels.get("istio.io/rev") != self.mesh_revision:
                errors.append(f"{context.key} service namespace missing istio.io/rev={self.mesh_revision}")
            if client_labels.get("istio.io/rev") or client_labels.get("istio-injection") == "enabled":
                errors.append(f"{context.key} client namespace must remain non-mesh")
        else:
            if service_labels.get("istio.io/rev") or client_labels.get("istio.io/rev"):
                errors.append(f"{context.key} namespaces must not carry mesh revision labels")

        service_accounts = [doc for doc in docs if doc.get("kind") == "ServiceAccount"]
        peer_items = [doc for doc in docs if doc.get("kind") == "PeerAuthentication"]
        strict_items = [
            item for item in peer_items
            if str(((item.get("spec") or {}).get("mtls") or {}).get("mode") or "").upper() == "STRICT"
        ]
        authz_items = [doc for doc in docs if doc.get("kind") == "AuthorizationPolicy"]
        if len(service_accounts) != expected["service_accounts"]:
            errors.append(f"{context.key} expected {expected['service_accounts']} ServiceAccounts; found {len(service_accounts)}")
        if len(peer_items) != expected["peer"]:
            errors.append(f"{context.key} expected {expected['peer']} PeerAuthentications; found {len(peer_items)}")
        if len(strict_items) != expected["strict"]:
            errors.append(f"{context.key} expected {expected['strict']} STRICT PeerAuthentications; found {len(strict_items)}")
        if len(authz_items) != expected["authz"]:
            errors.append(f"{context.key} expected {expected['authz']} AuthorizationPolicies; found {len(authz_items)}")

        peer_summary: dict[str, Any] = {}
        authz_summary: dict[str, Any] = {}
        if expected["mesh"]:
            peer_errors, peer_summary = self.validate_mtls_peer_authentications(context, peer_items)
            authz_errors, authz_summary = self.validate_mtls_authorization_policies(context, authz_items)
            errors.extend(peer_errors)
            errors.extend(authz_errors)

        required_annotations = {
            "sidecar.istio.io/proxyCPU",
            "sidecar.istio.io/proxyCPULimit",
            "sidecar.istio.io/proxyMemory",
            "sidecar.istio.io/proxyMemoryLimit",
        }
        for deployment in deployments:
            annotations = ((((deployment.get("spec") or {}).get("template") or {}).get("metadata") or {}).get("annotations") or {})
            sidecar_keys = {key for key in annotations if str(key).startswith("sidecar.istio.io/")}
            if expected["mesh"]:
                missing = sorted(required_annotations - set(annotations))
                if missing:
                    errors.append(f"{context.key} deployment missing proxy annotations {missing}")
            elif sidecar_keys:
                errors.append(f"{context.key} deployment has sidecar annotations {sorted(sidecar_keys)}")

        summary = {
            "condition": context.condition_name,
            "condition_key": context.key,
            "split_key": split_key_for_condition(context.key),
            "security_mode": security_mode_for_condition(context.key),
            "manifest_dir": str(context.manifest_dir),
            "expected_shape": expected,
            "kinds": kinds,
            "passed": not errors,
            "errors": errors,
            "peer_authentication_validation": peer_summary,
            "authorization_policy_validation": authz_summary,
        }
        out_path = self.static_dir / f"{context.condition_name}.json"
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if errors:
            raise PipelineError(
                f"Static manifest validation failed for {context.condition_name}:\n- "
                + "\n- ".join(errors)
            )
        return summary

    def _condition_service_name(self, context: paired.ConditionContext, index: int) -> str:
        from src.benchmark.config import format_k8s_service_name

        config = load_yaml(context.effective_config_path)
        template = str((config.get("kubernetes") or {}).get("service_name_template") or "{condition}-svc-{index}")
        return format_k8s_service_name(template, context.condition_name, index)

    def run_full_chain_probe(self, context: paired.ConditionContext) -> dict[str, Any]:
        output_path = context.diagnostics_dir / "full_chain_probe_output.txt"
        target = f"{self._condition_service_name(context, 1)}.{context.service_namespace}.svc.cluster.local:50051"
        result_payload: dict[str, Any] = {
            "target": target,
            "expected_hop_count": context.service_count,
            "expected_hop_indexes": list(range(1, context.service_count + 1)),
            "output_file": str(output_path),
        }
        probe_code = (
            "import json, sys\n"
            "import numpy as np\n"
            "import torch\n"
            "from src.client.chain_client import ChainClient\n"
            "target = sys.argv[1]\n"
            "max_message_bytes = int(sys.argv[2])\n"
            "expected_hops = int(sys.argv[3])\n"
            "torch.set_num_threads(1)\n"
            "torch.set_num_interop_threads(1)\n"
            "client = ChainClient(target, max_message_bytes=max_message_bytes)\n"
            "try:\n"
            "    tensor = torch.from_numpy(np.zeros((1, 3, 224, 224), dtype=np.float32))\n"
            "    response = client.infer_response(tensor)\n"
            "    hops = [{'hop_index': h.hop_index, 'activation_bytes': h.activation_bytes} for h in response.hop_timings]\n"
            "    payload = {'target': target, 'response_shape': list(response.shape), 'hop_count': len(hops), 'hop_indexes': [h['hop_index'] for h in hops], 'hop_timings': hops}\n"
            "    print(json.dumps(payload, indent=2))\n"
            "    if len(hops) != expected_hops or sorted(h['hop_index'] for h in hops) != list(range(1, expected_hops + 1)):\n"
            "        sys.exit(43)\n"
            "finally:\n"
            "    client.close()\n"
        )
        completed = run_command(
            [
                "kubectl", "exec", "-n", context.client_namespace, self.args.client_pod, "--",
                "python", "-c", probe_code, target, "16777216", str(context.service_count),
            ],
            capture_output=True,
            check=False,
            timeout_seconds=max(300, int(self.args.readiness_timeout or 180) * 4),
        )
        combined_output = (completed.stdout or "") + (completed.stderr or "")
        output_path.write_text(combined_output, encoding="utf-8")
        result_payload.update({"returncode": completed.returncode, "succeeded": completed.returncode == 0})
        try:
            payload = json.loads(completed.stdout or "{}")
            if isinstance(payload, dict):
                result_payload.update(payload)
        except json.JSONDecodeError:
            pass
        return result_payload

    def _debug_probe_manifest(self, context: paired.ConditionContext, pod_name_value: str) -> dict[str, Any]:
        config = load_yaml(context.effective_config_path)
        k8s = config.get("kubernetes") or {}
        client_resources = k8s.get("client_resources") or {}
        container: dict[str, Any] = {
            "name": "debug",
            "image": str(k8s.get("image")),
            "imagePullPolicy": str(k8s.get("image_pull_policy") or "Always"),
            "command": ["sleep", "infinity"],
        }
        if client_resources:
            container["resources"] = {
                "requests": {
                    "cpu": str(client_resources.get("cpu_request") or "100m"),
                    "memory": str(client_resources.get("memory_request") or "128Mi"),
                },
                "limits": {
                    "cpu": str(client_resources.get("cpu_limit") or "500m"),
                    "memory": str(client_resources.get("memory_limit") or "512Mi"),
                },
            }
        placement = k8s.get("placement") or {}
        selector = {}
        node_pool = str(placement.get("node_pool") or self.args.nodepool or "").strip()
        if node_pool:
            selector["agentpool"] = node_pool
        selector.update({str(key): str(value) for key, value in (placement.get("node_selector") or {}).items()})
        spec: dict[str, Any] = {"restartPolicy": "Never", "containers": [container]}
        if selector:
            spec["nodeSelector"] = selector
        tolerations = placement_tolerations(placement)
        if tolerations:
            spec["tolerations"] = tolerations
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name_value,
                "namespace": context.client_namespace,
                "labels": {
                    "app": "thesis-inference",
                    "condition": context.condition_name,
                    "experiment-condition": context.condition_name,
                    "workload-role": "debug-client",
                    "role": "debug-client",
                    "mesh-enabled": "false",
                    "security-condition": str(k8s.get("security_condition") or security_mode_for_condition(context.key)),
                },
                "annotations": {"sidecar.istio.io/inject": "false"},
            },
            "spec": spec,
        }

    def run_direct_probe(self, context: paired.ConditionContext, *, expected_blocked: bool) -> dict[str, Any]:
        pod_name_value = "rq21-ms-direct-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        target = f"{self._condition_service_name(context, 2)}.{context.service_namespace}.svc.cluster.local:50051"
        manifest = self._debug_probe_manifest(context, pod_name_value)
        manifest_path = context.diagnostics_dir / f"direct_probe_{context.key}_pod.yaml"
        output_path = context.diagnostics_dir / f"direct_probe_{context.key}_output.txt"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        result_payload: dict[str, Any] = {
            "target": target,
            "expected_blocked": expected_blocked,
            "manifest_file": str(manifest_path),
            "output_file": str(output_path),
            "pod_name": pod_name_value,
            "namespace": context.client_namespace,
            "pod_preserved": True,
        }
        probe_code = (
            "import grpc, sys\n"
            "target = sys.argv[1]\n"
            "timeout = float(sys.argv[2])\n"
            "channel = grpc.insecure_channel(target)\n"
            "try:\n"
            "    grpc.channel_ready_future(channel).result(timeout=timeout)\n"
            "except Exception as exc:\n"
            "    print('CHANNEL_BLOCKED', type(exc).__name__, str(exc))\n"
            "    sys.exit(42)\n"
            "else:\n"
            "    print('CHANNEL_READY')\n"
            "    sys.exit(0)\n"
            "finally:\n"
            "    channel.close()\n"
        )
        try:
            run_command(["kubectl", "apply", "-f", str(manifest_path)], timeout_seconds=90)
            run_command([
                "kubectl", "wait", "--for=condition=Ready", f"pod/{pod_name_value}",
                "-n", context.client_namespace, "--timeout=120s",
            ], timeout_seconds=150)
            completed = run_command([
                "kubectl", "exec", "-n", context.client_namespace, pod_name_value, "--",
                "python", "-c", probe_code, target, "8",
            ], capture_output=True, check=False, timeout_seconds=60)
            output_path.write_text((completed.stdout or "") + (completed.stderr or ""), encoding="utf-8")
            blocked = completed.returncode == 42
            ready = completed.returncode == 0
            passed = blocked if expected_blocked else ready
            result_payload.update({
                "returncode": completed.returncode,
                "blocked": blocked,
                "ready": ready,
                "passed": passed,
            })
            if passed:
                run_command([
                    "kubectl", "delete", "pod", pod_name_value, "-n", context.client_namespace,
                    "--ignore-not-found=true", "--wait=false",
                ], check=False, timeout_seconds=30)
                result_payload["pod_preserved"] = False
        except Exception as exc:
            output_path.write_text(str(exc), encoding="utf-8")
            result_payload.update({"passed": False, "exception": str(exc)})
        return result_payload

    def validate_plain_split_runtime(self, context: paired.ConditionContext) -> dict[str, Any]:
        validation = self.validate_plain_runtime(context)
        errors = list(validation.get("errors") or [])
        full_chain_probe = self.run_full_chain_probe(context)
        if not full_chain_probe.get("succeeded"):
            errors.append(f"{context.key} full-chain positive probe failed")
        direct_probe = self.run_direct_probe(context, expected_blocked=False)
        if not direct_probe.get("passed"):
            errors.append(f"{context.key} direct service2 probe did not become ready")
        validation.update({
            "condition_key": context.key,
            "full_chain_probe": full_chain_probe,
            "direct_service2_probe": direct_probe,
            "passed": not errors,
            "errors": errors,
        })
        (context.diagnostics_dir / "split_plain_runtime_validation.json").write_text(
            json.dumps(validation, indent=2),
            encoding="utf-8",
        )
        if errors:
            raise PipelineError(f"Plain split runtime validation failed for {context.condition_name}:\n- " + "\n- ".join(errors))
        return validation

    def run_mtls_security_preflight(self, context: paired.ConditionContext) -> Path:
        log("Running split-aware RQ2.1 mTLS/security validation before the mTLS benchmark.")
        artifact_dir = context.condition_dir / "security_preflight_split"
        diagnostics_dir = artifact_dir / "diagnostics"
        diagnostics_dir.mkdir(parents=True, exist_ok=True)

        full_chain_probe = self.run_full_chain_probe(context)
        direct_probe = self.run_direct_probe(context, expected_blocked=True)
        authz_expected = [
            policy.get("expected_principal")
            for policy in self.expected_mtls_authorization_policies(context)
            if policy.get("expected_principal")
        ]

        errors: list[str] = []
        if not full_chain_probe.get("succeeded"):
            errors.append("positive service1 full-chain probe failed")
        if not direct_probe.get("passed"):
            errors.append("non-mesh direct-denial probe did not block protected service2 as expected")

        enforcement = {
            "passed": not errors,
            "full_chain_probe": full_chain_probe,
            "non_mesh_direct_denial_probe": {
                "blocked_as_expected": bool(direct_probe.get("passed")),
                "blocked_segments": ["2"] if direct_probe.get("passed") else [],
                "target_results": [
                    {
                        "segment_index": "2",
                        "target": direct_probe.get("target"),
                        "blocked": bool(direct_probe.get("blocked")),
                        "ready": bool(direct_probe.get("ready")),
                        "passed": bool(direct_probe.get("passed")),
                        "returncode": direct_probe.get("returncode"),
                    }
                ],
                "raw_probe": direct_probe,
            },
            "authorization_policy_expected_principal": authz_expected[0] if authz_expected else None,
            "authorization_policy_expected_principals": authz_expected,
            "errors": errors,
        }
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "preflight_passed": not errors,
            "split_aware_preflight": True,
            "condition": context.condition_name,
            "condition_key": context.key,
            "split_key": split_key_for_condition(context.key),
            "service_namespace": context.service_namespace,
            "client_namespace": context.client_namespace,
            "enforcement_validation": enforcement,
            "control_plane_isolation": {},
            "errors": errors,
            "limitations": [
                "Split sensitivity uses the same mTLS/AuthZ enforcement probes as RQ2.1, but accepts arbitrary two-service split points.",
            ],
        }
        metadata_path = artifact_dir / "rq21_preflight_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        marker = context.condition_dir / "security_preflight_artifact.txt"
        marker.write_text(str(artifact_dir) + "\n", encoding="utf-8")
        if errors:
            raise PipelineError(
                f"Split-aware mTLS security validation failed for {context.condition_name}:\n- "
                + "\n- ".join(errors)
            )
        return artifact_dir

    def run_condition_once(self, key: str, pass_index: int, execution_index: int) -> None:
        context = self.condition_context(key, pass_index, execution_index)
        self.current_context = context
        context.condition_dir.mkdir(parents=True, exist_ok=True)
        context.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        static_summary = self.generate_manifests(context)
        try:
            self.apply_manifests(context)
            self.wait_for_ready(context)
            if security_mode_for_condition(key) == "plain":
                validation_artifact = self.validate_plain_split_runtime(context)
                security_preflight_artifact = None
                security_validation = None
                security_validation_passed = None
            else:
                validation_artifact = self.validate_mtls_runtime(context)
                security_preflight_artifact = self.run_mtls_security_preflight(context)
                security_validation = self.read_mtls_security_preflight_result(security_preflight_artifact)
                security_validation_passed = bool(security_validation.get("passed"))
                if not security_validation_passed:
                    raise PipelineError(
                        "mTLS security validation did not pass before benchmarking:\n- "
                        + "\n- ".join(
                            str(item)
                            for item in (security_validation.get("errors") or [security_validation.get("reason")])
                            if item
                        )
                    )
            operational_overhead = self.capture_operational_overhead(context)
            cpu_counter_metrics = self.run_condition_benchmark(context, pass_index)
            self.gather_diagnostics(context)
            self.completed_conditions.append({
                "pass": pass_index,
                "execution_index": execution_index,
                "condition_key": key,
                "split_key": split_key_for_condition(key),
                "security_mode": security_mode_for_condition(key),
                "condition": context.condition_name,
                "condition_dir": str(context.condition_dir),
                "benchmark_dir": str(context.benchmark_dir),
                "resource_samples": str(context.resource_samples_path),
                "static_manifest_validation": static_summary,
                "runtime_validation": validation_artifact,
                "runtime_validation_passed": bool(validation_artifact.get("passed")),
                "operational_overhead": operational_overhead,
                "cpu_counter_metrics": cpu_counter_metrics,
                "security_preflight_artifact": str(security_preflight_artifact) if security_preflight_artifact else None,
                "security_validation": security_validation,
                "security_validation_passed": security_validation_passed,
                "service_namespace": context.service_namespace,
                "client_namespace": context.client_namespace,
                "resource_cpu_measurement": str(self.resource_cpu_measurement_path(context)),
                "resource_metric_prime": str(self.resource_metric_prime_status_path(context))
                if not self.args.disable_resource_sampling
                else None,
            })
            if not self.args.preserve_namespaces:
                self.cleanup_namespaces(context)
        except Exception:
            try:
                self.gather_diagnostics(context)
            except Exception as diag_exc:
                warn(f"Failed to gather diagnostics for {context.condition_name}: {diag_exc}")
            if self.resources_deployed and self.args.cleanup_on_failure:
                self.cleanup_namespaces(context)
            raise
        finally:
            self.current_context = None

    def summarize_latency(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        summaries: dict[str, Any] = {}
        for key in self.condition_keys:
            key_rows = [row for row in rows if str(row.get("condition_key") or "") == key]
            latencies = [v for v in (paired.maybe_float(row.get("end_to_end_ms")) for row in key_rows) if v is not None]
            non_compute = [v for v in (paired.maybe_float(row.get("non_compute_overhead_ms")) for row in key_rows) if v is not None]
            total_compute = [v for v in (paired.maybe_float(row.get("total_compute_ms")) for row in key_rows) if v is not None]
            payload = {
                "condition": key_rows[0].get("condition") if key_rows else self.condition_names.get(key),
                "split_key": split_key_for_condition(key),
                "security_mode": security_mode_for_condition(key),
                "n": len(latencies),
                "mean_ms": paired.mean_or_none(latencies),
                "median_ms": paired.percentile(latencies, 50) if latencies else None,
                "p95_ms": paired.percentile(latencies, 95) if latencies else None,
                "p99_ms": paired.percentile(latencies, 99) if latencies else None,
                "non_compute_overhead_ms_mean": paired.mean_or_none(non_compute),
                "total_compute_ms_mean": paired.mean_or_none(total_compute),
                "expected_protected_activation_bytes": SPLIT_SPECS[split_key_for_condition(key)]["protected_activation_bytes"],
            }
            for metric in [
                "total_activation_bytes",
                "hop_1_activation_bytes",
                "hop_2_activation_bytes",
                "hop_1_forward_ms",
                "hop_2_forward_ms",
            ]:
                values = [v for v in (paired.maybe_float(row.get(metric)) for row in key_rows) if v is not None]
                payload[f"{metric}_mean"] = paired.mean_or_none(values)
            payload["protected_hop_activation_bytes_mean"] = payload.get(f"hop_{PROTECTED_HOP_INDEX}_activation_bytes_mean")
            payload["protected_hop_forward_ms_mean"] = payload.get(f"hop_{PROTECTED_HOP_INDEX}_forward_ms_mean")
            summaries[key] = payload
        return {"by_condition": summaries, "by_split": self.split_latency_deltas(summaries)}

    def split_latency_deltas(self, summaries: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for split_key in self.split_keys:
            plain = summaries.get(f"{split_key}_plain") or {}
            mtls = summaries.get(f"{split_key}_mtls") or {}
            plain_mean = plain.get("mean_ms")
            mtls_mean = mtls.get("mean_ms")
            plain_p95 = plain.get("p95_ms")
            mtls_p95 = mtls.get("p95_ms")
            plain_non_compute = plain.get("non_compute_overhead_ms_mean")
            mtls_non_compute = mtls.get("non_compute_overhead_ms_mean")
            plain_compute = plain.get("total_compute_ms_mean")
            mtls_compute = mtls.get("total_compute_ms_mean")
            delta = (
                mtls_mean - plain_mean
                if isinstance(mtls_mean, (int, float)) and isinstance(plain_mean, (int, float))
                else None
            )
            row = {
                "split_key": split_key,
                "split_label": SPLIT_SPECS[split_key]["label"],
                "split_points": SPLIT_SPECS[split_key]["split_points"],
                "compute_degenerate": bool(SPLIT_SPECS[split_key].get("compute_degenerate", False)),
                "expected_protected_activation_bytes": SPLIT_SPECS[split_key]["protected_activation_bytes"],
                "plain_condition": plain.get("condition"),
                "mtls_condition": mtls.get("condition"),
                "plain_mean_ms": plain_mean,
                "mtls_mean_ms": mtls_mean,
                "mean_latency_overhead_ms": delta,
                "mean_latency_overhead_pct": (
                    ((delta / plain_mean) * 100.0)
                    if isinstance(delta, (int, float)) and isinstance(plain_mean, (int, float)) and plain_mean > 0
                    else None
                ),
                "p95_latency_overhead_ms": (
                    mtls_p95 - plain_p95
                    if isinstance(mtls_p95, (int, float)) and isinstance(plain_p95, (int, float))
                    else None
                ),
                "non_compute_overhead_delta_ms": (
                    mtls_non_compute - plain_non_compute
                    if isinstance(mtls_non_compute, (int, float)) and isinstance(plain_non_compute, (int, float))
                    else None
                ),
                "total_compute_delta_ms": (
                    mtls_compute - plain_compute
                    if isinstance(mtls_compute, (int, float)) and isinstance(plain_compute, (int, float))
                    else None
                ),
            }
            for metric in [
                "total_activation_bytes_mean",
                "protected_hop_activation_bytes_mean",
                "protected_hop_forward_ms_mean",
                "hop_1_activation_bytes_mean",
                "hop_2_activation_bytes_mean",
                "hop_1_forward_ms_mean",
                "hop_2_forward_ms_mean",
            ]:
                plain_value = plain.get(metric)
                mtls_value = mtls.get(metric)
                row[f"{metric}_plain"] = plain_value
                row[f"{metric}_mtls"] = mtls_value
                row[f"{metric}_delta"] = (
                    mtls_value - plain_value
                    if isinstance(mtls_value, (int, float)) and isinstance(plain_value, (int, float))
                    else None
                )
            result[split_key] = row
        return result

    def summarize_resource_samples(self) -> dict[str, Any]:
        summaries = {key: self._resource_summary_for_key(key) for key in self.condition_keys}
        return {"by_condition": summaries, "by_split": self.metric_pair_deltas(summaries)}

    def _resource_summary_for_key(self, key: str) -> dict[str, Any]:
        records = [record for record in self.completed_conditions if str(record.get("condition_key")) == key]
        if not records:
            return {"available": False, "reason": "no completed condition runs were recorded"}
        expected_sidecars = self.expected_policy_shape(key)["mesh"]
        aggregated_cpu = {category: [] for category in paired.RESOURCE_CPU_METRIC_CATEGORIES}
        aggregated_memory = {category: [] for category in paired.RESOURCE_MEMORY_METRIC_CATEGORIES}
        failures: list[dict[str, Any]] = []
        passes_covered: set[int] = set()
        service_app_sample_row_count = 0
        sidecar_sample_row_count = 0
        client_sample_row_count = 0
        for record in records:
            path = Path(record["resource_samples"])
            if not path.exists():
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "resource sample CSV was not created"})
                continue
            cpu_counter_metrics = record.get("cpu_counter_metrics")
            cpu_metrics_for_record: dict[str, float] | None = None
            cpu_metrics_source = "kubectl_top"
            if isinstance(cpu_counter_metrics, dict) and cpu_counter_metrics:
                cpu_metrics_source = "kubelet_summary_delta"
                if not bool(cpu_counter_metrics.get("available")):
                    failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "container CPU counter measurement was incomplete"})
                    continue
                cpu_summary = cpu_counter_metrics.get("summary") or {}
                if any(not isinstance(cpu_summary.get(category), (int, float)) for category in paired.RESOURCE_CPU_METRIC_CATEGORIES):
                    failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "container CPU counter measurement summary was incomplete"})
                    continue
                cpu_metrics_for_record = {category: float(cpu_summary[category]) for category in paired.RESOURCE_CPU_METRIC_CATEGORIES}

            per_timestamp: dict[str, dict[str, float]] = {}
            service_namespace_rows = 0
            sidecar_rows = 0
            observed_sidecar_rows = 0
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    namespace = str(row.get("namespace") or "")
                    if namespace not in {record["service_namespace"], record["client_namespace"]}:
                        continue
                    container_name = str(row.get("container_name") or "")
                    if namespace == record["service_namespace"] and container_name == "istio-proxy":
                        observed_sidecar_rows += 1
                    bucket = per_timestamp.setdefault(str(row.get("timestamp") or "unknown"), paired.empty_resource_metric_sample())
                    cpu = paired.parse_cpu_mcores(str(row.get("cpu_usage") or ""))
                    memory = paired.parse_memory_mib(str(row.get("memory_usage") or ""))
                    if cpu is None or memory is None:
                        continue
                    if namespace == record["client_namespace"]:
                        client_sample_row_count += 1
                        bucket["client_memory_mib"] += memory
                        if cpu_metrics_source == "kubectl_top":
                            bucket["client_cpu_mcores"] += cpu
                    elif container_name == "istio-proxy":
                        service_namespace_rows += 1
                        sidecar_rows += 1
                        sidecar_sample_row_count += 1
                        bucket["sidecar_memory_mib"] += memory
                        if cpu_metrics_source == "kubectl_top":
                            bucket["sidecar_cpu_mcores"] += cpu
                    else:
                        service_namespace_rows += 1
                        service_app_sample_row_count += 1
                        bucket["service_app_memory_mib"] += memory
                        if cpu_metrics_source == "kubectl_top":
                            bucket["service_app_cpu_mcores"] += cpu
            if not per_timestamp or service_namespace_rows == 0:
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "resource sample CSV had no usable condition rows"})
                continue
            if not expected_sidecars and observed_sidecar_rows > 0:
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "plain condition resource sample CSV contained istio-proxy rows"})
                continue
            if expected_sidecars and sidecar_rows == 0:
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "mTLS condition resource sample CSV had zero istio-proxy rows"})
                continue
            passes_covered.add(int(record["pass"]))
            if cpu_metrics_for_record is not None:
                for category, value in cpu_metrics_for_record.items():
                    aggregated_cpu[category].append(value)
            for sample in per_timestamp.values():
                sample["total_pod_memory_mib"] = sample["service_app_memory_mib"] + sample["sidecar_memory_mib"]
                if cpu_metrics_source == "kubectl_top":
                    sample["total_pod_cpu_mcores"] = sample["service_app_cpu_mcores"] + sample["sidecar_cpu_mcores"]
                    for category in paired.RESOURCE_CPU_METRIC_CATEGORIES:
                        aggregated_cpu[category].append(sample[category])
                for category in paired.RESOURCE_MEMORY_METRIC_CATEGORIES:
                    aggregated_memory[category].append(sample[category])
        sample_count = len(aggregated_memory["service_app_memory_mib"])
        cpu_count = len(aggregated_cpu["service_app_cpu_mcores"])
        base = {
            "sample_count": sample_count,
            "cpu_measurement_count": cpu_count,
            "passes_covered": sorted(passes_covered),
            "service_app_sample_row_count": service_app_sample_row_count,
            "sidecar_sample_row_count": sidecar_sample_row_count,
            "client_sample_row_count": client_sample_row_count,
            "sidecar_metrics_available": sidecar_sample_row_count > 0,
        }
        if failures:
            return {"available": False, "reason": "one or more required resource sample artifacts were incomplete", **base, "failures": failures}
        if sample_count == 0 or cpu_count == 0:
            return {"available": False, "reason": "resource metric aggregation produced no usable CPU or memory measurements", **base}
        return {
            "available": True,
            **base,
            **{f"{category}_mean": paired.mean_or_none(values) for category, values in aggregated_cpu.items()},
            **{f"{category}_mean": paired.mean_or_none(values) for category, values in aggregated_memory.items()},
        }

    def summarize_operational_overhead(self) -> dict[str, Any]:
        summaries: dict[str, Any] = {}
        for key in self.condition_keys:
            records = [
                record for record in self.completed_conditions
                if str(record.get("condition_key")) == key and isinstance(record.get("operational_overhead"), dict)
            ]
            if not records:
                summaries[key] = {"available": False, "reason": "no operational-overhead records were captured"}
                continue
            operational_records = [record["operational_overhead"] for record in records]
            summary_metrics = [payload.get("summary") or {} for payload in operational_records]
            deployment_complexity = operational_records[0].get("deployment_complexity") or {}
            operational_complexity = operational_records[0].get("operational_complexity") or {}

            def metric_mean(metric: str) -> float | None:
                return paired.mean_or_none([
                    float(summary[metric])
                    for summary in summary_metrics
                    if isinstance(summary.get(metric), (int, float))
                ])

            summaries[key] = {
                "available": True,
                "passes_covered": sorted({int(record["pass"]) for record in records}),
                "service_schedule_to_ready_seconds_mean": metric_mean("service_schedule_to_ready_seconds_mean"),
                "service_sidecar_started_delay_seconds_mean": metric_mean("service_sidecar_started_delay_seconds_mean"),
                "service_sidecar_requested_cpu_mcores_total": metric_mean("service_sidecar_requested_cpu_mcores_total"),
                "service_sidecar_requested_memory_mib_total": metric_mean("service_sidecar_requested_memory_mib_total"),
                "service_total_requested_cpu_mcores_total": metric_mean("service_total_requested_cpu_mcores_total"),
                "service_total_requested_memory_mib_total": metric_mean("service_total_requested_memory_mib_total"),
                "deployment_complexity": deployment_complexity,
                "operational_complexity": operational_complexity,
                "control_plane_colocation": operational_records[0].get("control_plane_colocation") or {},
            }
        return {"by_condition": summaries, "by_split": self.metric_pair_deltas(summaries)}

    def metric_pair_deltas(self, summaries: dict[str, Any]) -> dict[str, Any]:
        metrics = [
            "service_app_cpu_mcores_mean",
            "sidecar_cpu_mcores_mean",
            "total_pod_cpu_mcores_mean",
            "service_app_memory_mib_mean",
            "sidecar_memory_mib_mean",
            "total_pod_memory_mib_mean",
            "service_schedule_to_ready_seconds_mean",
            "service_sidecar_started_delay_seconds_mean",
            "service_sidecar_requested_cpu_mcores_total",
            "service_sidecar_requested_memory_mib_total",
            "service_total_requested_cpu_mcores_total",
            "service_total_requested_memory_mib_total",
        ]
        result: dict[str, Any] = {}
        for split_key in self.split_keys:
            plain_payload = summaries.get(f"{split_key}_plain") or {}
            mtls_payload = summaries.get(f"{split_key}_mtls") or {}
            row = {
                "split_key": split_key,
                "split_label": SPLIT_SPECS[split_key]["label"],
                "expected_protected_activation_bytes": SPLIT_SPECS[split_key]["protected_activation_bytes"],
            }
            for metric in metrics:
                plain_value = plain_payload.get(metric)
                mtls_value = mtls_payload.get(metric)
                row[f"{metric}_plain"] = plain_value
                row[f"{metric}_mtls"] = mtls_value
                if isinstance(plain_value, (int, float)) and isinstance(mtls_value, (int, float)):
                    row[f"{metric}_delta"] = mtls_value - plain_value

            plain_complexity = plain_payload.get("deployment_complexity") or {}
            mtls_complexity = mtls_payload.get("deployment_complexity") or {}
            plain_kind_counts = plain_complexity.get("kubernetes_object_counts_by_kind") or {}
            mtls_kind_counts = mtls_complexity.get("kubernetes_object_counts_by_kind") or {}

            def kind_delta(kind: str) -> int:
                return int(mtls_kind_counts.get(kind) or 0) - int(plain_kind_counts.get(kind) or 0)

            row["deployment_complexity_delta"] = {
                "additional_kubernetes_object_count": int(mtls_complexity.get("kubernetes_object_count") or 0)
                - int(plain_complexity.get("kubernetes_object_count") or 0),
                "additional_service_account_count": kind_delta("ServiceAccount"),
                "additional_peer_authentication_count": kind_delta("PeerAuthentication"),
                "additional_authorization_policy_count": kind_delta("AuthorizationPolicy"),
                "additional_injected_container_count": int(mtls_complexity.get("total_injected_container_count") or 0)
                - int(plain_complexity.get("total_injected_container_count") or 0),
            }
            result[split_key] = row
        return result

    def summarize_security_validation(self) -> dict[str, Any]:
        by_condition: dict[str, Any] = {}
        failures: list[str] = []
        for key in self.condition_keys:
            records = [record for record in self.completed_conditions if str(record.get("condition_key")) == key]
            runtime_passed = bool(records) and all(bool((record.get("runtime_validation") or {}).get("passed")) for record in records)
            if security_mode_for_condition(key) == "mtls":
                security_passed = bool(records) and all(bool(record.get("security_validation_passed")) for record in records)
            else:
                security_passed = None
            passed = runtime_passed and (security_passed is not False)
            by_condition[key] = {
                "passed": passed,
                "runtime_validation_passed": runtime_passed,
                "security_preflight_passed": security_passed,
                "run_count": len(records),
                "runs": [
                    {
                        "pass": record.get("pass"),
                        "execution_index": record.get("execution_index"),
                        "runtime_validation_passed": bool((record.get("runtime_validation") or {}).get("passed")),
                        "security_validation_passed": record.get("security_validation_passed"),
                        "security_preflight_artifact": record.get("security_preflight_artifact"),
                    }
                    for record in records
                ],
            }
            if not passed:
                failures.append(key)
        return {"passed": not failures, "by_condition": by_condition, "failures": failures}

    def resource_summary_blockers(self, resources: dict[str, Any]) -> list[str]:
        blockers = []
        for key, payload in (resources.get("by_condition") or {}).items():
            if payload.get("available"):
                continue
            blockers.append(f"{key}: {payload.get('reason') or 'resource metrics unavailable'}")
            for failure in payload.get("failures") or []:
                blockers.append(f"{key} pass {failure.get('pass')} exec {failure.get('execution_index')}: {failure.get('reason')}")
        return blockers

    def merge_artifacts(self) -> None:
        rows = self.read_condition_rows()
        if not rows:
            raise PipelineError("No benchmark rows were collected")
        fieldnames = list(rows[0].keys())
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        raw_out = self.merged_dir / "raw_iterations.csv"
        with raw_out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        latency = self.summarize_latency(rows)
        resources = self.summarize_resource_samples()
        operational = self.summarize_operational_overhead()
        validation = self.summarize_security_validation()
        blockers = self.resource_summary_blockers(resources)
        if self.args.disable_resource_sampling:
            blockers.insert(0, "resource sampling was disabled; split sensitivity requires CPU and memory overhead metrics")
        if not validation.get("passed"):
            blockers.append("split-sensitivity runtime/security validation was not completed successfully")
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "smoke": bool(self.args.smoke),
            "topology": "chain2_split_sensitivity",
            "image_ref": self.effective_image_ref,
            "mesh_revision": self.mesh_revision,
            "protected_hop_index": PROTECTED_HOP_INDEX,
            "execution_plan": self.execution_plan,
            "conditions": self.completed_conditions,
            "latency": latency,
            "resources": resources,
            "operational": operational,
            "validation": validation,
            "requirements": {
                "resource_metrics_complete": not self.resource_summary_blockers(resources),
                "validation_complete": bool(validation.get("passed")),
                "blocking_issues": blockers,
            },
            "notes": [
                "Split-sensitivity results are internally comparable within this interleaved campaign.",
                "The protected inter-service activation for chain_2svc is reported as hop_2_activation_bytes.",
                "split_after_layer4 is retained as a low-payload diagnostic endpoint and remains compute-degenerate.",
            ],
        }
        (self.merged_dir / "split_sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (self.merged_dir / "operational_overhead_by_split.json").write_text(
            json.dumps(operational.get("by_split") or {}, indent=2),
            encoding="utf-8",
        )
        self.write_summary_csv(summary)
        self.write_resource_summary_csv(summary)
        self.write_aggregated_results_csv(summary)
        self.write_summary_markdown(summary)
        for key, path in self.effective_config_paths.items():
            shutil.copy2(path, self.merged_dir / f"{key}_effective_config.yaml")
        if blockers:
            raise PipelineError("RQ2.1 mTLS split artifact set is incomplete:\n- " + "\n- ".join(blockers))

    def write_summary_csv(self, summary: dict[str, Any]) -> None:
        out_path = self.merged_dir / "split_sensitivity_summary.csv"
        fieldnames = [
            "split_key",
            "split_label",
            "expected_protected_activation_bytes",
            "compute_degenerate",
            "plain_condition",
            "mtls_condition",
            "plain_mean_ms",
            "mtls_mean_ms",
            "mean_latency_overhead_ms",
            "mean_latency_overhead_pct",
            "p95_latency_overhead_ms",
            "non_compute_overhead_delta_ms",
            "total_compute_delta_ms",
            "protected_hop_activation_bytes_mean_plain",
            "protected_hop_activation_bytes_mean_mtls",
            "protected_hop_forward_ms_mean_plain",
            "protected_hop_forward_ms_mean_mtls",
            "total_activation_bytes_mean_plain",
            "total_activation_bytes_mean_mtls",
        ]
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for split_key in self.split_keys:
                payload = (summary["latency"].get("by_split") or {}).get(split_key) or {}
                writer.writerow({field: payload.get(field) for field in fieldnames})

    def write_resource_summary_csv(self, summary: dict[str, Any]) -> None:
        out_path = self.merged_dir / "resource_summary_by_split.csv"
        fieldnames = [
            "split_key",
            "split_label",
            "expected_protected_activation_bytes",
            "sidecar_cpu_mcores_mean_delta",
            "total_pod_cpu_mcores_mean_delta",
            "sidecar_memory_mib_mean_delta",
            "total_pod_memory_mib_mean_delta",
            "service_schedule_to_ready_seconds_mean_delta",
            "service_sidecar_started_delay_seconds_mean_mtls",
            "additional_kubernetes_object_count",
            "additional_service_account_count",
            "additional_peer_authentication_count",
            "additional_authorization_policy_count",
            "additional_injected_container_count",
        ]
        resources = summary.get("resources") or {}
        operational = summary.get("operational") or {}
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for split_key in self.split_keys:
                resource_row = (resources.get("by_split") or {}).get(split_key) or {}
                operational_row = (operational.get("by_split") or {}).get(split_key) or {}
                deployment_delta = operational_row.get("deployment_complexity_delta") or {}
                row = {
                    "split_key": split_key,
                    "split_label": SPLIT_SPECS[split_key]["label"],
                    "expected_protected_activation_bytes": SPLIT_SPECS[split_key]["protected_activation_bytes"],
                    "sidecar_cpu_mcores_mean_delta": resource_row.get("sidecar_cpu_mcores_mean_delta"),
                    "total_pod_cpu_mcores_mean_delta": resource_row.get("total_pod_cpu_mcores_mean_delta"),
                    "sidecar_memory_mib_mean_delta": resource_row.get("sidecar_memory_mib_mean_delta"),
                    "total_pod_memory_mib_mean_delta": resource_row.get("total_pod_memory_mib_mean_delta"),
                    "service_schedule_to_ready_seconds_mean_delta": operational_row.get("service_schedule_to_ready_seconds_mean_delta"),
                    "service_sidecar_started_delay_seconds_mean_mtls": operational_row.get("service_sidecar_started_delay_seconds_mean_mtls"),
                    **deployment_delta,
                }
                writer.writerow({field: row.get(field) for field in fieldnames})

    def write_aggregated_results_csv(self, summary: dict[str, Any]) -> None:
        out_path = self.merged_dir / "aggregated_results.csv"
        fieldnames = [
            "row_type",
            "condition_key",
            "split_key",
            "security_mode",
            "condition",
            "n",
            "mean_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
            "non_compute_overhead_ms_mean",
            "total_compute_ms_mean",
            "total_activation_bytes_mean",
            "protected_hop_activation_bytes_mean",
            "protected_hop_forward_ms_mean",
            "mean_latency_overhead_ms",
            "mean_latency_overhead_pct",
            "p95_latency_overhead_ms",
            "non_compute_overhead_delta_ms",
            "total_compute_delta_ms",
        ]
        latency = summary.get("latency") or {}
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for key in self.condition_keys:
                payload = (latency.get("by_condition") or {}).get(key) or {}
                row = {
                    "row_type": "condition",
                    "condition_key": key,
                    "split_key": split_key_for_condition(key),
                    "security_mode": security_mode_for_condition(key),
                }
                row.update(payload)
                writer.writerow({field: row.get(field) for field in fieldnames})
            for split_key in self.split_keys:
                payload = (latency.get("by_split") or {}).get(split_key) or {}
                row = {
                    "row_type": "split_pair_delta",
                    "split_key": split_key,
                    "condition": payload.get("split_label"),
                }
                row.update(payload)
                writer.writerow({field: row.get(field) for field in fieldnames})

    def write_summary_markdown(self, summary: dict[str, Any]) -> None:
        lines = [
            "# RQ2.1 mTLS Split Sensitivity Summary",
            "",
            f"- Smoke mode: `{summary['smoke']}`",
            f"- Image: `{summary['image_ref']}`",
            f"- Mesh revision: `{summary['mesh_revision']}`",
            f"- Protected hop index: `{summary['protected_hop_index']}`",
            f"- Execution order: `{summary['execution_plan']['passes']}`",
            "",
            "## Split Deltas",
            "",
            "| Split | Protected bytes | Plain mean ms | mTLS mean ms | Delta ms | Delta % | p95 delta ms |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for split_key in self.split_keys:
            payload = (summary["latency"].get("by_split") or {}).get(split_key) or {}
            lines.append(
                f"| {payload.get('split_label')} | {payload.get('expected_protected_activation_bytes')} | "
                f"{payload.get('plain_mean_ms')} | {payload.get('mtls_mean_ms')} | "
                f"{payload.get('mean_latency_overhead_ms')} | {payload.get('mean_latency_overhead_pct')} | "
                f"{payload.get('p95_latency_overhead_ms')} |"
            )
        lines.extend(["", "## Notes", ""])
        for note in summary.get("notes") or []:
            lines.append(f"- {note}")
        blockers = summary.get("requirements", {}).get("blocking_issues") or []
        if blockers:
            lines.extend(["", "## Blocking Issues", ""])
            lines.extend(f"- {blocker}" for blocker in blockers)
        lines.append("")
        (self.merged_dir / "split_sensitivity_summary.md").write_text("\n".join(lines), encoding="utf-8")

    def write_run_metadata(self, *, completed: bool) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "completed": completed,
            "smoke": bool(self.args.smoke),
            "artifact_dir": str(self.artifact_dir),
            "configs": {key: str(path) for key, path in self.source_paths.items()},
            "effective_configs": {key: str(path) for key, path in self.effective_config_paths.items()},
            "image_ref": self.effective_image_ref,
            "mesh_revision": self.mesh_revision,
            "nodepool": self.args.nodepool,
            "isolated_node_pools": bool(self.args.isolated_node_pools),
            "resource_group": self.args.resource_group,
            "cluster_name": self.args.cluster_name,
            "execution_plan": self.execution_plan,
            "completed_conditions": self.completed_conditions,
        }
        self.run_metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def pod_benchmark_root(self) -> str:
        return "/tmp/rq21_mtls_split"

    def run(self) -> None:
        self.validate_configs()
        log("RQ2.1 mTLS split sensitivity scope: four split points, each plain vs mTLS/AuthZ.")
        self.prepare_artifact_dirs()
        self.verify_required_files()
        self.verify_host_prerequisites()
        self.prepare_infrastructure()
        self.write_effective_configs()
        if self.args.generate_only:
            for key in self.condition_keys:
                context = self.condition_context(key, 0, 0)
                self.generate_manifests(context)
            self.write_run_metadata(completed=True)
            log(f"Generate-only mTLS split artifacts: {self.artifact_dir}")
            return
        self.verify_cluster_reachable()
        execution_index = 0
        for pass_record in self.execution_plan["passes"]:
            pass_index = int(pass_record["pass"])
            for key in pass_record["order"]:
                execution_index += 1
                log(f"Starting split sensitivity pass {pass_index}, execution {execution_index}: {self.condition_names[key]}")
                self.run_condition_once(key, pass_index, execution_index)
        self.merge_artifacts()
        self.write_run_metadata(completed=True)
        if self.args.destroy_infrastructure_on_success:
            self.destroy_infrastructure("successful mTLS split benchmark")
            self.write_run_metadata(completed=True)
        log(f"RQ2.1 mTLS split sensitivity artifacts: {self.artifact_dir}")

    def handle_failure(self, exc: Exception) -> None:
        if self.current_context and self.resources_deployed and self.args.cleanup_on_failure:
            try:
                self.cleanup_namespaces(self.current_context)
            except Exception as cleanup_exc:
                warn(f"Failed to clean up namespaces after split sensitivity failure: {cleanup_exc}")
        elif self.current_context and self.resources_deployed:
            warn(
                f"Preserving namespaces {self.current_context.service_namespace} and "
                f"{self.current_context.client_namespace} for inspection."
            )
        if self.args.destroy_infrastructure_on_failure:
            try:
                self.destroy_infrastructure("failed mTLS split benchmark")
            except Exception as destroy_exc:
                warn(f"Failed to destroy infrastructure after mTLS split benchmark failure: {destroy_exc}")
        try:
            self.write_run_metadata(completed=False)
        except Exception:
            pass
        warn(f"RQ2.1 mTLS split benchmark failed. Artifacts directory: {self.artifact_dir}")
        print(f"[{paired.timestamp()}] ERROR: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    runner = RQ21MtlsSplitRunner(args)
    try:
        runner.run()
    except Exception as exc:
        runner.handle_failure(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
