from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.benchmark.config import format_k8s_service_name

DEFAULT_CONFIG_REL = "configs/rq2/2.1/rq2_1_chain2_mtls.yaml"
DEFAULT_CLIENT_POD = "benchmark-client"
DEFAULT_NODEPOOL = "rq15pool"
DEFAULT_RESOURCE_GROUP = "rg-thesis-rq15"
DEFAULT_CLUSTER_NAME = "thesis-rq15"
DEFAULT_LOCATION = "swedencentral"
DEFAULT_NODE_VM_SIZE = "Standard_D8s_v3"
DEFAULT_NODE_COUNT = 1
DEFAULT_SYSTEM_NODEPOOL = "systempool"
DEFAULT_SYSTEM_NODE_VM_SIZE = "Standard_D2s_v3"
DEFAULT_SYSTEM_NODE_COUNT = 1
DEFAULT_BENCHMARK_NODE_TAINT = "workload=benchmark:NoSchedule"
INFRA_DIR = REPO_ROOT / "infra"
MULTI_NODE_PLACEMENT_STRATEGY = "multi_node_anti_affinity"
STRICT_SAME_NODE_PLACEMENT_STRATEGY = "strict_same_node"
SUPPORTED_TOPOLOGIES = {
    2: {
        "name": "chain_2svc",
        "split_points": ["layer2"],
        "framing": "primary one-boundary RQ2.1 preflight",
    },
    5: {
        "name": "chain_5svc",
        "split_points": ["layer1", "layer2", "layer3", "layer4"],
        "framing": "optional maximum-depth RQ2.1 stress preflight",
    },
}


class PipelineError(RuntimeError):
    pass


@dataclass
class RunnerState:
    artifact_dir: Path
    diagnostics_dir: Path
    manifest_dir: Path
    metadata_path: Path
    effective_config_path: Path
    resources_deployed: bool = False


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def log(message: str) -> None:
    print(f"[{timestamp()}] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[{timestamp()}] WARN: {message}", file=sys.stderr, flush=True)


WINDOWS_COMMAND_CANDIDATES = {
    "az": [r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"],
    "docker": [r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"],
    "kubectl": [r"C:\Program Files\Docker\Docker\resources\bin\kubectl.exe"],
}


def resolve_command_path(command_name: str) -> str | None:
    resolved = shutil.which(command_name)
    if resolved:
        return resolved
    if os.name == "nt":
        for candidate in WINDOWS_COMMAND_CANDIDATES.get(command_name, []):
            if os.path.exists(candidate):
                return candidate
    return None


def prepare_command_args(args: list[str]) -> list[str]:
    if not args:
        return args
    resolved = resolve_command_path(args[0])
    if not resolved:
        return args
    if resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", resolved, *args[1:]]
    return [resolved, *args[1:]]


def ensure_command(command_name: str) -> None:
    if resolve_command_path(command_name) is None:
        raise PipelineError(f"Required command not found: {command_name}")


def _running_under_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def wsl_windows_kubeconfig_pair() -> tuple[Path, str] | None:
    az_path = shutil.which("az") or ""
    if not (_running_under_wsl() and az_path.startswith("/mnt/")):
        return None
    try:
        windows_home = subprocess.check_output(
            ["cmd.exe", "/c", "echo", "%USERPROFILE%"],
            text=True,
        ).strip()
        if not windows_home or "%USERPROFILE%" in windows_home:
            return None
        windows_kubeconfig = str(PureWindowsPath(windows_home) / ".kube" / "config")
        wsl_kubeconfig = subprocess.check_output(
            ["wslpath", "-u", windows_kubeconfig],
            text=True,
        ).strip()
        if not wsl_kubeconfig:
            return None
        return Path(wsl_kubeconfig), windows_kubeconfig
    except Exception:
        warn(
            "Failed to resolve the Windows kubeconfig path from WSL; "
            "falling back to the Linux home directory."
        )
        return None


def default_kubeconfig_path() -> Path:
    kubeconfig_env = os.environ.get("KUBECONFIG")
    if kubeconfig_env:
        first_entry = kubeconfig_env.split(os.pathsep)[0].strip()
        if first_entry:
            return Path(first_entry).expanduser()
    shared_wsl_pair = wsl_windows_kubeconfig_pair()
    if shared_wsl_pair is not None:
        return shared_wsl_pair[0]
    return Path.home() / ".kube" / "config"


def az_cli_kubeconfig_path(kubeconfig_path: Path) -> str:
    shared_wsl_pair = wsl_windows_kubeconfig_pair()
    if shared_wsl_pair is not None and kubeconfig_path == shared_wsl_pair[0]:
        return shared_wsl_pair[1]

    az_path = shutil.which("az") or ""
    if _running_under_wsl() and az_path.startswith("/mnt/"):
        try:
            converted = subprocess.check_output(
                ["wslpath", "-w", str(kubeconfig_path)],
                text=True,
            ).strip()
            if not converted.startswith("\\\\wsl.localhost\\"):
                return converted
            warn(
                "The requested kubeconfig path resolves to a WSL UNC path that Windows az may not be able to write; "
                "falling back to the Linux path."
            )
        except Exception:
            warn(
                "Failed to convert kubeconfig path for Windows az CLI under WSL; "
                "falling back to the Linux path."
            )
    return str(kubeconfig_path)


def run_command(
    args: list[str],
    *,
    cwd: Path | None = REPO_ROOT,
    capture_output: bool = False,
    check: bool = True,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess:
    resolved_args = prepare_command_args(args)
    try:
        result = subprocess.run(
            resolved_args,
            cwd=str(cwd) if cwd else None,
            capture_output=capture_output,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        result = subprocess.CompletedProcess(
            resolved_args,
            124,
            stdout,
            stderr or f"Timed out after {timeout_seconds}s",
        )
        if check:
            raise PipelineError(
                f"Command timed out after {timeout_seconds}s: {' '.join(args)}"
            )
        return result
    if check and result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise PipelineError(f"Command failed: {' '.join(args)}\n{detail}")
    return result


def kubectl_text(args: list[str], *, check: bool = True) -> str:
    result = run_command(["kubectl", *args], capture_output=True, check=check)
    return (result.stdout or "").strip()


def kubectl_json(args: list[str], *, check: bool = True) -> dict:
    text = kubectl_text(args, check=check)
    if not text:
        return {}
    return json.loads(text)


def kubectl_json_or_none(args: list[str]) -> dict | None:
    try:
        return kubectl_json(args)
    except Exception:
        return None


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise PipelineError(f"Config did not parse as a YAML object: {path}")
    return payload


def parse_node_taint(taint: str) -> dict[str, str]:
    text = str(taint or "").strip()
    if not text:
        return {}
    body, _, effect = text.partition(":")
    key, sep, value = body.partition("=")
    if not key or not sep or not effect:
        return {}
    return {"key": key, "value": value, "effect": effect}


def toleration_matches_taint(toleration: dict[str, Any], taint: str) -> bool:
    parsed = parse_node_taint(taint)
    if not parsed:
        return False
    if str(toleration.get("key") or "") != parsed["key"]:
        return False
    effect = str(toleration.get("effect") or "")
    if effect and effect != parsed["effect"]:
        return False
    operator = str(toleration.get("operator") or "Equal")
    if operator == "Exists":
        return True
    return str(toleration.get("value") or "") == parsed["value"]


def placement_tolerations(placement: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in (placement.get("tolerations") or [])
        if isinstance(item, dict)
    ]


def placement_requires_control_plane_isolation(placement: dict[str, Any]) -> bool:
    return bool(placement.get("require_control_plane_isolation", False))


def placement_strategy(placement: dict[str, Any] | None) -> str:
    if not isinstance(placement, dict):
        return "none"
    return str(placement.get("strategy") or "none")


def placement_is_multi_node(placement: dict[str, Any] | None) -> bool:
    return placement_strategy(placement) == MULTI_NODE_PLACEMENT_STRATEGY


def placement_min_nodes(placement: dict[str, Any] | None) -> int | None:
    if not isinstance(placement, dict):
        return None
    raw = placement.get("min_nodes")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def minimum_benchmark_nodes_for_placement(
    placement: dict[str, Any] | None,
    service_count: int,
) -> int:
    if placement_is_multi_node(placement):
        dedicated_client = bool(
            (placement or {}).get("require_dedicated_client_node", False)
        )
        return int(service_count) + (1 if dedicated_client else 0)
    return 1


def is_avoidable_istio_control_plane_pod(record: dict[str, Any]) -> bool:
    namespace = str(record.get("namespace") or "")
    if namespace not in {"aks-istio-system", "istio-system"}:
        return False
    owner_kinds = {
        str(item.get("kind") or "")
        for item in (record.get("owner_references") or [])
        if isinstance(item, dict)
    }
    if "DaemonSet" in owner_kinds:
        return False
    labels = record.get("labels") or {}
    label_blob = " ".join(f"{key}={value}" for key, value in labels.items()).lower()
    identity_blob = f"{namespace} {record.get('pod_name') or ''} {label_blob}".lower()
    return "istio" in identity_blob or "asm" in identity_blob or "pilot" in identity_blob


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 1/2 RQ2.1 runner: generate and optionally apply the managed-Istio "
            "chain_2svc_mtls or optional chain_5svc_mtls manifests, then run a fail-closed mTLS/service-identity preflight. "
            "This does not run the paired plain-vs-mTLS benchmark."
        )
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_REL,
        help="RQ2.1 mTLS preflight config YAML; plain baseline configs are generated separately.",
    )
    parser.add_argument(
        "--results-root",
        default=str(REPO_ROOT / "results"),
        help="Parent directory for preflight artifacts",
    )
    parser.add_argument("--nodepool", default=DEFAULT_NODEPOOL, help="AKS nodepool label for manifest generation")
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD, help="Benchmark client pod name")
    parser.add_argument(
        "--provision",
        action="store_true",
        help="Create or reuse the Terraform-managed RQ1.5 AKS/ACR foundation and refresh kubeconfig before RQ2.1 preflight.",
    )
    parser.add_argument(
        "--provisioner",
        choices=["terraform"],
        default="terraform",
        help="Provisioning backend used when --provision is enabled.",
    )
    parser.add_argument(
        "--acr-name",
        default=None,
        help="ACR name without .azurecr.io. Derived from kubernetes.image when omitted.",
    )
    parser.add_argument(
        "--image-ref",
        default=None,
        help="Existing pinned image reference to inject, e.g. <acr>.azurecr.io/thesis-inference@sha256:<digest>.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push a fresh thesis-inference image to ACR and use the resolved pinned digest for this preflight.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the Docker image before pushing. Only valid with --push.",
    )
    parser.add_argument(
        "--image-tag",
        default=f"rq21-{utc_run_stamp().lower()}",
        help="ACR tag to use when --push is set or when --provision auto-pushes a missing image.",
    )
    parser.add_argument(
        "--local-image",
        default="thesis-inference:latest",
        help="Local Docker image to tag and push.",
    )
    parser.add_argument(
        "--no-auto-push-missing-image",
        action="store_true",
        help=(
            "When --provision is enabled and the configured pinned digest is missing from ACR, "
            "fail early instead of building and pushing a fresh image automatically."
        ),
    )
    parser.add_argument("--resource-group", default=DEFAULT_RESOURCE_GROUP, help="Azure resource group name")
    parser.add_argument("--cluster-name", default=DEFAULT_CLUSTER_NAME, help="AKS cluster name")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help="Azure region for provisioning")
    parser.add_argument("--node-count", type=int, default=DEFAULT_NODE_COUNT, help="Node count for Terraform provisioning")
    parser.add_argument(
        "--node-vm-size",
        default=DEFAULT_NODE_VM_SIZE,
        help="VM SKU used when provisioning the AKS cluster",
    )
    parser.set_defaults(isolated_node_pools=True)
    parser.add_argument(
        "--isolated-node-pools",
        dest="isolated_node_pools",
        action="store_true",
        help="Use the final RQ2.1 two-pool AKS contract. Enabled by default for this RQ2.1 runner.",
    )
    parser.add_argument(
        "--single-node-pool",
        dest="isolated_node_pools",
        action="store_false",
        help="Use the legacy single-pool AKS contract. Not for final thesis-facing RQ2.1 runs.",
    )
    parser.add_argument(
        "--system-nodepool",
        default=DEFAULT_SYSTEM_NODEPOOL,
        help="System node pool name when --isolated-node-pools is active.",
    )
    parser.add_argument(
        "--system-node-count",
        type=int,
        default=DEFAULT_SYSTEM_NODE_COUNT,
        help="System node count when --isolated-node-pools is active.",
    )
    parser.add_argument(
        "--system-node-vm-size",
        default=DEFAULT_SYSTEM_NODE_VM_SIZE,
        help="System node VM SKU when --isolated-node-pools is active.",
    )
    parser.add_argument(
        "--benchmark-taint",
        default=DEFAULT_BENCHMARK_NODE_TAINT,
        help="Benchmark node-pool taint that RQ2.1 benchmark pods must tolerate.",
    )
    parser.add_argument(
        "--skip-mesh-enable",
        action="store_true",
        help="Do not call az aks mesh enable; only validate whatever managed Istio revision is already present.",
    )
    parser.add_argument(
        "--mesh-revision",
        default=None,
        help=(
            "Override kubernetes.mesh.revision. Use 'auto' to choose the latest "
            "available AKS managed-Istio revision for --location."
        ),
    )
    parser.add_argument(
        "--manifest-output-dir",
        default=None,
        help="Override generated manifest directory. Defaults to the run artifact directory.",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Render manifests and validate the config shape without applying anything.",
    )
    parser.add_argument(
        "--preserve-existing",
        action="store_true",
        help="Do not delete existing RQ2.1 namespaces before applying manifests.",
    )
    parser.add_argument(
        "--cleanup-on-success",
        action="store_true",
        help="Delete the RQ2.1 namespaces after a successful preflight.",
    )
    parser.add_argument(
        "--cleanup-on-failure",
        action="store_true",
        help="Delete the RQ2.1 namespaces after diagnostics are collected for a failed preflight.",
    )
    parser.add_argument(
        "--readiness-timeout",
        type=int,
        default=None,
        help="Override readiness timeout in seconds.",
    )
    parser.add_argument(
        "--smoke-benchmark",
        action="store_true",
        help="After the mTLS preflight, run the tiny selected-condition benchmark profile inside the client pod.",
    )
    args = parser.parse_args()
    if args.build and not args.push:
        parser.error("--build requires --push")
    if args.image_ref and (args.push or args.build):
        parser.error("--image-ref cannot be combined with --push/--build")
    return args


class RQ21PreflightRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))
        self.repo_root = REPO_ROOT
        self.infra_dir = INFRA_DIR
        self.source_config_path = (self.repo_root / args.config).resolve()
        self.raw_config = load_yaml(self.source_config_path)
        self.k8s = self._k8s_section()
        self.mesh = self._mesh_section()
        self.condition = self._single_condition()
        self.condition_name = str(self.condition["name"])
        self.service_namespace = str(self.k8s["namespace"])
        self.client_namespace = str(self.k8s.get("client_namespace") or self.service_namespace)
        self.service_count = len(self.condition.get("chain_split_points") or []) + 1
        self.readiness_timeout = int(
            args.readiness_timeout
            or float(self.k8s.get("readiness_timeout", 120.0))
        )

        run_ts = utc_run_stamp()
        artifact_dir = Path(args.results_root).resolve() / f"rq2_1_preflight_{run_ts}"
        manifest_dir = (
            Path(args.manifest_output_dir).resolve()
            if args.manifest_output_dir
            else artifact_dir / "manifests"
        )
        self.state = RunnerState(
            artifact_dir=artifact_dir,
            diagnostics_dir=artifact_dir / "diagnostics",
            manifest_dir=manifest_dir,
            metadata_path=artifact_dir / "rq21_preflight_metadata.json",
            effective_config_path=artifact_dir / "effective_config.yaml",
        )
        self.metadata: dict[str, Any] = {}
        self.cluster_reachable = False
        self.acr_name = args.acr_name or self._derive_acr_name_from_config()
        self.terraform_outputs: dict[str, Any] = {}
        self.effective_image_ref = ""
        self._existing_acr_resource_group: str | None = None
        self._resource_group_exists: bool | None = None

    def _k8s_section(self) -> dict[str, Any]:
        k8s = self.raw_config.get("kubernetes") or {}
        if not isinstance(k8s, dict):
            raise PipelineError("Config must include a kubernetes mapping")
        return k8s

    def _mesh_section(self) -> dict[str, Any]:
        mesh = self.k8s.get("mesh") or {}
        if not isinstance(mesh, dict):
            raise PipelineError("kubernetes.mesh must be a mapping")
        return mesh

    def _single_condition(self) -> dict[str, Any]:
        conditions = self.raw_config.get("conditions") or []
        if len(conditions) != 1 or not isinstance(conditions[0], dict):
            raise PipelineError("RQ2.1 Stage 1/2 configs must contain exactly one condition")
        return conditions[0]

    def _derive_acr_name_from_config(self) -> str | None:
        image = str(getattr(self.args, "image_ref", None) or self.k8s.get("image", "")).strip()
        match = re.match(r"^([a-zA-Z0-9]+)\.azurecr\.io/", image)
        return match.group(1) if match else None

    def _active_config_path(self) -> Path:
        if self.state.effective_config_path.exists():
            return self.state.effective_config_path
        return self.source_config_path

    def _expected_downstream_segments(self) -> list[str]:
        return [str(index) for index in range(2, self.service_count + 1)]

    def _authorization_policy_configs(self) -> list[dict[str, str]]:
        authz = self.mesh.get("authorization_policy") or {}
        if not isinstance(authz, dict) or not bool(authz.get("enabled", False)):
            return []
        raw_policies = authz.get("policies")
        policies: list[dict[str, str]] = []
        if isinstance(raw_policies, list) and raw_policies:
            for item in raw_policies:
                if not isinstance(item, dict):
                    continue
                source_segment = str(item.get("source_segment_index") or "").strip()
                downstream_segment = str(item.get("downstream_segment_index") or "").strip()
                if not source_segment or not downstream_segment:
                    continue
                policies.append({
                    "name": str(
                        item.get("name")
                        or f"service{downstream_segment}-service{source_segment}-only"
                    ),
                    "source_segment_index": source_segment,
                    "downstream_segment_index": downstream_segment,
                })
            return policies
        source_segment = str(authz.get("source_segment_index") or "1")
        downstream_segment = str(authz.get("downstream_segment_index") or "2")
        return [
            {
                "name": str(authz.get("name") or "downstream-service1-only"),
                "source_segment_index": source_segment,
                "downstream_segment_index": downstream_segment,
            }
        ]

    def _expected_authorization_policies(self) -> list[dict[str, str]]:
        accounts = self.mesh.get("service_accounts") or {}
        expected: list[dict[str, str]] = []
        for policy in self._authorization_policy_configs():
            source_segment = str(policy["source_segment_index"])
            source_service_account = str(accounts.get(source_segment) or "")
            expected.append({
                **policy,
                "expected_principal": f"cluster.local/ns/{self.service_namespace}/sa/{source_service_account}",
            })
        return expected

    def validate_config(self) -> None:
        errors: list[str] = []
        if self.condition.get("type") != "chain":
            errors.append("RQ2.1 Stage 1/2 condition must be type=chain")
        topology_spec = SUPPORTED_TOPOLOGIES.get(self.service_count)
        placement = self.k8s.get("placement") or {}
        strategy = placement_strategy(placement)
        is_multinode = placement_is_multi_node(placement)
        if topology_spec is None:
            errors.append(
                f"RQ2.1 Stage 1/2 supports only chain_2svc and optional chain_5svc; found {self.service_count} services"
            )
        else:
            suffix = "_multinode" if is_multinode else ""
            expected_name = f"{topology_spec['name']}_mtls{suffix}"
            if self.condition_name != expected_name:
                errors.append(f"This preflight runner expected condition {expected_name}")
            split_points = list(self.condition.get("chain_split_points") or [])
            if split_points != list(topology_spec["split_points"]):
                errors.append(
                    f"{expected_name} must use chain_split_points={topology_spec['split_points']}; found {split_points}"
                )
        if strategy not in {STRICT_SAME_NODE_PLACEMENT_STRATEGY, MULTI_NODE_PLACEMENT_STRATEGY}:
            errors.append(
                "RQ2.1 preflight supports only strict same-node placement or "
                f"{MULTI_NODE_PLACEMENT_STRATEGY}; found {strategy}"
            )
        if is_multinode and self.service_count != 2:
            errors.append("RQ2.1b multi-node preflight is scoped to chain_2svc only")
        if not bool(self.mesh.get("enabled", False)):
            errors.append("kubernetes.mesh.enabled must be true for the mTLS preflight")
        if str(self.mesh.get("implementation") or "") != "managed AKS Istio add-on":
            errors.append("kubernetes.mesh.implementation must be 'managed AKS Istio add-on'")
        configured_revision = str(self.args.mesh_revision or self.mesh.get("revision") or "").strip()
        if not configured_revision:
            errors.append("kubernetes.mesh.revision must be set")
        if str(self.mesh.get("namespace") or self.service_namespace) != self.service_namespace:
            errors.append("kubernetes.mesh.namespace must match kubernetes.namespace")
        if self.client_namespace == self.service_namespace:
            errors.append("kubernetes.client_namespace must keep the benchmark client outside the mesh namespace")

        configured_node_pool = str(placement.get("node_pool") or "").strip()
        if configured_node_pool and configured_node_pool != str(self.args.nodepool):
            errors.append(
                f"kubernetes.placement.node_pool must match --nodepool ({self.args.nodepool}), found {configured_node_pool}"
            )
        if bool(getattr(self.args, "isolated_node_pools", False)):
            expected_node_count = minimum_benchmark_nodes_for_placement(
                placement,
                self.service_count,
            )
            if int(getattr(self.args, "node_count", DEFAULT_NODE_COUNT)) != expected_node_count:
                errors.append(
                    "Final RQ2.1 isolated-pool runs must use benchmark "
                    f"node_count={expected_node_count} for placement strategy {strategy}"
                )
            if int(getattr(self.args, "system_node_count", DEFAULT_SYSTEM_NODE_COUNT)) != 1:
                errors.append("Final RQ2.1 isolated-pool runs must use system_node_count=1")
            if str(getattr(self.args, "node_vm_size", DEFAULT_NODE_VM_SIZE)) != DEFAULT_NODE_VM_SIZE:
                errors.append(f"Final RQ2.1 isolated-pool runs must use benchmark node VM {DEFAULT_NODE_VM_SIZE}")
            if str(getattr(self.args, "system_node_vm_size", DEFAULT_SYSTEM_NODE_VM_SIZE)) != DEFAULT_SYSTEM_NODE_VM_SIZE:
                errors.append(f"Final RQ2.1 isolated-pool runs must use system node VM {DEFAULT_SYSTEM_NODE_VM_SIZE}")
            if not placement_requires_control_plane_isolation(placement):
                errors.append(
                    "Final RQ2.1 isolated-pool runs must set "
                    "kubernetes.placement.require_control_plane_isolation=true"
                )
            if not any(
                toleration_matches_taint(
                    item,
                    getattr(self.args, "benchmark_taint", DEFAULT_BENCHMARK_NODE_TAINT),
                )
                for item in placement_tolerations(placement)
            ):
                errors.append(
                    "Final RQ2.1 isolated-pool runs must include a benchmark-pool toleration "
                    f"matching {getattr(self.args, 'benchmark_taint', DEFAULT_BENCHMARK_NODE_TAINT)}"
                )
            explicit_selector = placement.get("node_selector") or {}
            if str(explicit_selector.get("workload") or "") != "benchmark":
                errors.append(
                    "Final RQ2.1 isolated-pool runs must set "
                    "kubernetes.placement.node_selector.workload=benchmark"
                )
            if is_multinode:
                required_min_nodes = minimum_benchmark_nodes_for_placement(
                    placement,
                    self.service_count,
                )
                if placement_min_nodes(placement) != required_min_nodes:
                    errors.append(
                        "RQ2.1b multi-node placement must set "
                        f"kubernetes.placement.min_nodes={required_min_nodes}"
                    )
                if not bool(placement.get("require_distinct_nodes", False)):
                    errors.append(
                        "RQ2.1b multi-node placement must set "
                        "kubernetes.placement.require_distinct_nodes=true"
                    )
                if not bool(placement.get("require_dedicated_client_node", False)):
                    errors.append(
                        "RQ2.1b multi-node placement must set "
                        "kubernetes.placement.require_dedicated_client_node=true"
                    )
                if bool(placement.get("require_same_node", False)) or bool(
                    placement.get("fail_if_not_colocated", False)
                ):
                    errors.append(
                        "RQ2.1b multi-node placement must not request same-node colocation"
                    )
            else:
                if not bool(placement.get("require_same_node", False)):
                    errors.append(
                        "Primary RQ2.1 placement must set "
                        "kubernetes.placement.require_same_node=true"
                    )
                if not bool(placement.get("fail_if_not_colocated", False)):
                    errors.append(
                        "Primary RQ2.1 placement must set "
                        "kubernetes.placement.fail_if_not_colocated=true"
                    )

        service_accounts = self.mesh.get("service_accounts") or {}
        for index in [str(value) for value in range(1, self.service_count + 1)]:
            if not str(service_accounts.get(index) or "").strip():
                errors.append(f"kubernetes.mesh.service_accounts.{index} must be set")

        proxy_resources = self.mesh.get("proxy_resources") or {}
        for key in ("cpu_request", "cpu_limit", "memory_request", "memory_limit"):
            if not str(proxy_resources.get(key) or "").strip():
                errors.append(f"kubernetes.mesh.proxy_resources.{key} must be set")

        peer = self.mesh.get("peer_authentication") or {}
        if not bool(peer.get("enabled", False)):
            errors.append("kubernetes.mesh.peer_authentication.enabled must be true")
        if str(peer.get("namespace_mode") or "") != "PERMISSIVE":
            errors.append("kubernetes.mesh.peer_authentication.namespace_mode must be PERMISSIVE")
        strict_segments = {
            str(item.get("segment_index"))
            for item in peer.get("strict_workloads") or []
            if isinstance(item, dict)
        }
        expected_strict_segments = set(self._expected_downstream_segments())
        if strict_segments != expected_strict_segments:
            errors.append(
                "kubernetes.mesh.peer_authentication.strict_workloads must target only downstream segment indexes "
                f"{sorted(expected_strict_segments)}"
            )

        authorization_policy = self.mesh.get("authorization_policy") or {}
        if not bool(authorization_policy.get("enabled", False)):
            errors.append("kubernetes.mesh.authorization_policy.enabled must be true")
        policies = self._authorization_policy_configs()
        expected_pairs = {
            (str(index - 1), str(index))
            for index in range(2, self.service_count + 1)
        }
        observed_pairs = {
            (
                str(policy.get("source_segment_index")),
                str(policy.get("downstream_segment_index")),
            )
            for policy in policies
        }
        if observed_pairs != expected_pairs:
            errors.append(
                "kubernetes.mesh.authorization_policy must contain exactly immediate upstream->downstream pairs "
                f"{sorted(expected_pairs)}; found {sorted(observed_pairs)}"
            )
        for policy in policies:
            if not str(policy.get("name") or "").strip():
                errors.append("kubernetes.mesh.authorization_policy policy names must be set")

        if errors:
            raise PipelineError("RQ2.1 config validation failed:\n- " + "\n- ".join(errors))

    def prepare_artifact_dirs(self) -> None:
        self.state.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self.state.manifest_dir.mkdir(parents=True, exist_ok=True)

    def verify_required_files(self) -> None:
        required_paths = [
            self.source_config_path,
            self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py",
        ]
        if self.args.provision:
            required_paths.extend([
                self.infra_dir / "main.tf",
                self.infra_dir / "variables.tf",
                self.infra_dir / "outputs.tf",
            ])
        for path in required_paths:
            if not path.exists():
                raise PipelineError(f"Required file is missing: {path}")

    def verify_host_prerequisites(self) -> None:
        if not self.args.generate_only:
            ensure_command("kubectl")
            ensure_command("az")
        if self.args.push:
            ensure_command("docker")
            ensure_command("az")
        if self.args.mesh_revision and self.args.mesh_revision.lower() == "auto":
            ensure_command("az")
        if self.args.provision:
            ensure_command("terraform")
            ensure_command("az")

    def _requested_vm_profile(self, vm_size: str) -> tuple[int, str]:
        result = run_command(
            [
                "az", "vm", "list-skus",
                "-l", self.args.location,
                "--size", vm_size,
                "-o", "json",
            ],
            capture_output=True,
        )
        payload = json.loads(result.stdout or "[]")
        if not payload:
            raise PipelineError(
                f"Azure SKU metadata lookup returned no records for {vm_size} in {self.args.location}"
            )

        sku = next(
            (item for item in payload if str(item.get("name")) == vm_size),
            payload[0],
        )
        family = str(sku.get("family") or "")
        capabilities = {entry.get("name"): entry.get("value") for entry in sku.get("capabilities", [])}
        vcpus_text = str(capabilities.get("vCPUs") or capabilities.get("vCPUsAvailable") or "")
        if not vcpus_text.isdigit():
            raise PipelineError(
                f"Unable to determine vCPU count for {vm_size} from Azure SKU metadata"
            )
        return int(vcpus_text), family

    def azure_quota_preflight(self) -> None:
        requested_profiles = [
            {
                "role": "benchmark",
                "vm_size": self.args.node_vm_size,
                "count": self.args.node_count,
            }
        ]
        if bool(getattr(self.args, "isolated_node_pools", False)):
            requested_profiles.append(
                {
                    "role": "system",
                    "vm_size": getattr(self.args, "system_node_vm_size", DEFAULT_SYSTEM_NODE_VM_SIZE),
                    "count": getattr(self.args, "system_node_count", DEFAULT_SYSTEM_NODE_COUNT),
                }
            )

        requested_total_vcpus = 0
        requested_family_vcpus: dict[str, int] = {}
        requested_description_parts = []
        for profile in requested_profiles:
            vm_size = str(profile["vm_size"])
            count = int(profile["count"])
            vm_vcpus, family = self._requested_vm_profile(vm_size)
            profile_total = vm_vcpus * count
            requested_total_vcpus += profile_total
            if family:
                requested_family_vcpus[family] = requested_family_vcpus.get(family, 0) + profile_total
            requested_description_parts.append(f"{vm_size} x{count} ({profile['role']})")
        requested_description = ", ".join(requested_description_parts)

        usage_result = run_command(
            ["az", "vm", "list-usage", "-l", self.args.location, "-o", "json"],
            capture_output=True,
        )
        usage_payload = json.loads(usage_result.stdout or "[]")

        regional_record = next(
            (item for item in usage_payload if str(item.get("name", {}).get("value")) == "cores"),
            None,
        )
        if regional_record is None:
            raise PipelineError(
                f"Could not find the regional vCPU quota record for {self.args.location}"
            )

        regional_limit = int(regional_record.get("limit") or 0)
        regional_current = int(regional_record.get("currentValue") or 0)
        regional_available = regional_limit - regional_current
        if regional_available < requested_total_vcpus:
            raise PipelineError(
                "Azure quota preflight failed before provisioning. "
                f"Location {self.args.location} has only {regional_available} regional vCPUs available, "
                f"but {requested_description} requires {requested_total_vcpus}."
            )

        for requested_family, family_requested_vcpus in sorted(requested_family_vcpus.items()):
            family_record = next(
                (
                    item for item in usage_payload
                    if str(item.get("name", {}).get("value", "")).lower() == requested_family.lower()
                ),
                None,
            )
            if family_record is not None:
                family_limit = int(family_record.get("limit") or 0)
                family_current = int(family_record.get("currentValue") or 0)
                family_available = family_limit - family_current
                if family_available < family_requested_vcpus:
                    raise PipelineError(
                        "Azure family quota preflight failed before provisioning. "
                        f"Family {requested_family} in {self.args.location} has only {family_available} vCPUs available, "
                        f"but {requested_description} requires {family_requested_vcpus} in that family."
                    )

    def _terraform_var_args(self) -> list[str]:
        if not self.acr_name:
            raise PipelineError("ACR name is required for Terraform provisioning")
        args = [
            f"-var=resource_group_name={self.args.resource_group}",
            f"-var=location={self.args.location}",
            f"-var=acr_name={self.acr_name}",
            f"-var=cluster_name={self.args.cluster_name}",
            f"-var=nodepool_name={self.args.nodepool}",
            f"-var=node_count={self.args.node_count}",
            f"-var=node_vm_size={self.args.node_vm_size}",
            f"-var=enable_benchmark_pool={str(bool(getattr(self.args, 'isolated_node_pools', False))).lower()}",
            f"-var=system_nodepool_name={getattr(self.args, 'system_nodepool', DEFAULT_SYSTEM_NODEPOOL)}",
            f"-var=system_node_count={getattr(self.args, 'system_node_count', DEFAULT_SYSTEM_NODE_COUNT)}",
            f"-var=system_node_vm_size={getattr(self.args, 'system_node_vm_size', DEFAULT_SYSTEM_NODE_VM_SIZE)}",
            f"-var=benchmark_node_taint={getattr(self.args, 'benchmark_taint', DEFAULT_BENCHMARK_NODE_TAINT)}",
        ]
        if not self._terraform_creates_resource_group():
            args.append("-var=create_resource_group=false")
        if self._terraform_uses_existing_acr():
            args.extend(
                [
                    "-var=create_acr=false",
                    f"-var=acr_resource_group_name={self._existing_acr_group()}",
                ]
            )
        return args

    def _terraform_output_value(self, name: str) -> Any:
        payload = self.terraform_outputs.get(name)
        if not isinstance(payload, dict) or "value" not in payload:
            raise PipelineError(f"Terraform output '{name}' is missing")
        return payload["value"]

    def _sync_from_terraform_outputs(self) -> None:
        self.args.resource_group = str(self._terraform_output_value("resource_group_name"))
        self.acr_name = str(self._terraform_output_value("acr_name"))
        self.args.cluster_name = str(self._terraform_output_value("cluster_name"))
        if "benchmark_nodepool_name" in self.terraform_outputs:
            self.args.nodepool = str(self._terraform_output_value("benchmark_nodepool_name"))
        actual_vm_size = str(self._terraform_output_value("node_vm_size"))
        if actual_vm_size != self.args.node_vm_size:
            warn(
                f"Terraform applied node_vm_size={actual_vm_size}, which differs from requested {self.args.node_vm_size}. "
                "Subsequent cluster checks will use the applied infrastructure state."
            )
            self.args.node_vm_size = actual_vm_size

    def _terraform_init(self) -> None:
        run_command(["terraform", "init", "-input=false"], cwd=self.infra_dir)

    def _az_tsv(self, args: list[str], *, check: bool = False) -> str:
        result = run_command(
            ["az", *args, "--output", "tsv"],
            capture_output=True,
            check=check,
        )
        return (result.stdout or "").strip() if result.returncode == 0 else ""

    def _terraform_uses_existing_acr(self) -> bool:
        return bool(getattr(self.args, "image_ref", None))

    def _terraform_creates_resource_group(self) -> bool:
        if self._resource_group_exists is None:
            group_id = self._az_tsv(
                ["group", "show", "--name", self.args.resource_group, "--query", "id"],
                check=False,
            )
            self._resource_group_exists = bool(group_id)
        return not self._resource_group_exists

    def _existing_acr_group(self) -> str:
        if self._existing_acr_resource_group is not None:
            return self._existing_acr_resource_group
        if not self.acr_name:
            raise PipelineError("ACR name is required before resolving existing ACR resource group")
        group = self._az_tsv(
            ["acr", "show", "--name", self.acr_name, "--query", "resourceGroup"],
            check=False,
        )
        if not group:
            raise PipelineError(
                f"ACR {self.acr_name} was not found in the current Azure subscription. "
                "The uniform-image run passes --image-ref, so the registry must already exist."
            )
        self._existing_acr_resource_group = group
        return group

    def _terraform_state_addresses(self) -> set[str]:
        result = run_command(
            ["terraform", "state", "list"],
            cwd=self.infra_dir,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in (result.stdout or "").splitlines() if line.strip()}

    def _terraform_import_if_exists(self, address: str, resource_id: str, state_addresses: set[str]) -> None:
        if address in state_addresses:
            return
        log(f"Importing existing Azure resource into Terraform state: {address}")
        run_command(
            ["terraform", "import", *self._terraform_var_args(), address, resource_id],
            cwd=self.infra_dir,
        )
        state_addresses.add(address)

    def _terraform_state_rm_if_present(self, addresses: list[str], state_addresses: set[str]) -> None:
        for address in addresses:
            if address not in state_addresses:
                continue
            log(
                f"Removing {address} from Terraform state because this run treats it "
                "as existing/shared infrastructure."
            )
            run_command(["terraform", "state", "rm", address], cwd=self.infra_dir)
            state_addresses.discard(address)

    def prepare_terraform_state(self) -> None:
        state_addresses = self._terraform_state_addresses()

        if not self._terraform_creates_resource_group():
            self._terraform_state_rm_if_present(
                ["azurerm_resource_group.rq15", "azurerm_resource_group.rq15[0]"],
                state_addresses,
            )

        if self._terraform_uses_existing_acr():
            self._terraform_state_rm_if_present(
                ["azurerm_container_registry.rq15", "azurerm_container_registry.rq15[0]"],
                state_addresses,
            )
        elif self.acr_name:
            acr_id = self._az_tsv(
                ["acr", "show", "--name", self.acr_name, "--query", "id"],
                check=False,
            )
            if acr_id:
                self._terraform_import_if_exists(
                    "azurerm_container_registry.rq15[0]",
                    acr_id,
                    state_addresses,
                )

        cluster_id = self._az_tsv(
            [
                "aks",
                "show",
                "--resource-group",
                self.args.resource_group,
                "--name",
                self.args.cluster_name,
                "--query",
                "id",
            ],
            check=False,
        )
        if cluster_id:
            self._terraform_import_if_exists(
                "azurerm_kubernetes_cluster.rq15",
                cluster_id,
                state_addresses,
            )
            nodepool_id = self._az_tsv(
                [
                    "aks",
                    "nodepool",
                    "show",
                    "--resource-group",
                    self.args.resource_group,
                    "--cluster-name",
                    self.args.cluster_name,
                    "--name",
                    self.args.nodepool,
                    "--query",
                    "id",
                ],
                check=False,
            )
            if nodepool_id:
                self._terraform_import_if_exists(
                    "azurerm_kubernetes_cluster_node_pool.benchmark[0]",
                    nodepool_id,
                    state_addresses,
                )
            else:
                self._terraform_state_rm_if_present(
                    ["azurerm_kubernetes_cluster_node_pool.benchmark[0]"],
                    state_addresses,
                )
        else:
            self._terraform_state_rm_if_present(
                [
                    "azurerm_kubernetes_cluster.rq15",
                    "azurerm_kubernetes_cluster_node_pool.benchmark[0]",
                    "azurerm_role_assignment.aks_acr_pull",
                ],
                state_addresses,
            )

    def target_aks_infrastructure_exists(self) -> bool:
        """Return true when the requested AKS/ACR target already exists.

        Terraform is used as "provision or reuse" for these runs. If the target
        cluster and registry already exist, quota preflight should not require
        the full VM quota again because Terraform can converge without adding
        nodes.
        """
        cluster = run_command(
            [
                "az", "aks", "show",
                "--resource-group", self.args.resource_group,
                "--name", self.args.cluster_name,
                "--query", "provisioningState",
                "-o", "tsv",
            ],
            capture_output=True,
            check=False,
        )
        if cluster.returncode != 0 or (cluster.stdout or "").strip().lower() != "succeeded":
            return False

        if getattr(self.args, "isolated_node_pools", False):
            nodepool = run_command(
                [
                    "az", "aks", "nodepool", "show",
                    "--resource-group", self.args.resource_group,
                    "--cluster-name", self.args.cluster_name,
                    "--name", self.args.nodepool,
                    "--query", "provisioningState",
                    "-o", "tsv",
                ],
                capture_output=True,
                check=False,
            )
            if nodepool.returncode != 0 or (nodepool.stdout or "").strip().lower() != "succeeded":
                return False

        if self.acr_name:
            acr_resource_group = (
                self._existing_acr_group()
                if self._terraform_uses_existing_acr()
                else self.args.resource_group
            )
            acr = run_command(
                [
                    "az", "acr", "show",
                    "--resource-group", acr_resource_group,
                    "--name", self.acr_name,
                    "--query", "provisioningState",
                    "-o", "tsv",
                ],
                capture_output=True,
                check=False,
            )
            if acr.returncode != 0 or (acr.stdout or "").strip().lower() != "succeeded":
                return False

        return True

    def refresh_kubeconfig(self) -> None:
        self.kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
        log(f"Refreshing kubeconfig for {self.args.cluster_name} in {self.kubeconfig_path}.")
        run_command(
            [
                "az", "aks", "get-credentials",
                "--resource-group", self.args.resource_group,
                "--name", self.args.cluster_name,
                "--overwrite-existing",
                "--file", az_cli_kubeconfig_path(self.kubeconfig_path),
            ]
        )

    def provision_with_terraform(self) -> None:
        log(f"Provisioning or reusing AKS infrastructure via Terraform in {self.infra_dir}.")
        self._terraform_init()
        self.prepare_terraform_state()
        if self.target_aks_infrastructure_exists():
            log(
                "Target AKS/ACR infrastructure already exists; reusing it without "
                "running Terraform apply."
            )
            result = run_command(
                ["terraform", "output", "-json"],
                cwd=self.infra_dir,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                self.terraform_outputs = json.loads(result.stdout or "{}")
                if self.terraform_outputs:
                    self._sync_from_terraform_outputs()
            else:
                warn(
                    "Could not read Terraform outputs while reusing existing infrastructure; "
                    "continuing with CLI arguments. "
                    f"Terraform output detail: {(result.stderr or result.stdout or '').strip()}"
                )
            self.refresh_kubeconfig()
            return
        else:
            self.azure_quota_preflight()
        run_command(
            [
                "terraform", "apply", "-auto-approve", "-input=false",
                *self._terraform_var_args(),
            ],
            cwd=self.infra_dir,
        )
        result = run_command(["terraform", "output", "-json"], cwd=self.infra_dir, capture_output=True)
        self.terraform_outputs = json.loads(result.stdout or "{}")
        self._sync_from_terraform_outputs()
        self.refresh_kubeconfig()

    def maybe_provision_cluster(self) -> None:
        if not self.args.provision:
            return
        self.provision_with_terraform()

    def _parse_acr_image_ref(self, image_ref: str) -> tuple[str, str, str | None, str | None]:
        match = re.match(
            r"^(?P<acr>[a-zA-Z0-9]+)\.azurecr\.io/(?P<repo>[^@:]+(?:/[^@:]+)*)(?:(?P<tag>:[^@]+)|@(?P<digest>sha256:[a-fA-F0-9]+))$",
            image_ref.strip(),
        )
        if not match:
            raise PipelineError(f"Unsupported ACR image reference: {image_ref!r}")
        tag = match.group("tag")
        return (
            match.group("acr"),
            match.group("repo"),
            tag[1:] if tag else None,
            match.group("digest"),
        )

    def _acr_manifest_exists(self, image_ref: str) -> tuple[bool, str]:
        acr_name, repository, tag, digest = self._parse_acr_image_ref(image_ref)
        manifest_name = f"{repository}@{digest}" if digest else f"{repository}:{tag}"
        attempts = [
            [
                "az", "acr", "manifest", "show-metadata",
                "--registry", acr_name,
                "--name", manifest_name,
                "-o", "json",
            ],
            [
                "az", "acr", "repository", "show",
                "--name", acr_name,
                "--image", manifest_name,
                "-o", "json",
            ],
        ]
        details = []
        for command in attempts:
            result = run_command(command, capture_output=True, check=False)
            if result.returncode == 0:
                return True, ""
            details.append((result.stderr or result.stdout or "").strip())
        return False, " | ".join(item for item in details if item) or "ACR manifest lookup failed"

    def push_image_to_acr(self, *, build: bool, reason: str) -> str:
        if not self.acr_name:
            raise PipelineError("Unable to determine the ACR name for image push")
        ensure_command("docker")
        ensure_command("az")

        if build:
            log(f"Building local image {self.args.local_image} before {reason}.")
            run_command(["docker", "build", "-t", self.args.local_image, "."])

        log(f"Logging in to ACR {self.acr_name}.azurecr.io.")
        run_command(["az", "acr", "login", "--name", self.acr_name])

        remote_image = f"{self.acr_name}.azurecr.io/thesis-inference:{self.args.image_tag}"
        log(f"Tagging {self.args.local_image} as {remote_image}.")
        run_command(["docker", "tag", self.args.local_image, remote_image])

        log(f"Pushing {remote_image}.")
        run_command(["docker", "push", remote_image])

        digest_result = run_command(
            [
                "az", "acr", "repository", "show",
                "--name", self.acr_name,
                "--image", f"thesis-inference:{self.args.image_tag}",
                "--query", "digest",
                "--output", "tsv",
            ],
            capture_output=True,
        )
        digest = (digest_result.stdout or "").strip().strip('"')
        if not digest.startswith("sha256:"):
            raise PipelineError(f"Unexpected ACR digest response after push: {digest!r}")
        pinned_ref = f"{self.acr_name}.azurecr.io/thesis-inference@{digest}"
        (self.state.artifact_dir / "image_reference.txt").write_text(pinned_ref + "\n", encoding="utf-8")
        (self.state.artifact_dir / "image_resolution.json").write_text(
            json.dumps(
                {
                    "reason": reason,
                    "acr_name": self.acr_name,
                    "local_image": self.args.local_image,
                    "pushed_tag": self.args.image_tag,
                    "pinned_ref": pinned_ref,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        log(f"Using pinned image reference {pinned_ref}.")
        return pinned_ref

    def resolve_image_reference(self) -> str:
        if getattr(self.args, "image_ref", None):
            if "@sha256:" not in self.args.image_ref:
                raise PipelineError("--image-ref must be a pinned digest reference")
            (self.state.artifact_dir / "image_reference.txt").write_text(
                self.args.image_ref + "\n",
                encoding="utf-8",
            )
            return self.args.image_ref

        configured_image = str(self.raw_config.get("kubernetes", {}).get("image", "")).strip()
        if self.args.push:
            return self.push_image_to_acr(build=self.args.build, reason="explicit --push")

        if "@sha256:" not in configured_image:
            raise PipelineError(
                "RQ2.1 live preflight requires a pinned kubernetes.image digest. "
                "Rerun with --push --build to publish and pin a fresh image automatically."
            )

        image_acr, _, _, _ = self._parse_acr_image_ref(configured_image)
        if self.acr_name and image_acr != self.acr_name:
            message = (
                f"Configured image uses ACR {image_acr}, but this run is targeting ACR {self.acr_name}. "
                "AKS was attached to the target ACR, so the effective config must use that registry."
            )
            if self.args.provision and not self.args.no_auto_push_missing_image:
                warn(message)
                return self.push_image_to_acr(build=True, reason="configured image registry differs from target ACR")
            raise PipelineError(message + " Rerun with --push --build or use the matching --acr-name.")

        exists, detail = self._acr_manifest_exists(configured_image)
        if exists:
            log(f"Verified pinned image exists in ACR: {configured_image}.")
            (self.state.artifact_dir / "image_reference.txt").write_text(configured_image + "\n", encoding="utf-8")
            return configured_image

        message = (
            f"Configured pinned image is not present in ACR or could not be verified: {configured_image}. "
            f"ACR detail: {detail}"
        )
        if self.args.provision and not self.args.no_auto_push_missing_image:
            warn(message)
            warn(
                "Because --provision is enabled, building and pushing a fresh thesis-inference image "
                "to avoid ImagePullBackOff."
            )
            return self.push_image_to_acr(build=True, reason="configured digest missing from provisioned ACR")

        raise PipelineError(
            message
            + "\nRerun with --push --build, or use --provision without --no-auto-push-missing-image "
            "so the runner can publish a fresh digest before applying manifests."
        )

    def _revision_sort_key(self, revision: str) -> tuple[int, ...]:
        numbers = re.findall(r"\d+", revision)
        return tuple(int(number) for number in numbers) if numbers else (0,)

    def _available_mesh_revisions(self) -> list[str]:
        result = run_command(
            [
                "az", "aks", "mesh", "get-revisions",
                "--location", self.args.location,
                "-o", "json",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            warn(
                "Unable to query AKS managed-Istio revisions for "
                f"{self.args.location}: {detail or result.returncode}"
            )
            return []
        revisions = sorted(
            set(re.findall(r"asm-\d+-\d+", result.stdout or "")),
            key=self._revision_sort_key,
        )
        return revisions

    def _requested_mesh_revision(self) -> str:
        return str(self.args.mesh_revision or self.mesh.get("revision") or "").strip()

    def _is_auto_revision(self, revision: str) -> bool:
        return revision.strip().lower() in {"auto", "latest", "supported"}

    def _select_supported_mesh_revision(self) -> str:
        requested = self._requested_mesh_revision()
        if not requested:
            raise PipelineError("kubernetes.mesh.revision must be set or --mesh-revision must be provided")

        available = self._available_mesh_revisions()
        installed = []
        try:
            installed = self._cluster_mesh_revisions()
        except PipelineError as exc:
            warn(f"Could not inspect currently installed mesh revisions before selection: {exc}")

        if self._is_auto_revision(requested):
            if installed:
                selected = sorted(installed, key=self._revision_sort_key)[-1]
                log(f"Using installed AKS managed-Istio revision {selected}.")
                return selected
            if available:
                selected = available[-1]
                log(
                    f"Selected latest available AKS managed-Istio revision {selected} "
                    f"for {self.args.location}."
                )
                return selected
            raise PipelineError(
                "Could not auto-select an AKS managed-Istio revision because Azure returned no available revisions. "
                "Run `az aks mesh get-revisions --location <location> -o table` and set --mesh-revision explicitly."
            )

        if requested in installed:
            return requested
        if requested in available:
            return requested
        if available:
            selected = available[-1]
            warn(
                f"Configured mesh revision {requested} is not available in {self.args.location}; "
                f"using supported revision {selected} for this run instead."
            )
            return selected
        return requested

    def write_effective_config(
        self,
        mesh_revision: str | None = None,
        image_ref: str | None = None,
    ) -> None:
        raw = load_yaml(self.source_config_path)
        raw.setdefault("kubernetes", {})
        raw["kubernetes"].setdefault("mesh", {})
        if image_ref is not None:
            raw["kubernetes"]["image"] = image_ref
        if mesh_revision:
            raw["kubernetes"]["mesh"]["revision"] = mesh_revision
            self.args.mesh_revision = mesh_revision
        elif self.args.mesh_revision:
            raw["kubernetes"]["mesh"]["revision"] = self.args.mesh_revision
        with self.state.effective_config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(raw, handle, sort_keys=False)

        self.raw_config = raw
        self.k8s = self._k8s_section()
        self.mesh = self._mesh_section()

    def prepare_effective_config(
        self,
        *,
        resolve_live_revision: bool,
        image_ref: str | None = None,
    ) -> None:
        if resolve_live_revision:
            self.write_effective_config(self._select_supported_mesh_revision(), image_ref=image_ref)
            return
        if self._is_auto_revision(self._requested_mesh_revision()):
            raise PipelineError(
                "--generate-only cannot use mesh revision auto-selection because it intentionally avoids live Azure calls. "
                "Pass --mesh-revision asm-X-Y for static manifest generation, or run without --generate-only."
            )
        self.write_effective_config(image_ref=image_ref)

    def generate_manifests(self) -> None:
        log(f"Generating RQ2.1 manifests into {self.state.manifest_dir}.")
        run_command([
            sys.executable,
            str(self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py"),
            "--config",
            str(self._active_config_path()),
            "--nodepool",
            self.args.nodepool,
            "--output-dir",
            str(self.state.manifest_dir),
        ])

    def verify_cluster_reachable(self) -> None:
        context_result = run_command(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            check=False,
        )
        current_context = (context_result.stdout or "").strip() or "unknown"
        cluster_result = run_command(
            ["kubectl", "cluster-info"],
            capture_output=True,
            check=False,
        )
        if cluster_result.returncode != 0:
            detail = (cluster_result.stderr or cluster_result.stdout or "").strip()
            raise PipelineError(
                "Kubernetes cluster is not reachable before applying RQ2.1 manifests. "
                f"Current context: {current_context}. "
                "This usually means the AKS cluster was deleted/recreated, the kubeconfig is stale, "
                "or WSL DNS cannot resolve the AKS API server hostname. "
                "Refresh kubeconfig with `az aks get-credentials --resource-group <rg> --name <cluster> --overwrite-existing` "
                "after confirming the cluster exists. "
                f"kubectl detail: {detail or 'no detail'}"
            )
        self.cluster_reachable = True
        first_line = (cluster_result.stdout or "").splitlines()[0] if cluster_result.stdout else "unknown"
        log(f"Kubernetes context: {current_context}")
        log(f"Cluster endpoint: {first_line}")

    def _configured_mesh_revision(self) -> str:
        revision = self._requested_mesh_revision()
        if not revision:
            raise PipelineError("kubernetes.mesh.revision is required for RQ2.1 mTLS")
        return revision

    def _cluster_mesh_revisions(self) -> list[str]:
        result = run_command(
            [
                "az", "aks", "show",
                "--resource-group", self.args.resource_group,
                "--name", self.args.cluster_name,
                "--query", "serviceMeshProfile.istio.revisions",
                "-o", "json",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(
                f"Unable to inspect AKS managed Istio add-on state for {self.args.cluster_name}: {detail}"
            )
        payload = json.loads(result.stdout or "null")
        if payload is None:
            return []
        if isinstance(payload, list):
            return [str(item) for item in payload if item not in (None, "")]
        return [str(payload)]

    def ensure_managed_istio(self) -> None:
        expected_revision = self._configured_mesh_revision()
        revisions = self._cluster_mesh_revisions()
        if expected_revision in revisions:
            log(
                f"AKS managed Istio add-on already has revision {expected_revision} "
                f"on {self.args.cluster_name}."
            )
            return

        if revisions:
            raise PipelineError(
                "AKS managed Istio add-on is enabled, but the configured revision is not present. "
                f"Configured kubernetes.mesh.revision={expected_revision}; observed revisions={revisions}. "
                "Update the RQ2.1 config to match the cluster or upgrade the mesh revision explicitly."
            )

        if self.args.skip_mesh_enable:
            raise PipelineError(
                "AKS managed Istio add-on is not enabled and --skip-mesh-enable was set. "
                f"Expected revision: {expected_revision}."
            )

        log(
            "Enabling AKS managed Istio add-on "
            f"for {self.args.cluster_name} with revision {expected_revision}."
        )
        result = run_command(
            [
                "az", "aks", "mesh", "enable",
                "--resource-group", self.args.resource_group,
                "--name", self.args.cluster_name,
                "--revision", expected_revision,
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(
                "Failed to enable the AKS managed Istio add-on. "
                "Check that the Azure CLI supports `az aks mesh`, the aks-preview extension if required, "
                "and that the configured revision is available in the cluster region. "
                f"Command output: {detail or result.returncode}"
            )

        revisions = self._cluster_mesh_revisions()
        if expected_revision not in revisions:
            raise PipelineError(
                "AKS managed Istio add-on enable command completed, but the expected revision was not observed. "
                f"Expected {expected_revision}; observed {revisions}."
            )
        log(f"AKS managed Istio add-on enabled with revision {expected_revision}.")

    def namespace_exists(self, namespace: str) -> bool:
        result = run_command(
            ["kubectl", "get", "namespace", namespace],
            check=False,
            capture_output=True,
        )
        return result.returncode == 0

    def wait_for_namespace_deletion(self, namespace: str, timeout_seconds: int = 180) -> None:
        deadline = time.monotonic() + timeout_seconds
        while self.namespace_exists(namespace):
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for namespace {namespace} to terminate")
            time.sleep(2)

    def cleanup_namespaces(self) -> None:
        namespaces = [self.service_namespace]
        if self.client_namespace != self.service_namespace:
            namespaces.append(self.client_namespace)
        for namespace in namespaces:
            log(f"Deleting namespace {namespace}.")
            run_command(
                ["kubectl", "delete", "namespace", namespace, "--ignore-not-found=true", "--wait=false"],
                check=False,
            )
        for namespace in namespaces:
            self.wait_for_namespace_deletion(namespace)
        self.state.resources_deployed = False

    def apply_manifests(self) -> None:
        if not self.args.preserve_existing:
            self.cleanup_namespaces()

        ordered_files = [
            self.state.manifest_dir / "00_namespace.yaml",
            self.state.manifest_dir / "01_service_accounts.yaml",
            self.state.manifest_dir / f"{self.condition_name}.yaml",
            self.state.manifest_dir / "99_benchmark_client.yaml",
        ]
        for path in ordered_files:
            if not path.exists():
                if path.name == "01_service_accounts.yaml":
                    continue
                raise PipelineError(f"Generated manifest is missing: {path}")
            log(f"Applying {path.name}.")
            run_command(["kubectl", "apply", "-f", str(path)])
        self.state.resources_deployed = True

    def wait_for_pod_exists(self, namespace: str, pod_name: str, timeout_seconds: int = 90) -> None:
        deadline = time.monotonic() + timeout_seconds
        while True:
            result = run_command(
                ["kubectl", "get", "pod", "-n", namespace, pod_name],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for pod {namespace}/{pod_name}")
            time.sleep(2)

    def wait_for_ready(self) -> None:
        timeout_seconds = self.readiness_timeout + 60
        deadline = time.monotonic() + timeout_seconds
        deployment_names: list[str] = []

        while True:
            payload = kubectl_text(
                [
                    "get",
                    "deployments",
                    "-n",
                    self.service_namespace,
                    "-l",
                    f"condition={self.condition_name}",
                    "-o",
                    "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
                ],
                check=False,
            )
            deployment_names = [line.strip() for line in payload.splitlines() if line.strip()]
            if len(deployment_names) == self.service_count:
                break
            if time.monotonic() >= deadline:
                raise PipelineError(
                    f"Timed out waiting for {self.service_count} deployments for {self.condition_name}"
                )
            time.sleep(2)

        for deployment_name in deployment_names:
            log(f"Waiting for deployment {deployment_name} rollout.")
            run_command([
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment_name}",
                "-n",
                self.service_namespace,
                f"--timeout={timeout_seconds}s",
            ])

        log("Waiting for inference service pods to become Ready.")
        run_command([
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-n",
            self.service_namespace,
            "-l",
            f"condition={self.condition_name},workload-role=service",
            f"--timeout={timeout_seconds}s",
        ])

        self.wait_for_pod_exists(self.client_namespace, self.args.client_pod)
        log("Waiting for benchmark client pod to become Ready.")
        run_command([
            "kubectl",
            "wait",
            "--for=condition=Ready",
            f"pod/{self.args.client_pod}",
            "-n",
            self.client_namespace,
            f"--timeout={timeout_seconds}s",
        ])

    def _namespace_snapshot(self, namespace: str) -> dict[str, Any]:
        payload = kubectl_json(["get", "namespace", namespace, "-o", "json"])
        metadata = payload.get("metadata") or {}
        return {
            "name": namespace,
            "labels": metadata.get("labels") or {},
            "annotations": metadata.get("annotations") or {},
        }

    def _service_pods(self) -> list[dict[str, Any]]:
        payload = kubectl_json([
            "get",
            "pods",
            "-n",
            self.service_namespace,
            "-l",
            f"condition={self.condition_name},workload-role=service",
            "-o",
            "json",
        ])
        return list(payload.get("items") or [])

    def _deployments(self) -> list[dict[str, Any]]:
        payload = kubectl_json([
            "get",
            "deployments",
            "-n",
            self.service_namespace,
            "-l",
            f"condition={self.condition_name},workload-role=service",
            "-o",
            "json",
        ])
        return list(payload.get("items") or [])

    def _client_pod(self) -> dict[str, Any]:
        return kubectl_json([
            "get",
            "pod",
            self.args.client_pod,
            "-n",
            self.client_namespace,
            "-o",
            "json",
        ])

    def _peer_authentications(self) -> list[dict[str, Any]]:
        payload = kubectl_json_or_none([
            "get",
            "peerauthentication.security.istio.io",
            "-n",
            self.service_namespace,
            "-o",
            "json",
        ])
        if not isinstance(payload, dict):
            return []
        return list(payload.get("items") or [])

    def _authorization_policies(self) -> list[dict[str, Any]]:
        payload = kubectl_json_or_none([
            "get",
            "authorizationpolicy.security.istio.io",
            "-n",
            self.service_namespace,
            "-o",
            "json",
        ])
        if not isinstance(payload, dict):
            return []
        return list(payload.get("items") or [])

    def _authorization_policy_config(self) -> dict[str, Any]:
        authz = self.mesh.get("authorization_policy") or {}
        return authz if isinstance(authz, dict) else {}

    def _authorization_policy_name(self) -> str:
        expected = self._expected_authorization_policies()
        return expected[0]["name"] if expected else "downstream-service1-only"

    def _authorization_policy_expected_principal(self, policy: dict[str, str] | None = None) -> str:
        if policy is not None:
            return str(policy.get("expected_principal") or "")
        expected = self._expected_authorization_policies()
        return expected[0]["expected_principal"] if expected else ""

    def _condition_service_name(self, segment_index: int) -> str:
        template = str(self.k8s.get("service_name_template") or "{condition}-svc-{index}")
        return format_k8s_service_name(template, self.condition_name, segment_index)

    def _mesh_control_plane_pods(self) -> list[dict[str, Any]]:
        payload = kubectl_json_or_none(["get", "pods", "-A", "-o", "json"])
        if not isinstance(payload, dict):
            return []
        records = []
        system_namespaces = {"aks-istio-system", "istio-system", "kube-system"}
        for pod in payload.get("items") or []:
            metadata = pod.get("metadata") or {}
            namespace = str(metadata.get("namespace") or "")
            if namespace not in system_namespaces:
                continue
            name = str(metadata.get("name") or "")
            labels = metadata.get("labels") or {}
            label_blob = " ".join(f"{key}={value}" for key, value in labels.items()).lower()
            identity_blob = f"{namespace} {name} {label_blob}".lower()
            if not (
                namespace in {"aks-istio-system", "istio-system"}
                or "istio" in identity_blob
                or "asm" in identity_blob
                or "envoy" in identity_blob
            ):
                continue
            records.append({
                "namespace": namespace,
                "pod_name": name,
                "node_name": (pod.get("spec") or {}).get("nodeName", "unknown"),
                "phase": (pod.get("status") or {}).get("phase", "unknown"),
                "labels": labels,
                "owner_references": metadata.get("ownerReferences", []) or [],
            })
        return records

    def _app_container_specs(self, pod: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            container
            for container in (pod.get("spec") or {}).get("containers", [])
            if isinstance(container, dict)
        ]

    def _init_container_specs(self, pod: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            container
            for container in (pod.get("spec") or {}).get("initContainers", [])
            if isinstance(container, dict)
        ]

    def _all_container_specs(self, pod: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        return [
            ("init", container)
            for container in self._init_container_specs(pod)
        ] + [
            ("app", container)
            for container in self._app_container_specs(pod)
        ]

    def _app_container_names(self, pod: dict[str, Any]) -> list[str]:
        return [str(container.get("name")) for container in self._app_container_specs(pod)]

    def _container_names(self, pod: dict[str, Any]) -> list[str]:
        return [
            str(container.get("name"))
            for _, container in self._all_container_specs(pod)
        ]

    def _status_by_container(self, pod: dict[str, Any]) -> dict[str, dict[str, Any]]:
        status_payload = pod.get("status") or {}
        statuses = (
            (status_payload.get("containerStatuses") or [])
            + (status_payload.get("initContainerStatuses") or [])
        )
        return {
            str(status.get("name")): status
            for status in statuses
            if isinstance(status, dict)
        }

    def _pod_name(self, pod: dict[str, Any]) -> str:
        return str((pod.get("metadata") or {}).get("name") or "unknown")

    def _segment_index(self, pod: dict[str, Any]) -> str:
        return str(((pod.get("metadata") or {}).get("labels") or {}).get("segment-index") or "unknown")

    def _container_ready(self, pod: dict[str, Any], container_name: str) -> bool:
        return bool(self._status_by_container(pod).get(container_name, {}).get("ready", False))

    def _bad_pod_states(self, pod: dict[str, Any]) -> list[str]:
        errors = []
        pod_name = self._pod_name(pod)
        phase = str((pod.get("status") or {}).get("phase") or "unknown")
        if phase in {"Pending", "Failed", "Unknown"}:
            errors.append(f"{pod_name}: pod phase is {phase}")

        for condition in (pod.get("status") or {}).get("conditions") or []:
            if condition.get("type") == "PodScheduled" and condition.get("status") == "False":
                reason = condition.get("reason") or "unknown"
                errors.append(f"{pod_name}: pod scheduling failed ({reason})")

        status_payload = pod.get("status") or {}
        statuses = (
            (status_payload.get("containerStatuses") or [])
            + (status_payload.get("initContainerStatuses") or [])
        )
        for status in statuses:
            state = status.get("state") or {}
            waiting = state.get("waiting") or {}
            reason = waiting.get("reason")
            if reason in {
                "CrashLoopBackOff",
                "ImagePullBackOff",
                "ErrImagePull",
                "CreateContainerConfigError",
                "CreateContainerError",
            }:
                errors.append(f"{pod_name}/{status.get('name')}: container waiting reason is {reason}")
        return errors

    def _pod_summary(self, pod: dict[str, Any]) -> dict[str, Any]:
        statuses = self._status_by_container(pod)
        containers = []
        for container_type, container in self._all_container_specs(pod):
            name = str(container.get("name") or "unknown")
            status = statuses.get(name, {})
            containers.append({
                "name": name,
                "container_type": container_type,
                "native_sidecar": container_type == "init" and name == "istio-proxy",
                "image": container.get("image", "unknown"),
                "image_id": status.get("imageID", "unknown"),
                "ready": bool(status.get("ready", False)),
                "resources": container.get("resources", {}) or {},
            })
        return {
            "pod_name": self._pod_name(pod),
            "namespace": (pod.get("metadata") or {}).get("namespace", "unknown"),
            "node_name": (pod.get("spec") or {}).get("nodeName", "unknown"),
            "phase": (pod.get("status") or {}).get("phase", "unknown"),
            "service_account_name": (pod.get("spec") or {}).get("serviceAccountName", "unknown"),
            "labels": (pod.get("metadata") or {}).get("labels", {}) or {},
            "annotations": (pod.get("metadata") or {}).get("annotations", {}) or {},
            "containers": containers,
            "sidecar_present": any(container["name"] == "istio-proxy" for container in containers),
            "sidecar_image_ids": [
                container["image_id"]
                for container in containers
                if container["name"] == "istio-proxy" and container["image_id"] not in (None, "")
            ],
        }

    def _deployment_proxy_annotations(self, deployments: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
        records: dict[str, dict[str, str]] = {}
        for deployment in deployments:
            name = str((deployment.get("metadata") or {}).get("name") or "unknown")
            annotations = (
                ((deployment.get("spec") or {}).get("template") or {})
                .get("metadata", {})
                .get("annotations", {})
                or {}
            )
            records[name] = {
                key: str(annotations.get(key))
                for key in (
                    "sidecar.istio.io/proxyCPU",
                    "sidecar.istio.io/proxyCPULimit",
                    "sidecar.istio.io/proxyMemory",
                    "sidecar.istio.io/proxyMemoryLimit",
                )
                if key in annotations
            }
        return records

    def _authorization_policy_principals(self, policy: dict[str, Any]) -> list[str]:
        principals: list[str] = []
        for rule in (policy.get("spec") or {}).get("rules") or []:
            for source in rule.get("from") or []:
                source_block = source.get("source") or {}
                principals.extend(str(item) for item in source_block.get("principals") or [])
        return principals

    def _validate_authorization_policy(self, policies: list[dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        expected_policies = self._expected_authorization_policies()
        by_name = {
            str((item.get("metadata") or {}).get("name") or ""): item
            for item in policies
        }
        expected_names = {policy["name"] for policy in expected_policies}
        observed_names = {name for name in by_name if name}
        unexpected_names = sorted(observed_names - expected_names)
        if unexpected_names:
            errors.append(f"Unexpected AuthorizationPolicy resources: {unexpected_names}")
        if len(policies) != len(expected_policies):
            errors.append(
                f"Expected exactly {len(expected_policies)} AuthorizationPolicy resources; found {len(policies)}"
            )

        for expected in expected_policies:
            expected_name = expected["name"]
            expected_principal = self._authorization_policy_expected_principal(expected)
            downstream_segment = expected["downstream_segment_index"]
            policy = by_name.get(expected_name)
            if not policy:
                errors.append(f"Missing AuthorizationPolicy {expected_name}")
                continue

            spec = policy.get("spec") or {}
            selector = (spec.get("selector") or {}).get("matchLabels") or {}
            if (
                selector.get("condition") != self.condition_name
                or selector.get("segment-index") != downstream_segment
                or selector.get("workload-role") != "service"
            ):
                errors.append(
                    f"AuthorizationPolicy {expected_name} must select condition={self.condition_name}, "
                    f"segment-index={downstream_segment}, workload-role=service"
                )
            if str(spec.get("action") or "ALLOW") != "ALLOW":
                errors.append(f"AuthorizationPolicy {expected_name} must use action=ALLOW")

            observed_principals = sorted(set(self._authorization_policy_principals(policy)))
            if observed_principals != [expected_principal]:
                errors.append(
                    f"AuthorizationPolicy {expected_name} must allow only source principal {expected_principal}; "
                    f"observed {observed_principals}"
                )
        return errors

    def collect_preflight_metadata(
        self,
        service_pods: list[dict[str, Any]],
        client_pod: dict[str, Any],
        deployments: list[dict[str, Any]],
        peer_auths: list[dict[str, Any]],
        authorization_policies: list[dict[str, Any]],
        control_plane_pods: list[dict[str, Any]],
        enforcement_validation: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        service_summaries = [self._pod_summary(pod) for pod in service_pods]
        client_summary = self._pod_summary(client_pod)
        benchmark_nodes = {
            item["node_name"]
            for item in service_summaries
            if item["node_name"] not in (None, "", "unknown")
        }
        if client_summary["node_name"] not in (None, "", "unknown"):
            benchmark_nodes.add(client_summary["node_name"])
        shared_avoidable_control_plane_pods = [
            pod
            for pod in control_plane_pods
            if str(pod.get("node_name") or "") in benchmark_nodes
            and is_avoidable_istio_control_plane_pod(pod)
        ]
        return {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "config_path": str(self._active_config_path()),
            "condition": self.condition_name,
            "topology": (SUPPORTED_TOPOLOGIES.get(self.service_count) or {}).get("name"),
            "service_count": self.service_count,
            "mesh": {
                "enabled": bool(self.mesh.get("enabled", False)),
                "implementation": self.mesh.get("implementation"),
                "revision": self.mesh.get("revision"),
                "namespace": self.mesh.get("namespace") or self.service_namespace,
            },
            "namespaces": {
                "service": self._namespace_snapshot(self.service_namespace),
                "client": self._namespace_snapshot(self.client_namespace),
            },
            "service_accounts": {
                "declared": self.mesh.get("service_accounts") or {},
                "observed_by_pod": {
                    item["pod_name"]: item["service_account_name"]
                    for item in service_summaries
                },
            },
            "sidecar_presence_per_pod": {
                item["pod_name"]: item["sidecar_present"]
                for item in service_summaries
            },
            "sidecar_image_ids_by_pod": {
                item["pod_name"]: item["sidecar_image_ids"]
                for item in service_summaries
            },
            "proxy_resources": {
                "declared": self.mesh.get("proxy_resources") or {},
                "annotations_by_deployment": self._deployment_proxy_annotations(deployments),
            },
            "peer_authentication_resources": [
                {
                    "name": (item.get("metadata") or {}).get("name", "unknown"),
                    "namespace": (item.get("metadata") or {}).get("namespace", self.service_namespace),
                    "labels": (item.get("metadata") or {}).get("labels", {}) or {},
                    "spec": item.get("spec", {}) or {},
                }
                for item in peer_auths
            ],
            "authorization_policy_resources": [
                {
                    "name": (item.get("metadata") or {}).get("name", "unknown"),
                    "namespace": (item.get("metadata") or {}).get("namespace", self.service_namespace),
                    "labels": (item.get("metadata") or {}).get("labels", {}) or {},
                    "spec": item.get("spec", {}) or {},
                }
                for item in authorization_policies
            ],
            "enforcement_validation": enforcement_validation,
            "service_pod_node_placement": {
                item["pod_name"]: item["node_name"]
                for item in service_summaries
            },
            "client_pod_node_placement": {
                client_summary["pod_name"]: client_summary["node_name"],
            },
            "service_pods": service_summaries,
            "client_pod": client_summary,
            "mesh_control_plane_system_pod_placement": control_plane_pods,
            "control_plane_isolation": {
                "required": (
                    bool(getattr(self.args, "isolated_node_pools", False))
                    or placement_requires_control_plane_isolation(self.k8s.get("placement") or {})
                ),
                "benchmark_node_names": sorted(benchmark_nodes),
                "avoidable_istio_control_plane_pods_on_benchmark_node": shared_avoidable_control_plane_pods,
                "violates_isolated_pool_contract": bool(
                    shared_avoidable_control_plane_pods
                    and (
                        bool(getattr(self.args, "isolated_node_pools", False))
                        or placement_requires_control_plane_isolation(self.k8s.get("placement") or {})
                    )
                ),
            },
            "preflight_passed": not errors,
            "errors": errors,
            "warnings": warnings,
            "limitations": warnings,
        }

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        self.state.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state.metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
        log(f"Wrote RQ2.1 preflight metadata: {self.state.metadata_path}")

    def _validate_runtime_placement(
        self,
        service_pods: list[dict[str, Any]],
        client_pod: dict[str, Any],
    ) -> tuple[list[str], dict[str, Any]]:
        placement = self.k8s.get("placement") or {}
        strategy = placement_strategy(placement)
        service_records = [
            {
                "pod_name": self._pod_name(pod),
                "node_name": str((pod.get("spec") or {}).get("nodeName") or "unknown"),
            }
            for pod in service_pods
        ]
        service_nodes = [
            record["node_name"]
            for record in service_records
            if record["node_name"] not in {"", "unknown"}
        ]
        service_node_set = set(service_nodes)
        client_node = str((client_pod.get("spec") or {}).get("nodeName") or "unknown")
        errors: list[str] = []

        if placement_is_multi_node(placement):
            unknown_services = [
                record["pod_name"]
                for record in service_records
                if record["node_name"] in {"", "unknown"}
            ]
            if unknown_services:
                errors.append(
                    "Multi-node placement validation is missing service node names for "
                    + ", ".join(unknown_services)
                )
            if len(service_node_set) != len(service_records):
                errors.append(
                    "Inference service pods are not on distinct nodes: "
                    + json.dumps(
                        {
                            record["pod_name"]: record["node_name"]
                            for record in service_records
                        },
                        sort_keys=True,
                    )
                )
            if client_node in {"", "unknown"}:
                errors.append("Benchmark client node placement is unknown")
            elif bool(placement.get("require_dedicated_client_node", False)) and client_node in service_node_set:
                errors.append(
                    f"Benchmark client is not on a dedicated node: client={client_node}, "
                    f"services={sorted(service_node_set)}"
                )
        else:
            if len(service_node_set) != 1:
                errors.append(
                    f"Inference service pods are not strictly colocated on one node: "
                    f"{sorted(service_node_set)}"
                )
            if len(service_node_set) == 1 and client_node not in service_node_set:
                errors.append(
                    f"Benchmark client is not colocated with inference services: "
                    f"client={client_node}, services={sorted(service_node_set)}"
                )

        return errors, {
            "strategy": strategy,
            "service_pod_node_placement": {
                record["pod_name"]: record["node_name"]
                for record in service_records
            },
            "service_nodes": sorted(service_node_set),
            "client_node": client_node,
            "service_nodes_distinct": len(service_node_set) == len(service_records),
            "dedicated_client_node": (
                client_node not in {"", "unknown"} and client_node not in service_node_set
            ),
        }

    def run_formal_preflight(self) -> None:
        errors: list[str] = []
        warnings: list[str] = []

        service_pods = self._service_pods()
        client_pod = self._client_pod()
        deployments = self._deployments()
        peer_auths = self._peer_authentications()
        authorization_policies = self._authorization_policies()
        control_plane_pods = self._mesh_control_plane_pods()
        enforcement_validation: dict[str, Any] = {
            "ran": False,
            "skipped_reason": "preflight static checks have not completed",
        }

        if len(service_pods) != self.service_count:
            errors.append(
                f"Expected {self.service_count} service pods for {self.condition_name}, found {len(service_pods)}"
            )
        if len(deployments) != self.service_count:
            errors.append(
                f"Expected {self.service_count} service deployments for {self.condition_name}, found {len(deployments)}"
            )

        service_ns_labels = self._namespace_snapshot(self.service_namespace)["labels"]
        expected_revision = str(self.mesh.get("revision"))
        if service_ns_labels.get("istio.io/rev") != expected_revision:
            errors.append(
                f"Service namespace must be labeled istio.io/rev={expected_revision}; found {service_ns_labels.get('istio.io/rev')}"
            )
        client_ns_labels = self._namespace_snapshot(self.client_namespace)["labels"]
        if client_ns_labels.get("istio.io/rev") or client_ns_labels.get("istio-injection") == "enabled":
            errors.append("Client namespace has a mesh injection label; benchmark client must remain outside the mesh")

        declared_accounts = {
            str(key): str(value)
            for key, value in (self.mesh.get("service_accounts") or {}).items()
        }
        for pod in service_pods:
            pod_name = self._pod_name(pod)
            segment_index = self._segment_index(pod)
            all_container_names = self._container_names(pod)
            app_container_names = self._app_container_names(pod)
            if "istio-proxy" not in all_container_names:
                errors.append(f"{pod_name}: missing istio-proxy container")
            if "inference" not in app_container_names:
                errors.append(f"{pod_name}: missing inference app container")
            if not self._container_ready(pod, "inference"):
                errors.append(f"{pod_name}: inference container is not Ready")
            if not self._container_ready(pod, "istio-proxy"):
                errors.append(f"{pod_name}: istio-proxy container is not Ready")

            observed_account = str((pod.get("spec") or {}).get("serviceAccountName") or "")
            expected_account = declared_accounts.get(segment_index)
            if observed_account in {"", "default"}:
                errors.append(f"{pod_name}: uses namespace default service account")
            if expected_account and observed_account != expected_account:
                errors.append(
                    f"{pod_name}: expected serviceAccountName={expected_account}, found {observed_account}"
                )
            errors.extend(self._bad_pod_states(pod))

        placement_errors, placement_summary = self._validate_runtime_placement(
            service_pods,
            client_pod,
        )
        errors.extend(placement_errors)
        service_nodes = set(placement_summary["service_nodes"])

        client_container_names = self._app_container_names(client_pod)
        all_client_container_names = self._container_names(client_pod)
        if client_container_names != ["client"]:
            errors.append(
                f"Benchmark client must have exactly one app container named client; found {client_container_names}"
            )
        if "istio-proxy" in all_client_container_names:
            errors.append("Benchmark client pod contains istio-proxy; client must remain non-meshed")
        errors.extend(self._bad_pod_states(client_pod))

        proxy_annotations = self._deployment_proxy_annotations(deployments)
        required_annotations = {
            "sidecar.istio.io/proxyCPU": str((self.mesh.get("proxy_resources") or {}).get("cpu_request")),
            "sidecar.istio.io/proxyCPULimit": str((self.mesh.get("proxy_resources") or {}).get("cpu_limit")),
            "sidecar.istio.io/proxyMemory": str((self.mesh.get("proxy_resources") or {}).get("memory_request")),
            "sidecar.istio.io/proxyMemoryLimit": str((self.mesh.get("proxy_resources") or {}).get("memory_limit")),
        }
        for deployment_name, annotations in proxy_annotations.items():
            for key, expected_value in required_annotations.items():
                if annotations.get(key) != expected_value:
                    errors.append(
                        f"{deployment_name}: expected annotation {key}={expected_value}, found {annotations.get(key)}"
                    )

        peer_by_name = {
            str((item.get("metadata") or {}).get("name")): item
            for item in peer_auths
        }
        default_peer = peer_by_name.get("default")
        if not default_peer:
            errors.append("Missing namespace default PeerAuthentication")
        else:
            default_spec = default_peer.get("spec") or {}
            if (default_spec.get("mtls") or {}).get("mode") != "PERMISSIVE":
                errors.append("Namespace default PeerAuthentication must set mtls.mode=PERMISSIVE")
            if default_spec.get("selector"):
                errors.append("Namespace default PeerAuthentication must not have a workload selector")

        strict_by_segment: dict[str, list[dict[str, Any]]] = {}
        for peer_auth in peer_auths:
            spec = peer_auth.get("spec") or {}
            selector = (spec.get("selector") or {}).get("matchLabels") or {}
            mode = str((spec.get("mtls") or {}).get("mode") or "").upper()
            if (
                mode == "STRICT"
                and selector.get("condition") == self.condition_name
                and selector.get("workload-role") == "service"
            ):
                strict_by_segment.setdefault(str(selector.get("segment-index") or ""), []).append(peer_auth)
        expected_strict_segments = set(self._expected_downstream_segments())
        observed_strict_segments = set(strict_by_segment)
        expected_peer_count = 1 + len(expected_strict_segments)
        if len(peer_auths) != expected_peer_count:
            errors.append(
                f"Expected exactly {expected_peer_count} PeerAuthentication resources "
                f"(namespace default plus downstream STRICT policies); found {len(peer_auths)}"
            )
        if observed_strict_segments != expected_strict_segments:
            errors.append(
                "STRICT PeerAuthentication resources must select exactly downstream service segments "
                f"{sorted(expected_strict_segments)}; found {sorted(observed_strict_segments)}"
            )
        for segment in sorted(expected_strict_segments):
            if len(strict_by_segment.get(segment) or []) != 1:
                errors.append(
                    f"Expected exactly one STRICT PeerAuthentication for segment {segment}; "
                    f"found {len(strict_by_segment.get(segment) or [])}"
                )

        errors.extend(self._validate_authorization_policy(authorization_policies))

        client_node = str((client_pod.get("spec") or {}).get("nodeName") or "unknown")
        benchmark_nodes = set(service_nodes)
        if client_node != "unknown":
            benchmark_nodes.add(client_node)
        control_plane_nodes = {
            str(item.get("node_name"))
            for item in control_plane_pods
            if item.get("node_name") not in (None, "", "unknown")
        }
        shared_nodes = sorted(benchmark_nodes & control_plane_nodes)
        shared_avoidable_control_plane_pods = [
            pod
            for pod in control_plane_pods
            if str(pod.get("node_name") or "") in benchmark_nodes
            and is_avoidable_istio_control_plane_pod(pod)
        ]
        isolation_required = (
            bool(getattr(self.args, "isolated_node_pools", False))
            or placement_requires_control_plane_isolation(self.k8s.get("placement") or {})
        )
        if isolation_required and shared_avoidable_control_plane_pods:
            errors.append(
                "Isolated-pool RQ2.1 contract violated: avoidable Istio control-plane pods share "
                "benchmark node(s): "
                + ", ".join(
                    f"{pod.get('namespace')}/{pod.get('pod_name')}@{pod.get('node_name')}"
                    for pod in shared_avoidable_control_plane_pods
                )
            )
        if shared_nodes:
            warnings.append(
                "Mesh control-plane/system pods share benchmark node(s) "
                + ", ".join(shared_nodes)
                + "; recorded as an RQ2.1 placement limitation."
            )

        if errors:
            enforcement_validation = {
                "ran": False,
                "skipped_reason": "static preflight validation failed before runtime probes",
                "expected_non_mesh_direct_failure": True,
            }
        else:
            enforcement_validation, enforcement_errors = self.run_enforcement_validation()
            errors.extend(enforcement_errors)

        metadata = self.collect_preflight_metadata(
            service_pods,
            client_pod,
            deployments,
            peer_auths,
            authorization_policies,
            control_plane_pods,
            enforcement_validation,
            errors,
            warnings,
        )
        self.metadata = metadata
        self.write_metadata(metadata)

        if errors:
            raise PipelineError("RQ2.1 mTLS preflight failed:\n- " + "\n- ".join(errors))

        log("RQ2.1 mTLS preflight passed.")
        for item in warnings:
            warn(item)

    def _debug_probe_node_selector(self) -> dict[str, str]:
        selector: dict[str, str] = {}
        placement = self.k8s.get("placement") or {}
        node_pool = str(placement.get("node_pool") or self.args.nodepool or "").strip()
        if node_pool:
            selector["agentpool"] = node_pool
        explicit = placement.get("node_selector") or {}
        selector.update({str(key): str(value) for key, value in explicit.items()})
        return selector

    def _debug_probe_tolerations(self) -> list[dict[str, Any]]:
        placement = self.k8s.get("placement") or {}
        return placement_tolerations(placement)

    def _debug_probe_manifest(self, pod_name: str) -> dict[str, Any]:
        container = {
            "name": "debug",
            "image": str(self.k8s.get("image")),
            "imagePullPolicy": str(self.k8s.get("image_pull_policy") or "Always"),
            "command": ["sleep", "infinity"],
        }
        client_resources = self.k8s.get("client_resources") or {}
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
        spec: dict[str, Any] = {
            "restartPolicy": "Never",
            "containers": [container],
        }
        node_selector = self._debug_probe_node_selector()
        if node_selector:
            spec["nodeSelector"] = node_selector
        tolerations = self._debug_probe_tolerations()
        if tolerations:
            spec["tolerations"] = tolerations
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": self.client_namespace,
                "labels": {
                    "app": "thesis-inference",
                    "condition": self.condition_name,
                    "experiment-condition": self.condition_name,
                    "workload-role": "debug-client",
                    "role": "debug-client",
                    "mesh-enabled": "false",
                    "security-condition": "mtls",
                },
                "annotations": {
                    "sidecar.istio.io/inject": "false",
                },
            },
            "spec": spec,
        }

    def _write_enforcement_json(self, payload: dict[str, Any]) -> None:
        path = self.state.diagnostics_dir / "enforcement_validation.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _run_full_chain_probe(self) -> tuple[dict[str, Any], list[str]]:
        errors: list[str] = []
        output_path = self.state.diagnostics_dir / "full_chain_probe_output.txt"
        first_target = (
            f"{self._condition_service_name(1)}."
            f"{self.service_namespace}.svc.cluster.local:{self.k8s.get('grpc_port', 50051)}"
        )
        result_payload: dict[str, Any] = {
            "description": (
                "Positive chain probe: non-meshed benchmark client calls service1 only; "
                f"the mesh-protected chain must return {self.service_count} hop timings."
            ),
            "target": first_target,
            "expected_hop_count": self.service_count,
            "expected_hop_indexes": list(range(1, self.service_count + 1)),
            "output_file": str(output_path),
        }

        try:
            probe_code = (
                "import json, sys\n"
                "import numpy as np\n"
                "import torch\n"
                "from src.client.chain_client import ChainClient\n"
                "target = sys.argv[1]\n"
                "max_message_bytes = int(sys.argv[2])\n"
                "torch.set_num_threads(1)\n"
                "torch.set_num_interop_threads(1)\n"
                "client = ChainClient(target, max_message_bytes=max_message_bytes)\n"
                "try:\n"
                "    tensor = torch.from_numpy(np.zeros((1, 3, 224, 224), dtype=np.float32))\n"
                "    response = client.infer_response(tensor)\n"
                "    hops = [\n"
                "        {\n"
                "            'hop_index': hop.hop_index,\n"
                "            'deserialize_ms': hop.deserialize_ms,\n"
                "            'compute_ms': hop.compute_ms,\n"
                "            'serialize_ms': hop.serialize_ms,\n"
                "            'forward_ms': hop.forward_ms,\n"
                "            'activation_bytes': hop.activation_bytes,\n"
                "        }\n"
                "        for hop in response.hop_timings\n"
                "    ]\n"
                "    payload = {\n"
                "        'target': target,\n"
                "        'response_shape': list(response.shape),\n"
                "        'hop_count': len(hops),\n"
                "        'hop_indexes': [hop['hop_index'] for hop in hops],\n"
                "        'hop_timings': hops,\n"
                "    }\n"
                "    print(json.dumps(payload, indent=2))\n"
                "    expected_hops = int(sys.argv[3])\n"
                "    expected_indexes = list(range(1, expected_hops + 1))\n"
                "    if len(hops) != expected_hops or sorted(hop['hop_index'] for hop in hops) != expected_indexes:\n"
                "        print('UNEXPECTED_HOPS: service1 did not return the expected chain hop timings', file=sys.stderr)\n"
                "        sys.exit(43)\n"
                "finally:\n"
                "    client.close()\n"
            )
            command = [
                "kubectl",
                "exec",
                "-n",
                self.client_namespace,
                self.args.client_pod,
                "--",
                "python",
                "-c",
                probe_code,
                first_target,
                str(self.k8s.get("max_message_bytes", 16 * 1024 * 1024)),
                str(self.service_count),
            ]
            completed = run_command(
                command,
                capture_output=True,
                check=False,
                timeout_seconds=max(300, self.readiness_timeout * 4),
            )
            combined_output = (completed.stdout or "") + (completed.stderr or "")
            output_path.write_text(combined_output, encoding="utf-8")
            result_payload.update({
                "returncode": completed.returncode,
                "succeeded": completed.returncode == 0,
            })
            try:
                probe_payload = json.loads(completed.stdout or "{}")
                if isinstance(probe_payload, dict):
                    result_payload.update({
                        "hop_count": probe_payload.get("hop_count"),
                        "hop_indexes": probe_payload.get("hop_indexes"),
                        "hop_timings": probe_payload.get("hop_timings"),
                        "response_shape": probe_payload.get("response_shape"),
                    })
            except json.JSONDecodeError:
                pass
            if completed.returncode != 0:
                errors.append(
                    "Positive service1 chain probe failed; see diagnostics/full_chain_probe_output.txt"
                )
        except Exception as exc:
            output_path.write_text(str(exc), encoding="utf-8")
            result_payload.update({
                "returncode": None,
                "succeeded": False,
                "exception": str(exc),
            })
            errors.append(f"Positive service1 chain probe failed: {exc}")
        return result_payload, errors

    def _run_non_mesh_direct_denial_probe(self) -> tuple[dict[str, Any], list[str]]:
        errors: list[str] = []
        pod_name = "rq21-direct-deny-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        targets = [
            {
                "segment_index": index,
                "target": (
                    f"{self._condition_service_name(index)}."
                    f"{self.service_namespace}.svc.cluster.local:{self.k8s.get('grpc_port', 50051)}"
                ),
            }
            for index in range(2, self.service_count + 1)
        ]
        manifest = self._debug_probe_manifest(pod_name)
        manifest_path = self.state.diagnostics_dir / "negative_direct_probe_pod.yaml"
        output_path = self.state.diagnostics_dir / "negative_direct_probe_output.txt"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        result_payload: dict[str, Any] = {
            "description": "Non-meshed debug pod direct gRPC readiness probes to downstream services.",
            "pod_name": pod_name,
            "namespace": self.client_namespace,
            "target": targets[0]["target"] if targets else None,
            "targets": targets,
            "expected_failure": True,
            "manifest_file": str(manifest_path),
            "output_file": str(output_path),
            "pod_preserved": True,
        }

        try:
            run_command(["kubectl", "apply", "-f", str(manifest_path)], timeout_seconds=90)
            run_command([
                "kubectl",
                "wait",
                "--for=condition=Ready",
                f"pod/{pod_name}",
                "-n",
                self.client_namespace,
                "--timeout=120s",
            ], timeout_seconds=150)
            probe_code = (
                "import grpc, sys\n"
                "target = sys.argv[1]\n"
                "timeout = float(sys.argv[2])\n"
                "print(f'probing {target} from a non-meshed pod')\n"
                "channel = grpc.insecure_channel(target)\n"
                "try:\n"
                "    grpc.channel_ready_future(channel).result(timeout=timeout)\n"
                "except Exception as exc:\n"
                "    print('EXPECTED_FAILURE: direct non-meshed gRPC channel was not ready:', type(exc).__name__, str(exc))\n"
                "    sys.exit(42)\n"
                "else:\n"
                "    print('UNEXPECTED_SUCCESS: direct non-meshed gRPC channel became ready')\n"
                "    sys.exit(0)\n"
                "finally:\n"
                "    channel.close()\n"
            )
            output_chunks: list[str] = []
            target_results = []
            for target_record in targets:
                completed = run_command([
                    "kubectl",
                    "exec",
                    "-n",
                    self.client_namespace,
                    pod_name,
                    "--",
                    "python",
                    "-c",
                    probe_code,
                    target_record["target"],
                    "8",
                ], capture_output=True, check=False, timeout_seconds=60)
                combined_output = (completed.stdout or "") + (completed.stderr or "")
                output_chunks.append(
                    f"## segment {target_record['segment_index']} -> {target_record['target']}\n"
                    + combined_output
                )
                blocked_as_expected = completed.returncode == 42
                target_result = {
                    **target_record,
                    "returncode": completed.returncode,
                    "blocked_as_expected": blocked_as_expected,
                    "succeeded_unexpectedly": completed.returncode == 0,
                }
                target_results.append(target_result)
                if completed.returncode == 0:
                    errors.append(
                        f"Non-meshed debug pod unexpectedly reached downstream service{target_record['segment_index']} directly; "
                        "STRICT mTLS/AuthorizationPolicy enforcement did not fail closed"
                    )
                elif completed.returncode != 42:
                    errors.append(
                        f"Non-meshed debug pod denial probe for service{target_record['segment_index']} did not complete cleanly; "
                        "see diagnostics/negative_direct_probe_output.txt"
                    )
            output_path.write_text("\n".join(output_chunks), encoding="utf-8")
            all_blocked = bool(target_results) and all(item["blocked_as_expected"] for item in target_results)
            result_payload.update({
                "returncode": 42 if all_blocked else None,
                "blocked_as_expected": all_blocked,
                "succeeded_unexpectedly": any(item["succeeded_unexpectedly"] for item in target_results),
                "target_results": target_results,
                "blocked_segments": [
                    item["segment_index"]
                    for item in target_results
                    if item["blocked_as_expected"]
                ],
            })
            if all_blocked:
                run_command([
                    "kubectl",
                    "delete",
                    "pod",
                    pod_name,
                    "-n",
                    self.client_namespace,
                    "--ignore-not-found=true",
                    "--wait=false",
                ], check=False, timeout_seconds=30)
                result_payload["pod_preserved"] = False
        except Exception as exc:
            output_path.write_text(str(exc), encoding="utf-8")
            result_payload.update({
                "returncode": None,
                "blocked_as_expected": False,
                "exception": str(exc),
            })
            errors.append(f"Non-meshed debug pod denial probe failed to run: {exc}")
        return result_payload, errors

    def run_enforcement_validation(self) -> tuple[dict[str, Any], list[str]]:
        log("Running functional mTLS/service-identity enforcement validation.")
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        validation: dict[str, Any] = {
            "ran": True,
            "expected_non_mesh_direct_failure": True,
            "authorization_policy_expected_principal": self._authorization_policy_expected_principal(),
            "authorization_policy_expected_principals": [
                policy["expected_principal"]
                for policy in self._expected_authorization_policies()
            ],
        }
        errors: list[str] = []

        chain_probe, chain_errors = self._run_full_chain_probe()
        validation["full_chain_probe"] = chain_probe
        errors.extend(chain_errors)

        direct_probe, direct_errors = self._run_non_mesh_direct_denial_probe()
        validation["non_mesh_direct_denial_probe"] = direct_probe
        errors.extend(direct_errors)

        validation["passed"] = not errors
        validation["errors"] = errors
        self._write_enforcement_json(validation)
        return validation, errors

    def write_file_into_pod(self, remote_path: str, content: str) -> None:
        import base64

        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        code = (
            "import base64, pathlib, sys; "
            "path = pathlib.Path(sys.argv[2]); "
            "path.parent.mkdir(parents=True, exist_ok=True); "
            "path.write_bytes(base64.b64decode(sys.argv[1]))"
        )
        run_command([
            "kubectl",
            "exec",
            "-n",
            self.client_namespace,
            self.args.client_pod,
            "--",
            "python",
            "-c",
            code,
            encoded,
            remote_path,
        ])

    def run_smoke_benchmark(self) -> None:
        log("Injecting runtime metadata before the optional smoke benchmark.")
        run_command([
            sys.executable,
            str(self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py"),
            "--config",
            str(self._active_config_path()),
            "--namespace",
            self.service_namespace,
            "--client-namespace",
            self.client_namespace,
            "--client-pod",
            self.args.client_pod,
        ])
        remote_config = "/tmp/rq21_effective_config.yaml"
        self.write_file_into_pod(remote_config, self._active_config_path().read_text(encoding="utf-8"))
        remote_output = f"/tmp/rq21_smoke_{utc_run_stamp()}"
        log("Running optional tiny in-cluster smoke benchmark.")
        command = [
            "kubectl",
            "exec",
            "-n",
            self.client_namespace,
            self.args.client_pod,
            "--",
            "python",
            "run_k8s_experiment.py",
            "--config",
            remote_config,
            "--condition",
            self.condition_name,
            "--output-dir",
            remote_output,
        ]
        completed = run_command(command, capture_output=True, check=False)
        smoke_output_path = self.state.artifact_dir / "smoke_benchmark_output.txt"
        smoke_output_path.write_text(
            (completed.stdout or "") + (completed.stderr or ""),
            encoding="utf-8",
        )
        smoke_marker = self.state.artifact_dir / "smoke_benchmark_remote_path.txt"
        smoke_marker.write_text(remote_output + "\n", encoding="utf-8")
        smoke_json = self.state.artifact_dir / "smoke_benchmark_artifact.json"
        smoke_json.write_text(
            json.dumps(
                {
                    "remote_output_dir": remote_output,
                    "local_command_output": str(smoke_output_path),
                    "returncode": completed.returncode,
                    "succeeded": completed.returncode == 0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise PipelineError(
                f"Optional smoke benchmark failed; see {smoke_output_path}"
            )
        log(f"Smoke benchmark completed in client pod path {remote_output}.")

    def gather_diagnostics(self) -> None:
        if self.args.generate_only:
            return
        if not self.cluster_reachable:
            warn("Skipping Kubernetes diagnostics because the cluster was not reachable.")
            return
        log(f"Gathering RQ2.1 diagnostics under {self.state.diagnostics_dir}.")
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        commands = {
            "service_pods_wide.txt": ["get", "pods", "-n", self.service_namespace, "-o", "wide"],
            "client_pods_wide.txt": ["get", "pods", "-n", self.client_namespace, "-o", "wide"],
            "service_deployments.txt": ["get", "deployments", "-n", self.service_namespace, "-o", "wide"],
            "service_pods_describe.txt": [
                "describe",
                "pods",
                "-n",
                self.service_namespace,
                "-l",
                f"condition={self.condition_name},workload-role=service",
            ],
            "client_pod_describe.txt": [
                "describe",
                "pod",
                self.args.client_pod,
                "-n",
                self.client_namespace,
            ],
            "service_events.txt": [
                "get",
                "events",
                "-n",
                self.service_namespace,
                "--sort-by=.lastTimestamp",
            ],
            "service_logs_inference.txt": [
                "logs",
                "-n",
                self.service_namespace,
                "-l",
                f"condition={self.condition_name},workload-role=service",
                "-c",
                "inference",
                "--tail=200",
                "--prefix=true",
            ],
            "service_logs_istio_proxy.txt": [
                "logs",
                "-n",
                self.service_namespace,
                "-l",
                f"condition={self.condition_name},workload-role=service",
                "-c",
                "istio-proxy",
                "--tail=200",
                "--prefix=true",
            ],
            "client_events.txt": [
                "get",
                "events",
                "-n",
                self.client_namespace,
                "--sort-by=.lastTimestamp",
            ],
            "client_logs.txt": [
                "logs",
                "-n",
                self.client_namespace,
                self.args.client_pod,
                "-c",
                "client",
                "--tail=200",
            ],
            "peer_authentication.txt": [
                "get",
                "peerauthentication.security.istio.io",
                "-n",
                self.service_namespace,
                "-o",
                "yaml",
            ],
            "authorization_policy.txt": [
                "get",
                "authorizationpolicy.security.istio.io",
                "-n",
                self.service_namespace,
                "-o",
                "yaml",
            ],
        }
        for file_name, args in commands.items():
            result = run_command(["kubectl", *args], capture_output=True, check=False)
            (self.state.diagnostics_dir / file_name).write_text(
                (result.stdout or "") + (result.stderr or ""),
                encoding="utf-8",
            )

    def handle_failure(self, exc: Exception) -> None:
        try:
            self.gather_diagnostics()
        except Exception as diag_exc:
            warn(f"Failed to gather diagnostics: {diag_exc}")
        if self.state.resources_deployed and self.args.cleanup_on_failure:
            try:
                log("Cleanup-on-failure enabled; deleting RQ2.1 namespaces.")
                self.cleanup_namespaces()
            except Exception as cleanup_exc:
                warn(f"Failed to clean up namespaces after failure: {cleanup_exc}")
        elif self.state.resources_deployed:
            warn(
                f"Preserving namespaces {self.service_namespace} and {self.client_namespace} for inspection."
            )
        warn(f"RQ2.1 run failed. Artifacts directory: {self.state.artifact_dir}")
        print(f"[{timestamp()}] ERROR: {exc}", file=sys.stderr)

    def run(self) -> None:
        self.validate_config()
        topology_spec = SUPPORTED_TOPOLOGIES.get(self.service_count) or {}
        log(
            f"RQ2.1 runner scope: {self.condition_name} preflight "
            f"({topology_spec.get('framing', 'supported RQ2.1 topology')}); "
            "the paired plain-vs-mTLS benchmark is intentionally not run here."
        )
        self.prepare_artifact_dirs()
        self.verify_required_files()
        self.verify_host_prerequisites()
        if self.args.generate_only:
            self.prepare_effective_config(resolve_live_revision=False)
        else:
            self.maybe_provision_cluster()
            self.effective_image_ref = self.resolve_image_reference()
            self.prepare_effective_config(
                resolve_live_revision=True,
                image_ref=self.effective_image_ref,
            )
            self.ensure_managed_istio()
        self.generate_manifests()
        if self.args.generate_only:
            log("Generate-only mode complete; no live AKS preflight was run.")
            return
        self.verify_cluster_reachable()
        self.apply_manifests()
        self.wait_for_ready()
        self.run_formal_preflight()
        if self.args.smoke_benchmark:
            self.run_smoke_benchmark()
        if self.args.cleanup_on_success:
            self.cleanup_namespaces()
        log(f"RQ2.1 Stage 1/2 preflight artifacts: {self.state.artifact_dir}")


def main() -> int:
    args = parse_args()
    try:
        runner = RQ21PreflightRunner(args)
        runner.run()
    except Exception as exc:
        if "runner" in locals():
            runner.handle_failure(exc)
        else:
            print(f"[{timestamp()}] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
