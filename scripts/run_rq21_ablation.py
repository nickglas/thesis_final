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
import time
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


CONDITION_CONFIGS = {
    "c0": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_plain_nonmesh.yaml",
    "c1": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_default_no_authz.yaml",
    "c2": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_strict_mtls_no_authz.yaml",
    "c3": "configs/rq2/2.1/ablation/rq2_1_ablation_chain2_mesh_strict_mtls_authz.yaml",
}
CONDITION_KEYS = ("c0", "c1", "c2", "c3")
ADJACENT_DELTAS = (
    ("c1_minus_c0", "c1", "c0", "mesh-default sidecar/auto-mTLS cost"),
    ("c2_minus_c1", "c2", "c1", "strict mTLS enforcement cost"),
    ("c3_minus_c2", "c3", "c2", "AuthorizationPolicy cost"),
    ("c3_minus_c0", "c3", "c0", "total hardened-path cost"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "RQ2.1 four-condition ablation runner for chain_2svc. "
            "Compares plain non-mesh, mesh-default/no-AuthZ, strict-mTLS/no-AuthZ, "
            "and strict-mTLS/AuthZ conditions inside one interleaved campaign."
        )
    )
    for key, default in CONDITION_CONFIGS.items():
        parser.add_argument(f"--{key}-config", default=default)
    parser.add_argument("--results-root", default=str(REPO_ROOT / "results_exports"))
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD)
    parser.add_argument("--nodepool", default=DEFAULT_NODEPOOL)
    parser.add_argument("--provision", action="store_true")
    parser.add_argument("--provisioner", choices=["terraform"], default="terraform")
    parser.add_argument("--acr-name", default=None)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--image-ref", default=None)
    parser.add_argument("--image-tag", default=f"rq21-ablation-{utc_run_stamp().lower()}")
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
    parser.add_argument("--ablation-passes", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=42)
    parser.add_argument(
        "--order",
        choices=["seeded", "fixed", "reverse"],
        default="seeded",
        help="Condition order mode for pass 1; later passes rotate the order.",
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
    if args.ablation_passes < 1:
        parser.error("--ablation-passes must be at least 1")
    if args.resource_sample_interval_seconds < 0:
        parser.error("--resource-sample-interval-seconds must be non-negative")
    return args


class RQ21AblationRunner(paired.RQ21PairedBenchmarkRunner):
    condition_keys = CONDITION_KEYS

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
        self.artifact_dir = Path(args.results_root).resolve() / f"rq2_1_ablation_{self.run_stamp}"
        self.config_dir = self.artifact_dir / "effective_configs"
        self.conditions_root = self.artifact_dir / "conditions"
        self.merged_dir = self.artifact_dir / "merged"
        self.static_dir = self.artifact_dir / "static_validation"
        self.run_metadata_path = self.artifact_dir / "rq21_ablation_run_metadata.json"

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

    def _build_execution_plan(self) -> dict[str, Any]:
        if self.args.order == "reverse":
            first_order = list(reversed(self.condition_keys))
        else:
            first_order = list(self.condition_keys)
            if self.args.order == "seeded":
                random.Random(self.args.order_seed).shuffle(first_order)
        passes = []
        for pass_index in range(1, self.args.ablation_passes + 1):
            offset = (pass_index - 1) % len(first_order)
            order = first_order[offset:] + first_order[:offset]
            passes.append({"pass": pass_index, "order": order})
        return {
            "order_mode": self.args.order,
            "order_seed": self.args.order_seed,
            "ablation_passes": self.args.ablation_passes,
            "passes": passes,
            "condition_keys": list(self.condition_keys),
            "adjacent_deltas": [
                {"name": name, "to": high, "from": low, "label": label}
                for name, high, low, label in ADJACENT_DELTAS
            ],
        }

    def active_hop_indexes(self) -> list[int]:
        return [1, 2]

    def expected_downstream_segments(self, service_count: int | None = None) -> list[str]:
        return ["2"]

    def _helper_args(
        self,
        *,
        config_path: Path,
        results_root: Path,
        manifest_output_dir: Path | None = None,
        preserve_existing: bool = True,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            config=str(config_path),
            results_root=str(results_root),
            nodepool=self.args.nodepool,
            client_pod=self.args.client_pod,
            provision=self.args.provision,
            provisioner=self.args.provisioner,
            acr_name=self.acr_name,
            image_ref=self.args.image_ref,
            push=self.args.push,
            build=self.args.build,
            image_tag=self.args.image_tag,
            local_image=self.args.local_image,
            no_auto_push_missing_image=self.args.no_auto_push_missing_image,
            resource_group=self.args.resource_group,
            cluster_name=self.args.cluster_name,
            location=self.args.location,
            node_count=self.args.node_count,
            node_vm_size=self.args.node_vm_size,
            isolated_node_pools=self.args.isolated_node_pools,
            system_nodepool=self.args.system_nodepool,
            system_node_count=self.args.system_node_count,
            system_node_vm_size=self.args.system_node_vm_size,
            benchmark_taint=self.args.benchmark_taint,
            skip_mesh_enable=self.args.skip_mesh_enable,
            mesh_revision=self.args.mesh_revision,
            manifest_output_dir=str(manifest_output_dir) if manifest_output_dir else None,
            generate_only=False,
            preserve_existing=preserve_existing,
            cleanup_on_success=False,
            cleanup_on_failure=False,
            readiness_timeout=self.args.readiness_timeout,
            smoke_benchmark=False,
        )

    def lifecycle_helper(self) -> RQ21PreflightRunner:
        if self.lifecycle_runner is None:
            lifecycle_root = self.artifact_dir / "lifecycle"
            lifecycle_manifest_dir = lifecycle_root / "manifests"
            self.lifecycle_runner = RQ21PreflightRunner(
                self._helper_args(
                    config_path=self.source_paths["c3"],
                    results_root=lifecycle_root,
                    manifest_output_dir=lifecycle_manifest_dir,
                    preserve_existing=True,
                )
            )
            self.lifecycle_runner.prepare_artifact_dirs()
        return self.lifecycle_runner

    def _configured_image_ref(self) -> str:
        return str((self.raw_configs["c3"].get("kubernetes") or {}).get("image") or "").strip()

    def _configured_mesh_revision(self) -> str:
        return str(
            self.args.mesh_revision
            or ((self.raw_configs["c3"].get("kubernetes") or {}).get("mesh") or {}).get("revision")
            or ""
        ).strip()

    def validate_configs(self) -> None:
        errors: list[str] = []
        expected_names = {
            "c0": "chain_2svc_plain_nonmesh",
            "c1": "chain_2svc_mesh_default_no_authz",
            "c2": "chain_2svc_mesh_strict_mtls_no_authz",
            "c3": "chain_2svc_mesh_strict_mtls_authz",
        }
        for key, expected_name in expected_names.items():
            if self.condition_names.get(key) != expected_name:
                errors.append(f"{key} config must contain condition {expected_name}")
            condition = paired.first_condition(self.raw_configs[key])
            if paired.service_count_for_condition(condition) != 2:
                errors.append(f"{key} must be chain_2svc")
            if list(condition.get("chain_split_points") or []) != ["layer2"]:
                errors.append(f"{key} must split after layer2")

        for section in ("model", "benchmark", "grpc", "cpu_stabilisation", "carry_forward", "parity", "warmup_calibration"):
            values = [self.raw_configs[key].get(section) for key in self.condition_keys]
            if any(value != values[0] for value in values[1:]):
                errors.append(f"All ablation configs must match section '{section}'")

        images = {
            str((self.raw_configs[key].get("kubernetes") or {}).get("image") or "")
            for key in self.condition_keys
        }
        if len(images) != 1:
            errors.append(f"All ablation configs must use the same image reference; found {sorted(images)}")
        revisions = {
            str((((self.raw_configs[key].get("kubernetes") or {}).get("mesh") or {}).get("revision") or ""))
            for key in ("c1", "c2", "c3")
        }
        if len(revisions) != 1:
            errors.append(f"Mesh conditions must use the same mesh revision; found {sorted(revisions)}")

        mesh_enabled = {
            key: bool((((self.raw_configs[key].get("kubernetes") or {}).get("mesh") or {}).get("enabled", False)))
            for key in self.condition_keys
        }
        if mesh_enabled["c0"]:
            errors.append("c0 must not enable mesh")
        for key in ("c1", "c2", "c3"):
            if not mesh_enabled[key]:
                errors.append(f"{key} must enable mesh")

        def mesh(key: str) -> dict[str, Any]:
            payload = ((self.raw_configs[key].get("kubernetes") or {}).get("mesh") or {})
            return payload if isinstance(payload, dict) else {}

        c1_mesh = mesh("c1")
        if bool((c1_mesh.get("peer_authentication") or {}).get("enabled", False)):
            errors.append("c1 must not enable PeerAuthentication")
        if bool((c1_mesh.get("authorization_policy") or {}).get("enabled", False)):
            errors.append("c1 must not enable AuthorizationPolicy")

        for key in ("c2", "c3"):
            peer = mesh(key).get("peer_authentication") or {}
            strict = peer.get("strict_workloads") or []
            strict_segments = {
                str(item.get("segment_index"))
                for item in strict
                if isinstance(item, dict) and str(item.get("mode") or "STRICT").upper() == "STRICT"
            }
            if not bool(peer.get("enabled", False)) or strict_segments != {"2"}:
                errors.append(f"{key} must enable only service2 STRICT PeerAuthentication")

        if bool((mesh("c2").get("authorization_policy") or {}).get("enabled", False)):
            errors.append("c2 must not enable AuthorizationPolicy")
        c3_authz = mesh("c3").get("authorization_policy") or {}
        if not bool(c3_authz.get("enabled", False)):
            errors.append("c3 must enable AuthorizationPolicy")
        if str(c3_authz.get("source_segment_index") or "") != "1" or str(c3_authz.get("downstream_segment_index") or "") != "2":
            errors.append("c3 AuthorizationPolicy must be service1 -> service2")

        if errors:
            raise PipelineError("RQ2.1 ablation config validation failed:\n- " + "\n- ".join(errors))

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

    def prepare_infrastructure(self) -> None:
        lifecycle: RQ21PreflightRunner | None = None
        revision = self._configured_mesh_revision()
        if self.args.provision or self.args.push or self.args.build or revision.lower() in {"auto", "latest", "supported"}:
            lifecycle = self.lifecycle_helper()

        if self.args.provision:
            lifecycle = self.lifecycle_helper()
            lifecycle.maybe_provision_cluster()
            self.args.resource_group = lifecycle.args.resource_group
            self.args.cluster_name = lifecycle.args.cluster_name
            self.args.node_vm_size = lifecycle.args.node_vm_size
            self.acr_name = lifecycle.acr_name
            self.infrastructure_provisioned = True

        if self.args.image_ref:
            self.effective_image_ref = self.args.image_ref
            image_resolution = {"reason": "explicit --image-ref", "pinned_ref": self.effective_image_ref}
        elif self.args.provision or self.args.push or self.args.build:
            lifecycle = self.lifecycle_helper()
            self.effective_image_ref = lifecycle.resolve_image_reference()
            image_resolution_path = lifecycle.state.artifact_dir / "image_resolution.json"
            if image_resolution_path.exists():
                image_resolution = json.loads(image_resolution_path.read_text(encoding="utf-8"))
            else:
                image_resolution = {"reason": "lifecycle image resolution", "pinned_ref": self.effective_image_ref}
        else:
            self.effective_image_ref = self._configured_image_ref()
            image_resolution = {"reason": "existing pinned image", "pinned_ref": self.effective_image_ref}

        if "@sha256:" not in self.effective_image_ref:
            raise PipelineError("RQ2.1 ablation runner requires a pinned digest image reference")
        if not revision:
            raise PipelineError("RQ2.1 ablation mesh configs must pin kubernetes.mesh.revision")

        if lifecycle is not None:
            lifecycle.prepare_effective_config(resolve_live_revision=True, image_ref=self.effective_image_ref)
            self.mesh_revision = str(lifecycle.mesh.get("revision") or lifecycle.args.mesh_revision or revision)
            lifecycle.ensure_managed_istio()
        else:
            self.mesh_revision = revision

        (self.artifact_dir / "image_reference.txt").write_text(self.effective_image_ref + "\n", encoding="utf-8")
        image_resolution.update({"ablation_artifact_dir": str(self.artifact_dir), "pinned_ref": self.effective_image_ref})
        (self.artifact_dir / "image_resolution.json").write_text(json.dumps(image_resolution, indent=2), encoding="utf-8")
        (self.artifact_dir / "infrastructure_lifecycle.json").write_text(
            json.dumps(
                {
                    "provision_requested": bool(self.args.provision),
                    "provisioned": self.infrastructure_provisioned,
                    "destroy_on_success": bool(self.args.destroy_infrastructure_on_success),
                    "destroy_on_failure": bool(self.args.destroy_infrastructure_on_failure),
                    "resource_group": self.args.resource_group,
                    "cluster_name": self.args.cluster_name,
                    "acr_name": self.acr_name,
                    "nodepool": self.args.nodepool,
                    "node_count": self.args.node_count,
                    "node_vm_size": self.args.node_vm_size,
                    "isolated_node_pools": bool(self.args.isolated_node_pools),
                    "system_nodepool": self.args.system_nodepool,
                    "system_node_count": self.args.system_node_count,
                    "system_node_vm_size": self.args.system_node_vm_size,
                    "benchmark_taint": self.args.benchmark_taint,
                    "mesh_revision": self.mesh_revision,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

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
        service_accounts = mesh.get("service_accounts") or {}
        authz = mesh.get("authorization_policy") or {}
        if not isinstance(authz, dict) or not bool(authz.get("enabled", False)):
            return []
        raw_policies = authz.get("policies")
        policies = raw_policies if isinstance(raw_policies, list) and raw_policies else [authz]
        expected: list[dict[str, str]] = []
        for policy in policies:
            source_segment = str(policy.get("source_segment_index") or "1")
            downstream_segment = str(policy.get("downstream_segment_index") or "2")
            source_service_account = str(service_accounts.get(source_segment) or "")
            expected.append({
                "name": str(policy.get("name") or f"service{downstream_segment}-service{source_segment}-only"),
                "source_segment_index": source_segment,
                "downstream_segment_index": downstream_segment,
                "expected_principal": f"cluster.local/ns/{context.service_namespace}/sa/{source_service_account}",
            })
        return expected

    def expected_policy_shape(self, key: str) -> dict[str, Any]:
        return {
            "c0": {"mesh": False, "service_accounts": 0, "peer": 0, "strict": 0, "authz": 0},
            "c1": {"mesh": True, "service_accounts": 2, "peer": 0, "strict": 0, "authz": 0},
            "c2": {"mesh": True, "service_accounts": 2, "peer": 2, "strict": 1, "authz": 0},
            "c3": {"mesh": True, "service_accounts": 2, "peer": 2, "strict": 1, "authz": 1},
        }[key]

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
                errors.append("c0 namespaces must not carry mesh revision labels")

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
        if context.key in {"c2", "c3"}:
            peer_errors, peer_summary = self.validate_mtls_peer_authentications(context, peer_items)
            errors.extend(peer_errors)
        if context.key == "c3":
            authz_errors, authz_summary = self.validate_mtls_authorization_policies(context, authz_items)
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
                errors.append(f"c0 deployment has sidecar annotations {sorted(sidecar_keys)}")

        summary = {
            "condition": context.condition_name,
            "condition_key": context.key,
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
                    "security-condition": str(k8s.get("security_condition") or context.key),
                },
                "annotations": {"sidecar.istio.io/inject": "false"},
            },
            "spec": spec,
        }

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
            "    hops = [{'hop_index': h.hop_index, 'deserialize_ms': h.deserialize_ms, 'compute_ms': h.compute_ms, 'serialize_ms': h.serialize_ms, 'forward_ms': h.forward_ms, 'activation_bytes': h.activation_bytes} for h in response.hop_timings]\n"
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

    def run_direct_probe(self, context: paired.ConditionContext, *, expected_blocked: bool) -> dict[str, Any]:
        pod_name_value = "rq21-ab-direct-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
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

    def validate_ablation_runtime(self, context: paired.ConditionContext) -> dict[str, Any]:
        expected = self.expected_policy_shape(context.key)
        errors: list[str] = []
        service_pods = self.service_pods(context)
        client_pod = self.client_pod(context)
        namespace = kubectl_json(["get", "namespace", context.service_namespace, "-o", "json"])
        client_namespace = kubectl_json(["get", "namespace", context.client_namespace, "-o", "json"])
        service_labels = (namespace.get("metadata") or {}).get("labels") or {}
        client_labels = (client_namespace.get("metadata") or {}).get("labels") or {}
        if expected["mesh"] and service_labels.get("istio.io/rev") != self.mesh_revision:
            errors.append(f"{context.key} service namespace missing istio.io/rev={self.mesh_revision}")
        if not expected["mesh"] and (service_labels.get("istio.io/rev") or service_labels.get("istio-injection") == "enabled"):
            errors.append("c0 service namespace has mesh injection label")
        if client_labels.get("istio.io/rev") or client_labels.get("istio-injection") == "enabled":
            errors.append(f"{context.key} client namespace must remain non-mesh")

        peer_items = list((kubectl_json_or_none([
            "get", "peerauthentication.security.istio.io", "-n", context.service_namespace, "-o", "json",
        ]) or {}).get("items") or [])
        authz_items = list((kubectl_json_or_none([
            "get", "authorizationpolicy.security.istio.io", "-n", context.service_namespace, "-o", "json",
        ]) or {}).get("items") or [])
        strict_items = [
            item for item in peer_items
            if str(((item.get("spec") or {}).get("mtls") or {}).get("mode") or "").upper() == "STRICT"
        ]
        if len(peer_items) != expected["peer"]:
            errors.append(f"{context.key} expected {expected['peer']} PeerAuthentications; found {len(peer_items)}")
        if len(strict_items) != expected["strict"]:
            errors.append(f"{context.key} expected {expected['strict']} STRICT PeerAuthentications; found {len(strict_items)}")
        if len(authz_items) != expected["authz"]:
            errors.append(f"{context.key} expected {expected['authz']} AuthorizationPolicies; found {len(authz_items)}")
        peer_summary: dict[str, Any] = {}
        authz_summary: dict[str, Any] = {}
        if context.key in {"c2", "c3"}:
            peer_errors, peer_summary = self.validate_mtls_peer_authentications(context, peer_items)
            errors.extend(peer_errors)
        if context.key == "c3":
            authz_errors, authz_summary = self.validate_mtls_authorization_policies(context, authz_items)
            errors.extend(authz_errors)

        nodes = set()
        for pod in service_pods:
            name = paired.pod_name(pod)
            nodes.add(str((pod.get("spec") or {}).get("nodeName") or "unknown"))
            names = [str(container.get("name")) for container in paired.container_specs(pod)]
            app_names = [str(container.get("name")) for container in paired.app_container_specs(pod)]
            service_account = str((pod.get("spec") or {}).get("serviceAccountName") or "default")
            if expected["mesh"]:
                if "istio-proxy" not in names:
                    errors.append(f"{name}: meshed service pod missing istio-proxy")
                if service_account == "default":
                    errors.append(f"{name}: meshed service pod must use explicit ServiceAccount")
            elif "istio-proxy" in names:
                errors.append(f"{name}: c0 service pod contains istio-proxy")
            if "inference" not in app_names or not paired.container_ready(pod, "inference"):
                errors.append(f"{name}: inference app container is not Ready")
            errors.extend(paired.bad_pod_states(pod))
        nodes.discard("unknown")
        if len(nodes) != 1:
            errors.append(f"{context.key} service pods are not strictly colocated on one node: {sorted(nodes)}")

        client_node = str((client_pod.get("spec") or {}).get("nodeName") or "unknown")
        if len(nodes) == 1 and client_node not in nodes:
            errors.append(f"{context.key} benchmark client is not colocated with service pods")
        client_names = [str(container.get("name")) for container in paired.container_specs(client_pod)]
        client_app_names = [str(container.get("name")) for container in paired.app_container_specs(client_pod)]
        if client_app_names != ["client"]:
            errors.append(f"{context.key} benchmark client must have one app container named client")
        if "istio-proxy" in client_names:
            errors.append(f"{context.key} benchmark client contains istio-proxy")
        errors.extend(paired.bad_pod_states(client_pod))

        full_chain_probe = self.run_full_chain_probe(context)
        if not full_chain_probe.get("succeeded"):
            errors.append(f"{context.key} full-chain positive probe failed")
        direct_probe = self.run_direct_probe(context, expected_blocked=context.key in {"c2", "c3"})
        if not direct_probe.get("passed"):
            expected_text = "blocked" if context.key in {"c2", "c3"} else "ready"
            errors.append(f"{context.key} direct service2 probe did not produce expected {expected_text} result")

        result = {
            "condition": context.condition_name,
            "condition_key": context.key,
            "passed": not errors,
            "errors": errors,
            "service_pod_nodes": sorted(nodes),
            "client_node": client_node,
            "expected_shape": expected,
            "peer_authentication_validation": peer_summary,
            "authorization_policy_validation": authz_summary,
            "full_chain_probe": full_chain_probe,
            "direct_service2_probe": direct_probe,
        }
        path = context.diagnostics_dir / "ablation_runtime_validation.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if errors:
            raise PipelineError(f"Ablation runtime validation failed for {context.condition_name}:\n- " + "\n- ".join(errors))
        return result

    def run_condition_once(self, key: str, pass_index: int, execution_index: int) -> None:
        context = self.condition_context(key, pass_index, execution_index)
        self.current_context = context
        context.condition_dir.mkdir(parents=True, exist_ok=True)
        context.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        static_summary = self.generate_manifests(context)
        try:
            self.apply_manifests(context)
            self.wait_for_ready(context)
            validation_artifact = self.validate_ablation_runtime(context)
            operational_overhead = self.capture_operational_overhead(context)
            cpu_counter_metrics = self.run_condition_benchmark(context, pass_index)
            self.gather_diagnostics(context)
            self.completed_conditions.append({
                "pass": pass_index,
                "execution_index": execution_index,
                "condition_key": key,
                "condition": context.condition_name,
                "condition_dir": str(context.condition_dir),
                "benchmark_dir": str(context.benchmark_dir),
                "resource_samples": str(context.resource_samples_path),
                "static_manifest_validation": static_summary,
                "runtime_validation": validation_artifact,
                "runtime_validation_passed": bool(validation_artifact.get("passed")),
                "operational_overhead": operational_overhead,
                "cpu_counter_metrics": cpu_counter_metrics,
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
                "n": len(latencies),
                "mean_ms": paired.mean_or_none(latencies),
                "median_ms": paired.percentile(latencies, 50) if latencies else None,
                "p95_ms": paired.percentile(latencies, 95) if latencies else None,
                "p99_ms": paired.percentile(latencies, 99) if latencies else None,
                "non_compute_overhead_ms_mean": paired.mean_or_none(non_compute),
                "total_compute_ms_mean": paired.mean_or_none(total_compute),
            }
            for metric in ["total_activation_bytes", "hop_1_activation_bytes", "hop_2_activation_bytes", "hop_1_forward_ms", "hop_2_forward_ms"]:
                values = [v for v in (paired.maybe_float(row.get(metric)) for row in key_rows) if v is not None]
                payload[f"{metric}_mean"] = paired.mean_or_none(values)
            summaries[key] = payload
        return {"by_condition": summaries, "adjacent_deltas": self.adjacent_deltas(summaries)}

    def adjacent_deltas(self, summaries: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, high, low, label in ADJACENT_DELTAS:
            high_payload = summaries.get(high) or {}
            low_payload = summaries.get(low) or {}
            high_mean = high_payload.get("mean_ms")
            low_mean = low_payload.get("mean_ms")
            high_p95 = high_payload.get("p95_ms")
            low_p95 = low_payload.get("p95_ms")
            delta = high_mean - low_mean if isinstance(high_mean, (int, float)) and isinstance(low_mean, (int, float)) else None
            result[name] = {
                "label": label,
                "from": low,
                "to": high,
                "mean_latency_delta_ms": delta,
                "mean_latency_delta_pct": ((delta / low_mean) * 100.0) if isinstance(delta, (int, float)) and isinstance(low_mean, (int, float)) and low_mean > 0 else None,
                "p95_latency_delta_ms": high_p95 - low_p95 if isinstance(high_p95, (int, float)) and isinstance(low_p95, (int, float)) else None,
            }
        return result

    def summarize_resource_samples(self) -> dict[str, Any]:
        summaries = {
            key: self._resource_summary_for_key(key)
            for key in self.condition_keys
        }
        return {"by_condition": summaries, "adjacent_deltas": self._metric_adjacent_deltas(summaries)}

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
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "non-mesh condition resource sample CSV contained istio-proxy rows"})
                continue
            if expected_sidecars and sidecar_rows == 0:
                failures.append({"pass": int(record["pass"]), "execution_index": int(record["execution_index"]), "reason": "mesh condition resource sample CSV had zero istio-proxy rows"})
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
        return {"by_condition": summaries, "adjacent_deltas": self._metric_adjacent_deltas(summaries)}

    def _metric_adjacent_deltas(self, summaries: dict[str, Any]) -> dict[str, Any]:
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
        ]
        result: dict[str, Any] = {}
        for name, high, low, label in ADJACENT_DELTAS:
            row = {"label": label, "from": low, "to": high}
            high_payload = summaries.get(high) or {}
            low_payload = summaries.get(low) or {}
            for metric in metrics:
                high_value = high_payload.get(metric)
                low_value = low_payload.get(metric)
                if isinstance(high_value, (int, float)) and isinstance(low_value, (int, float)):
                    row[f"{metric}_delta"] = high_value - low_value
            result[name] = row
        return result

    def summarize_validation(self) -> dict[str, Any]:
        by_condition = {}
        failures = []
        for key in self.condition_keys:
            records = [record for record in self.completed_conditions if str(record.get("condition_key")) == key]
            passed = bool(records) and all(bool((record.get("runtime_validation") or {}).get("passed")) for record in records)
            by_condition[key] = {
                "passed": passed,
                "run_count": len(records),
                "conditions": [
                    {
                        "pass": record.get("pass"),
                        "execution_index": record.get("execution_index"),
                        "full_chain_probe_passed": bool(((record.get("runtime_validation") or {}).get("full_chain_probe") or {}).get("succeeded")),
                        "direct_probe_passed": bool(((record.get("runtime_validation") or {}).get("direct_service2_probe") or {}).get("passed")),
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
        validation = self.summarize_validation()
        blockers = self.resource_summary_blockers(resources)
        if self.args.disable_resource_sampling:
            blockers.insert(0, "resource sampling was disabled; ablation requires CPU and memory overhead metrics")
        if not validation.get("passed"):
            blockers.append("condition-specific ablation validation was not completed successfully")
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "smoke": bool(self.args.smoke),
            "topology": "chain2",
            "image_ref": self.effective_image_ref,
            "mesh_revision": self.mesh_revision,
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
                "Ablation results are internally comparable within this interleaved campaign.",
                "Do not numerically splice these deltas into the frozen two-condition RQ2.1 result.",
                "C1 is mesh-default sidecar/auto-mTLS/no-AuthZ, not a proven plaintext sidecar-only condition.",
            ],
        }
        (self.merged_dir / "rq2_1_ablation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        self.write_summary_csv(summary)
        self.write_summary_markdown(summary)
        for key, path in self.effective_config_paths.items():
            shutil.copy2(path, self.merged_dir / f"{key}_effective_config.yaml")
        if blockers:
            raise PipelineError("RQ2.1 ablation artifact set is incomplete:\n- " + "\n- ".join(blockers))

    def write_summary_csv(self, summary: dict[str, Any]) -> None:
        out_path = self.merged_dir / "rq2_1_ablation_summary.csv"
        fieldnames = [
            "condition_key", "condition", "n", "mean_ms", "median_ms", "p95_ms", "p99_ms",
            "non_compute_overhead_ms_mean", "total_compute_ms_mean",
            "service_app_cpu_mcores_mean", "sidecar_cpu_mcores_mean", "total_pod_cpu_mcores_mean",
            "service_app_memory_mib_mean", "sidecar_memory_mib_mean", "total_pod_memory_mib_mean",
            "service_schedule_to_ready_seconds_mean", "service_sidecar_started_delay_seconds_mean",
            "deployment_kubernetes_object_count", "deployment_service_account_count",
            "deployment_peer_authentication_count", "deployment_authorization_policy_count",
            "deployment_injected_container_count", "validation_passed",
        ]
        latency = summary["latency"]["by_condition"]
        resources = summary["resources"]["by_condition"]
        operational = summary["operational"]["by_condition"]
        validation = summary["validation"]["by_condition"]
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for key in self.condition_keys:
                row = {"condition_key": key}
                row.update(latency.get(key) or {})
                row.update(resources.get(key) or {})
                op = operational.get(key) or {}
                row.update(op)
                complexity = op.get("deployment_complexity") or {}
                kind_counts = complexity.get("kubernetes_object_counts_by_kind") or {}
                row["deployment_kubernetes_object_count"] = complexity.get("kubernetes_object_count")
                row["deployment_service_account_count"] = kind_counts.get("ServiceAccount")
                row["deployment_peer_authentication_count"] = kind_counts.get("PeerAuthentication")
                row["deployment_authorization_policy_count"] = kind_counts.get("AuthorizationPolicy")
                row["deployment_injected_container_count"] = complexity.get("total_injected_container_count")
                row["validation_passed"] = (validation.get(key) or {}).get("passed")
                writer.writerow({field: row.get(field) for field in fieldnames})

    def write_summary_markdown(self, summary: dict[str, Any]) -> None:
        lines = [
            "# RQ2.1 Ablation Summary",
            "",
            f"- Smoke mode: `{summary['smoke']}`",
            f"- Image: `{summary['image_ref']}`",
            f"- Mesh revision: `{summary['mesh_revision']}`",
            f"- Execution order: `{summary['execution_plan']['passes']}`",
            "",
            "## Latency By Condition",
            "",
            "| Condition | Mean ms | p95 ms | Non-compute mean ms |",
            "| --- | ---: | ---: | ---: |",
        ]
        for key in self.condition_keys:
            payload = summary["latency"]["by_condition"].get(key) or {}
            lines.append(
                f"| {key} | {payload.get('mean_ms')} | {payload.get('p95_ms')} | "
                f"{payload.get('non_compute_overhead_ms_mean')} |"
            )
        lines.extend(["", "## Adjacent Deltas", "", "| Delta | Mean ms | Mean % | p95 ms |", "| --- | ---: | ---: | ---: |"])
        for name, payload in (summary["latency"].get("adjacent_deltas") or {}).items():
            lines.append(
                f"| {name} | {payload.get('mean_latency_delta_ms')} | "
                f"{payload.get('mean_latency_delta_pct')} | {payload.get('p95_latency_delta_ms')} |"
            )
        lines.extend(["", "## Notes", ""])
        for note in summary.get("notes") or []:
            lines.append(f"- {note}")
        blockers = summary.get("requirements", {}).get("blocking_issues") or []
        if blockers:
            lines.extend(["", "## Blocking Issues", ""])
            lines.extend(f"- {blocker}" for blocker in blockers)
        lines.append("")
        (self.merged_dir / "rq2_1_ablation_summary.md").write_text("\n".join(lines), encoding="utf-8")

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
        return "/tmp/rq21_ablation"

    def run(self) -> None:
        self.validate_configs()
        log("RQ2.1 ablation scope: C0 plain, C1 mesh-default/no-AuthZ, C2 strict-mTLS/no-AuthZ, C3 strict-mTLS/AuthZ.")
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
            log(f"Generate-only ablation artifacts: {self.artifact_dir}")
            return
        self.verify_cluster_reachable()
        execution_index = 0
        for pass_record in self.execution_plan["passes"]:
            pass_index = int(pass_record["pass"])
            for key in pass_record["order"]:
                execution_index += 1
                log(f"Starting ablation pass {pass_index}, execution {execution_index}: {self.condition_names[key]}")
                self.run_condition_once(key, pass_index, execution_index)
        self.merge_artifacts()
        self.write_run_metadata(completed=True)
        if self.args.destroy_infrastructure_on_success:
            self.destroy_infrastructure("successful ablation benchmark")
            self.write_run_metadata(completed=True)
        log(f"RQ2.1 ablation artifacts: {self.artifact_dir}")

    def handle_failure(self, exc: Exception) -> None:
        if self.current_context and self.resources_deployed and self.args.cleanup_on_failure:
            try:
                self.cleanup_namespaces(self.current_context)
            except Exception as cleanup_exc:
                warn(f"Failed to clean up namespaces after ablation failure: {cleanup_exc}")
        elif self.current_context and self.resources_deployed:
            warn(
                f"Preserving namespaces {self.current_context.service_namespace} and "
                f"{self.current_context.client_namespace} for inspection."
            )
        if self.args.destroy_infrastructure_on_failure:
            try:
                self.destroy_infrastructure("failed ablation benchmark")
            except Exception as destroy_exc:
                warn(f"Failed to destroy infrastructure after ablation benchmark failure: {destroy_exc}")
        try:
            self.write_run_metadata(completed=False)
        except Exception:
            pass
        warn(f"RQ2.1 ablation benchmark failed. Artifacts directory: {self.artifact_dir}")
        print(f"[{paired.timestamp()}] ERROR: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    runner = RQ21AblationRunner(args)
    try:
        runner.run()
    except Exception as exc:
        runner.handle_failure(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
