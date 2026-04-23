from __future__ import annotations

import argparse
import base64
import csv
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.benchmark.config import format_k8s_service_name, load_config, sanitize_k8s_name_component
from src.benchmark.deployment_metadata import build_environment_deployment_section


DEFAULT_CONFIG_REL = "configs/rq1/1.1/rq1_1_azure_fully_controlled.yaml"
DEFAULT_CLIENT_POD = "benchmark-client"
DEFAULT_NODEPOOL = "rq11pool"
DEFAULT_RESOURCE_GROUP = "rg-thesis-rq11"
DEFAULT_CLUSTER_NAME = "thesis-rq11"
DEFAULT_LOCATION = "swedencentral"
DEFAULT_NODE_VM_SIZE = "Standard_D4s_v3"
DEFAULT_NODE_COUNT = 1
GENERATED_DIR = REPO_ROOT / "k8s" / "aks" / "generated"
INFRA_DIR = REPO_ROOT / "infra"

EXPECTED_CONDITIONS = {
    "monolithic": ("monolithic", None),
    "split_after_layer1": ("split", "layer1"),
    "split_after_layer2": ("split", "layer2"),
    "split_after_layer3": ("split", "layer3"),
    "split_after_layer4": ("split", "layer4"),
}


class PipelineError(RuntimeError):
    pass


@dataclass
class RunnerState:
    host_export_dir: Path
    diagnostics_dir: Path
    host_partial_results_dir: Path
    host_benchmark_log_dir: Path
    merged_results_dir: Path
    effective_config_path: Path
    pod_partial_results_root: str
    pod_config_path: str
    final_results_dir: Path | None = None
    resources_deployed: bool = False
    infra_provisioned: bool = False


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def log(message: str) -> None:
    print(f"[{timestamp()}] {message}")


def warn(message: str) -> None:
    print(f"[{timestamp()}] WARN: {message}", file=sys.stderr)


_WINDOWS_COMMAND_SUFFIXES = (".exe", ".cmd", ".bat", ".com")


def _resolve_command_name(command_name: str) -> str | None:
    resolved = shutil.which(command_name)
    if resolved:
        return resolved

    if not _running_under_wsl() or os.path.splitext(command_name)[1]:
        return None

    for suffix in _WINDOWS_COMMAND_SUFFIXES:
        resolved = shutil.which(f"{command_name}{suffix}")
        if resolved:
            return resolved
    return None


def _normalize_command_args(args: list[str]) -> list[str]:
    if not args:
        return args
    resolved = _resolve_command_name(args[0])
    if not resolved:
        return args
    return [resolved, *args[1:]]


def ensure_command(command_name: str) -> None:
    if _resolve_command_name(command_name) is None:
        raise PipelineError(f"Required command not found: {command_name}")


def wsl_windows_kubeconfig_pair() -> tuple[Path, str] | None:
    az_path = _resolve_command_name("az") or ""
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


def _running_under_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def az_cli_kubeconfig_path(kubeconfig_path: Path) -> str:
    shared_wsl_pair = wsl_windows_kubeconfig_pair()
    if shared_wsl_pair is not None and kubeconfig_path == shared_wsl_pair[0]:
        return shared_wsl_pair[1]

    az_path = _resolve_command_name("az") or ""
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
    text: bool = True,
) -> subprocess.CompletedProcess:
    normalized_args = _normalize_command_args(args)
    result = subprocess.run(
        normalized_args,
        cwd=str(cwd) if cwd else None,
        capture_output=capture_output,
        text=text,
    )
    if check and result.returncode != 0:
        cmd = " ".join(args)
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise PipelineError(f"Command failed: {cmd}\n{detail}")
    return result


def stream_command(args: list[str], log_path: Path, *, cwd: Path | None = None) -> None:
    normalized_args = _normalize_command_args(args)
    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            normalized_args,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            handle.write(line)

        exit_code = process.wait()
        if exit_code != 0:
            raise PipelineError(
                f"Command failed with exit code {exit_code}: {' '.join(args)}"
            )


def require_python_modules(module_names: list[str]) -> None:
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive path
            raise PipelineError(
                f"Required Python module '{module_name}' is not available: {exc}"
            ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Provision, deploy, benchmark, export, and optionally destroy the "
            "AKS-backed RQ1.1 fully controlled coarse split benchmark."
        )
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_REL, help="Source experiment config YAML")
    parser.add_argument(
        "--results-root",
        default=str(REPO_ROOT / "results_exports"),
        help="Parent directory for host-side exported artifacts",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Namespace override for the run. Defaults to kubernetes.namespace in the config.",
    )
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD, help="Benchmark client pod name")
    parser.add_argument(
        "--pod-config-path",
        default="/tmp/rq11_effective_config.yaml",
        help="Path inside the client pod where the effective config is copied",
    )
    parser.add_argument(
        "--nodepool",
        default=DEFAULT_NODEPOOL,
        help="AKS nodepool label used for preflight and manifest generation",
    )
    parser.add_argument(
        "--terraform-dir",
        default=str(INFRA_DIR),
        help="Terraform working directory for AKS provisioning",
    )
    parser.add_argument(
        "--provision",
        action="store_true",
        help="Provision the Azure resource group, ACR, AKS cluster, and kubeconfig before the run",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push a fresh image to ACR and use the resolved digest for this run",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the Docker image before pushing. Only valid with --push.",
    )
    parser.add_argument(
        "--acr-name",
        default=None,
        help="ACR name without the .azurecr.io suffix. Derived from kubernetes.image when omitted.",
    )
    parser.add_argument(
        "--image-tag",
        default=f"rq11-{utc_run_stamp().lower()}",
        help="Tag to push when --push is used",
    )
    parser.add_argument(
        "--local-image",
        default="thesis-inference:latest",
        help="Local Docker image to tag and push",
    )
    parser.add_argument("--resource-group", default=DEFAULT_RESOURCE_GROUP, help="Azure resource group name")
    parser.add_argument("--cluster-name", default=DEFAULT_CLUSTER_NAME, help="AKS cluster name")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help="Azure region for provisioning")
    parser.add_argument("--node-count", type=int, default=DEFAULT_NODE_COUNT, help="Node count for AKS provisioning")
    parser.add_argument(
        "--node-vm-size",
        default=DEFAULT_NODE_VM_SIZE,
        help="VM SKU used when provisioning the AKS cluster",
    )
    parser.add_argument(
        "--keep-infra",
        "--skip-destroy",
        dest="keep_infra",
        action="store_true",
        help="Preserve the Kubernetes namespace and Terraform-managed Azure resources for inspection",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the fail-closed cluster preflight. Not recommended for thesis-facing runs.",
    )
    args = parser.parse_args()

    if args.build and not args.push:
        parser.error("--build requires --push")
    return args


class RQ11AzureOrchestrator:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))
        self.repo_root = REPO_ROOT
        self.infra_dir = Path(args.terraform_dir).resolve()
        self.source_config_path = self._resolve_source_config_path(args.config)
        self.run_ts = utc_run_stamp()
        host_export_dir = Path(args.results_root).resolve() / f"rq1_1_azure_fully_controlled_{self.run_ts}"
        self.state = RunnerState(
            host_export_dir=host_export_dir,
            diagnostics_dir=host_export_dir / "diagnostics",
            host_partial_results_dir=host_export_dir / "partial_results",
            host_benchmark_log_dir=host_export_dir / "condition_logs",
            merged_results_dir=host_export_dir / "merged_results",
            effective_config_path=host_export_dir / "effective_config.yaml",
            pod_partial_results_root=f"/tmp/rq11_azure_{self.run_ts}",
            pod_config_path=args.pod_config_path,
        )
        self.raw_config = self._load_raw_config(self.source_config_path)
        self.namespace = args.namespace or str(self.raw_config["kubernetes"]["namespace"])
        self.conditions: list[str] = []
        self.condition_specs: dict[str, dict[str, Any]] = {}
        self.acr_name = args.acr_name or self._derive_acr_name_from_config()
        self.effective_image_ref = ""
        self.current_context = ""
        self.terraform_outputs: dict[str, Any] = {}
        self.placement_policy: dict[str, Any] = {
            "strategy": "none",
            "require_same_node": False,
            "fail_if_not_colocated": False,
            "node_selector": {},
            "node_pool": None,
        }

    def _requested_vm_profile(self) -> tuple[int, str]:
        result = run_command(
            [
                "az", "vm", "list-skus",
                "-l", self.args.location,
                "--size", self.args.node_vm_size,
                "-o", "json",
            ],
            capture_output=True,
        )
        payload = json.loads(result.stdout or "[]")
        if not payload:
            raise PipelineError(
                f"Azure SKU metadata lookup returned no records for {self.args.node_vm_size} in {self.args.location}"
            )

        sku = next(
            (item for item in payload if str(item.get("name")) == self.args.node_vm_size),
            payload[0],
        )
        family = str(sku.get("family") or "")
        capabilities = {entry.get("name"): entry.get("value") for entry in sku.get("capabilities", [])}
        vcpus_text = str(capabilities.get("vCPUs") or capabilities.get("vCPUsAvailable") or "")
        if not vcpus_text.isdigit():
            raise PipelineError(
                f"Unable to determine vCPU count for {self.args.node_vm_size} from Azure SKU metadata"
            )
        return int(vcpus_text), family

    def azure_quota_preflight(self) -> None:
        requested_vm_vcpus, requested_family = self._requested_vm_profile()
        requested_total_vcpus = requested_vm_vcpus * self.args.node_count

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
                f"but {self.args.node_vm_size} x{self.args.node_count} requires {requested_total_vcpus}."
            )

        family_record = None
        if requested_family:
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
            if family_available < requested_total_vcpus:
                raise PipelineError(
                    "Azure family quota preflight failed before provisioning. "
                    f"Family {requested_family} in {self.args.location} has only {family_available} vCPUs available, "
                    f"but {self.args.node_vm_size} x{self.args.node_count} requires {requested_total_vcpus}."
                )

    def _load_raw_config(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def _resolve_source_config_path(self, config_arg: str) -> Path:
        requested = Path(config_arg).expanduser()
        candidates: list[Path] = []

        if requested.is_absolute():
            candidates.append(requested)
        else:
            candidates.append((self.repo_root / requested).resolve())
            candidates.append((Path.cwd() / requested).resolve())

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        basename_matches = sorted(self.repo_root.glob(f"configs/**/{requested.name}"))
        if len(basename_matches) == 1:
            resolved = basename_matches[0].resolve()
            try:
                relative_path = resolved.relative_to(self.repo_root)
            except ValueError:
                relative_path = resolved
            warn(
                f"Config path '{config_arg}' was not found directly; using discovered config '{relative_path}'."
            )
            return resolved

        if len(basename_matches) > 1:
            options = "\n- ".join(
                str(match.resolve().relative_to(self.repo_root))
                for match in basename_matches
            )
            raise PipelineError(
                "Config path resolution is ambiguous for "
                f"'{config_arg}'. Matching files under the repository:\n- {options}"
            )

        raise PipelineError(
            f"Config file not found: {config_arg}. "
            f"Relative paths are resolved from repository root {self.repo_root}."
        )

    def _derive_acr_name_from_config(self) -> str | None:
        image = str(self.raw_config.get("kubernetes", {}).get("image", "")).strip()
        match = re.match(r"^([a-zA-Z0-9]+)\.azurecr\.io/", image)
        return match.group(1) if match else None

    def prepare_artifact_dirs(self) -> None:
        self.state.host_export_dir.mkdir(parents=True, exist_ok=True)
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self.state.host_partial_results_dir.mkdir(parents=True, exist_ok=True)
        self.state.host_benchmark_log_dir.mkdir(parents=True, exist_ok=True)

    def verify_required_files(self) -> None:
        required_paths = [
            self.source_config_path,
            self.repo_root / "run_analysis.py",
            self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py",
            self.repo_root / "scripts" / "preflight_rq11_azure.py",
            self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py",
            self.repo_root / "src" / "benchmark" / "k8s_split_experiment.py",
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
        ensure_command("kubectl")
        if self.args.push:
            ensure_command("docker")
            ensure_command("az")
        if self.args.provision:
            ensure_command("terraform")
            ensure_command("az")
        require_python_modules(["yaml", "scipy", "matplotlib"])

    def _terraform_var_args(self) -> list[str]:
        if not self.acr_name:
            raise PipelineError("ACR name is required for Terraform provisioning")
        return [
            f"-var=resource_group_name={self.args.resource_group}",
            f"-var=location={self.args.location}",
            f"-var=acr_name={self.acr_name}",
            f"-var=cluster_name={self.args.cluster_name}",
            f"-var=nodepool_name={self.args.nodepool}",
            f"-var=node_count={self.args.node_count}",
            f"-var=node_vm_size={self.args.node_vm_size}",
        ]

    def _terraform_output_value(self, name: str) -> Any:
        payload = self.terraform_outputs.get(name)
        if not isinstance(payload, dict) or "value" not in payload:
            raise PipelineError(f"Terraform output '{name}' is missing")
        return payload["value"]

    def _sync_from_terraform_outputs(self) -> None:
        self.args.resource_group = str(self._terraform_output_value("resource_group_name"))
        self.acr_name = str(self._terraform_output_value("acr_name"))
        self.args.cluster_name = str(self._terraform_output_value("cluster_name"))
        actual_vm_size = str(self._terraform_output_value("node_vm_size"))
        if actual_vm_size != self.args.node_vm_size:
            warn(
                f"Terraform applied node_vm_size={actual_vm_size}, which differs from requested {self.args.node_vm_size}. "
                "Subsequent cluster checks will use the applied infrastructure state."
            )
            self.args.node_vm_size = actual_vm_size

    def _terraform_init(self) -> None:
        run_command(["terraform", "init", "-input=false"], cwd=self.infra_dir)

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
        log(f"Provisioning AKS infrastructure via Terraform in {self.infra_dir}.")
        self.azure_quota_preflight()
        self._terraform_init()
        try:
            run_command(
                [
                    "terraform", "apply", "-auto-approve", "-input=false",
                    *self._terraform_var_args(),
                ],
                cwd=self.infra_dir,
            )
        except Exception:
            warn("Terraform apply failed; attempting best-effort cleanup of partial resources.")
            try:
                self.destroy_with_terraform()
            except Exception as cleanup_exc:  # pragma: no cover - best effort cleanup
                warn(f"Automatic Terraform cleanup failed: {cleanup_exc}")
            raise

        result = run_command(["terraform", "output", "-json"], cwd=self.infra_dir, capture_output=True)
        self.terraform_outputs = json.loads(result.stdout or "{}")
        self._sync_from_terraform_outputs()
        self.refresh_kubeconfig()
        self.state.infra_provisioned = True

    def destroy_with_terraform(self) -> None:
        log(f"Destroying Terraform-managed AKS infrastructure in {self.infra_dir}.")
        self._terraform_init()
        run_command(
            [
                "terraform", "destroy", "-auto-approve", "-input=false",
                *self._terraform_var_args(),
            ],
            cwd=self.infra_dir,
        )

    def maybe_provision_cluster(self) -> None:
        if not self.args.provision:
            return
        self.provision_with_terraform()

    def refresh_cluster_context(self, *, retry_seconds: int = 180, retry_interval: int = 10) -> None:
        self.current_context = self.kubectl_text(["config", "current-context"])
        log(f"Kubernetes context: {self.current_context}")
        deadline = time.monotonic() + retry_seconds
        last_exc: Exception | None = None
        while True:
            try:
                cluster_info = self.kubectl_text(["cluster-info"])
                first_line = cluster_info.splitlines()[0] if cluster_info else "unknown"
                log(f"Cluster endpoint: {first_line}")
                return
            except Exception as exc:
                last_exc = exc
                remaining = int(deadline - time.monotonic())
                if remaining <= 0:
                    break
                log(f"Cluster not yet reachable ({exc}); retrying in {retry_interval}s ({remaining}s remaining)...")
                time.sleep(retry_interval)
        raise PipelineError(f"Cluster not reachable after {retry_seconds}s: {last_exc}")

    def resolve_image_reference(self) -> str:
        configured_image = str(self.raw_config.get("kubernetes", {}).get("image", "")).strip()
        if self.args.push:
            if not self.acr_name:
                raise PipelineError("Unable to determine the ACR name for --push")
            if self.args.build:
                log(f"Building local image {self.args.local_image}.")
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
            digest = (digest_result.stdout or "").strip()
            if not digest.startswith("sha256:"):
                raise PipelineError(f"Unexpected ACR digest response: {digest!r}")
            pinned_ref = f"{self.acr_name}.azurecr.io/thesis-inference@{digest}"
            log(f"Using pinned image reference {pinned_ref}.")
            return pinned_ref

        if "@sha256:" not in configured_image:
            raise PipelineError(
                "Source config does not contain a pinned digest image. Either update the config "
                "or rerun with --push to publish and pin a new image automatically."
            )
        log(f"Using pinned image from config: {configured_image}")
        return configured_image

    def write_effective_config(self, image_ref: str | None = None) -> None:
        raw = self._load_raw_config(self.source_config_path)
        raw.setdefault("kubernetes", {})
        raw["kubernetes"]["namespace"] = self.namespace
        if image_ref is not None:
            raw["kubernetes"]["image"] = image_ref
        with self.state.effective_config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(raw, handle, sort_keys=False)

    def validate_effective_config(self, *, require_pinned_image: bool) -> None:
        with self.state.effective_config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)

        k8s = raw.get("kubernetes") or {}
        placement = k8s.get("placement") or {}
        service = k8s.get("resources") or {}
        client = k8s.get("client_resources") or service
        threading = (raw.get("cpu_stabilisation") or {}).get("threading") or {}
        governor = (raw.get("cpu_stabilisation") or {}).get("governor") or {}
        turbo = (raw.get("cpu_stabilisation") or {}).get("turbo") or {}
        errors: list[str] = []

        image = str(k8s.get("image", ""))
        if require_pinned_image and "@sha256:" not in image:
            errors.append("kubernetes.image must be a pinned digest reference for the thesis-facing run")
        if str(k8s.get("image_pull_policy", "")) != "Always":
            errors.append("kubernetes.image_pull_policy must be Always for the thesis-facing run")
        if str(placement.get("strategy", "")) != "strict_same_node":
            errors.append("kubernetes.placement.strategy must be strict_same_node")
        if placement.get("require_same_node") is not True:
            errors.append("kubernetes.placement.require_same_node must be true")
        if placement.get("fail_if_not_colocated") is not True:
            errors.append("kubernetes.placement.fail_if_not_colocated must be true")
        configured_node_pool = str(placement.get("node_pool") or "").strip()
        if configured_node_pool and configured_node_pool != str(self.args.nodepool):
            errors.append(
                f"kubernetes.placement.node_pool must match --nodepool ({self.args.nodepool}), found {configured_node_pool}"
            )

        for label, resources in (("service", service), ("client", client)):
            if str(resources.get("cpu_request")) != str(resources.get("cpu_limit")):
                errors.append(f"{label} cpu_request must equal cpu_limit for fully controlled QoS")
            if str(resources.get("memory_request")) != str(resources.get("memory_limit")):
                errors.append(f"{label} memory_request must equal memory_limit for fully controlled QoS")
            if not re.fullmatch(r"[0-9]+", str(resources.get("cpu_request", ""))):
                errors.append(f"{label} cpu_request must be an integer core value for the AKS profile")

        expected_threads = {
            "pytorch_intra_op": 1,
            "pytorch_inter_op": 1,
            "omp_num_threads": 1,
            "mkl_num_threads": 1,
            "openblas_num_threads": 1,
        }
        for key, expected in expected_threads.items():
            actual = threading.get(key)
            if actual != expected:
                errors.append(f"cpu_stabilisation.threading.{key} expected {expected}, found {actual}")

        if governor.get("set_governor"):
            errors.append("cpu_stabilisation.governor.set_governor must be false on AKS")
        if turbo.get("disable_turbo"):
            errors.append("cpu_stabilisation.turbo.disable_turbo must be false on AKS")

        condition_map = {cond["name"]: cond for cond in raw.get("conditions", [])}
        if set(condition_map) != set(EXPECTED_CONDITIONS):
            errors.append(
                "conditions must be exactly: " + ", ".join(sorted(EXPECTED_CONDITIONS))
            )
        else:
            for name, (expected_type, expected_split) in EXPECTED_CONDITIONS.items():
                condition = condition_map[name]
                if str(condition.get("type")) != expected_type:
                    errors.append(f"{name} must have type={expected_type}")
                if expected_split is not None and str(condition.get("split_after")) != expected_split:
                    errors.append(f"{name} must have split_after={expected_split}")

        if errors:
            raise PipelineError("Effective config validation failed:\n- " + "\n- ".join(errors))

    def load_conditions(self) -> None:
        config = load_config(str(self.state.effective_config_path))
        self.conditions = [condition.name for condition in config.conditions]
        placement = config.kubernetes.placement
        self.placement_policy = {
            "strategy": placement.strategy,
            "require_same_node": bool(placement.require_same_node),
            "fail_if_not_colocated": bool(placement.fail_if_not_colocated),
            "node_selector": dict(placement.node_selector),
            "node_pool": placement.node_pool,
        }
        self.condition_specs = {}
        for condition in config.conditions:
            if condition.type == "monolithic":
                remote_service_count = 0
            elif condition.type == "split":
                remote_service_count = 1
            elif condition.type == "chain":
                remote_service_count = len(condition.chain_split_points or []) + 1
            else:
                raise PipelineError(f"Unsupported condition type: {condition.type}")
            self.condition_specs[condition.name] = {
                "type": condition.type,
                "split_after": condition.split_after,
                "remote_service_count": remote_service_count,
            }
        if not self.conditions:
            raise PipelineError("No conditions were found in the effective config")

    def run_cluster_preflight(self) -> None:
        if self.args.skip_preflight:
            warn("Skipping scripts/preflight_rq11_azure.py at user request.")
            return

        log("Running fail-closed cluster preflight for the AKS-backed RQ1.1 profile.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "scripts" / "preflight_rq11_azure.py"),
                "--config", str(self.state.effective_config_path),
                "--mode", "rolling",
                "--namespace", self.namespace,
                "--nodepool", self.args.nodepool,
            ]
        )

    def generate_manifests(self) -> None:
        log(f"Generating AKS manifests from {self.state.effective_config_path}.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py"),
                "--config", str(self.state.effective_config_path),
                "--nodepool", self.args.nodepool,
            ]
        )

    def validate_generated_manifests(self) -> None:
        log("Validating generated manifests against the effective RQ1.1 Azure config.")
        with self.state.effective_config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)

        threading = raw["cpu_stabilisation"]["threading"]
        k8s = raw["kubernetes"]
        placement = k8s.get("placement") or {}
        placement_strategy = str(placement.get("strategy") or "none")
        resources = k8s["resources"]
        client_resources = k8s["client_resources"]
        expected_env = {
            "PYTORCH_INTRA_OP_THREADS": str(threading["pytorch_intra_op"]),
            "PYTORCH_INTER_OP_THREADS": str(threading["pytorch_inter_op"]),
            "OMP_NUM_THREADS": str(threading["omp_num_threads"]),
            "MKL_NUM_THREADS": str(threading["mkl_num_threads"]),
            "OPENBLAS_NUM_THREADS": str(threading["openblas_num_threads"]),
        }
        condition_map = {cond["name"]: cond for cond in raw["conditions"]}

        errors: list[str] = []
        required_files = ["00_namespace.yaml", "99_benchmark_client.yaml"] + [f"{name}.yaml" for name in self.conditions]
        if placement_strategy != "none":
            required_files.extend([
                f"99_benchmark_client_{sanitize_k8s_name_component(name)}.yaml"
                for name in self.conditions
            ])
        for file_name in required_files:
            path = GENERATED_DIR / file_name
            if not path.exists():
                errors.append(f"missing generated manifest: {file_name}")

        for condition in self.conditions:
            path = GENERATED_DIR / f"{condition}.yaml"
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                docs = [doc for doc in yaml.safe_load_all(handle) if doc]

            deployments = [doc for doc in docs if doc.get("kind") == "Deployment"]
            services = [doc for doc in docs if doc.get("kind") == "Service"]
            spec = self.condition_specs[condition]
            expected_deployments = int(spec["remote_service_count"])
            if len(deployments) != expected_deployments:
                errors.append(
                    f"{condition}: expected {expected_deployments} Deployment docs, found {len(deployments)}"
                )
                continue
            if len(services) != expected_deployments:
                errors.append(
                    f"{condition}: expected {expected_deployments} Service docs, found {len(services)}"
                )
                continue

            for doc in deployments:
                name = doc.get("metadata", {}).get("name", "<unknown>")
                container = doc["spec"]["template"]["spec"]["containers"][0]
                env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
                requests = container.get("resources", {}).get("requests", {})
                limits = container.get("resources", {}).get("limits", {})
                pod_spec = doc["spec"]["template"]["spec"]
                if str(container.get("image")) != str(k8s["image"]):
                    errors.append(f"{name}: expected image {k8s['image']}, found {container.get('image')}")
                if str(container.get("imagePullPolicy")) != str(k8s["image_pull_policy"]):
                    errors.append(
                        f"{name}: expected imagePullPolicy={k8s['image_pull_policy']}, found {container.get('imagePullPolicy')}"
                    )
                for key, expected in expected_env.items():
                    if env.get(key) != expected:
                        errors.append(f"{name}: expected {key}={expected}, found {env.get(key)}")
                if str(requests.get("cpu")) != str(resources["cpu_request"]):
                    errors.append(f"{name}: expected requests.cpu={resources['cpu_request']}, found {requests.get('cpu')}")
                if str(limits.get("cpu")) != str(resources["cpu_limit"]):
                    errors.append(f"{name}: expected limits.cpu={resources['cpu_limit']}, found {limits.get('cpu')}")
                if str(requests.get("memory")) != str(resources["memory_request"]):
                    errors.append(
                        f"{name}: expected requests.memory={resources['memory_request']}, found {requests.get('memory')}"
                    )
                if str(limits.get("memory")) != str(resources["memory_limit"]):
                    errors.append(
                        f"{name}: expected limits.memory={resources['memory_limit']}, found {limits.get('memory')}"
                    )
                if spec["type"] == "split":
                    command = container.get("command") or []
                    if command != ["python", "-m", "src.services.service_b_runner"]:
                        errors.append(
                            f"{name}: expected split command ['python', '-m', 'src.services.service_b_runner'], found {command}"
                        )
                    args = container.get("args") or []
                    split_after = str(condition_map[condition].get("split_after"))
                    if split_after not in args:
                        errors.append(f"{name}: missing split_after argument {split_after}")
                    if pod_spec.get("affinity"):
                        errors.append(f"{name}: split service deployment should not carry service-to-service affinity")

        client_path = GENERATED_DIR / "99_benchmark_client.yaml"
        if client_path.exists():
            with client_path.open("r", encoding="utf-8") as handle:
                client_doc = yaml.safe_load(handle)
            container = client_doc["spec"]["containers"][0]
            env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
            requests = container.get("resources", {}).get("requests", {})
            limits = container.get("resources", {}).get("limits", {})
            labels = client_doc.get("metadata", {}).get("labels", {})
            if str(container.get("image")) != str(k8s["image"]):
                errors.append(f"benchmark-client: expected image {k8s['image']}, found {container.get('image')}")
            if str(container.get("imagePullPolicy")) != str(k8s["image_pull_policy"]):
                errors.append(
                    f"benchmark-client: expected imagePullPolicy={k8s['image_pull_policy']}, found {container.get('imagePullPolicy')}"
                )
            for key, expected in expected_env.items():
                if env.get(key) != expected:
                    errors.append(f"benchmark-client: expected {key}={expected}, found {env.get(key)}")
            if str(requests.get("cpu")) != str(client_resources["cpu_request"]):
                errors.append(
                    f"benchmark-client: expected requests.cpu={client_resources['cpu_request']}, found {requests.get('cpu')}"
                )
            if str(limits.get("cpu")) != str(client_resources["cpu_limit"]):
                errors.append(
                    f"benchmark-client: expected limits.cpu={client_resources['cpu_limit']}, found {limits.get('cpu')}"
                )
            if str(requests.get("memory")) != str(client_resources["memory_request"]):
                errors.append(
                    f"benchmark-client: expected requests.memory={client_resources['memory_request']}, found {requests.get('memory')}"
                )
            if str(limits.get("memory")) != str(client_resources["memory_limit"]):
                errors.append(
                    f"benchmark-client: expected limits.memory={client_resources['memory_limit']}, found {limits.get('memory')}"
                )
            if labels.get("workload-role") != "client":
                errors.append("benchmark-client: expected metadata.labels.workload-role=client")

        if placement_strategy != "none":
            for condition in self.conditions:
                client_manifest_path = self.client_manifest_path(condition)
                if not client_manifest_path.exists():
                    continue
                with client_manifest_path.open("r", encoding="utf-8") as handle:
                    client_doc = yaml.safe_load(handle)
                labels = client_doc.get("metadata", {}).get("labels", {})
                pod_spec = client_doc.get("spec", {})
                if labels.get("condition") != condition:
                    errors.append(f"{client_manifest_path.name}: expected metadata.labels.condition={condition}")
                if labels.get("workload-role") != "client":
                    errors.append(f"{client_manifest_path.name}: expected metadata.labels.workload-role=client")

                if self.condition_specs[condition]["type"] != "split":
                    continue

                affinity = (pod_spec.get("affinity") or {}).get("podAffinity") or {}
                if placement_strategy == "strict_same_node":
                    terms = affinity.get("requiredDuringSchedulingIgnoredDuringExecution") or []
                    if len(terms) != 1:
                        errors.append(
                            f"{client_manifest_path.name}: expected one required podAffinity term for strict_same_node"
                        )
                        continue
                    match_labels = (terms[0].get("labelSelector") or {}).get("matchLabels") or {}
                else:
                    terms = affinity.get("preferredDuringSchedulingIgnoredDuringExecution") or []
                    if len(terms) != 1:
                        errors.append(
                            f"{client_manifest_path.name}: expected one preferred podAffinity term for prefer_same_node"
                        )
                        continue
                    match_labels = ((terms[0].get("podAffinityTerm") or {}).get("labelSelector") or {}).get("matchLabels") or {}

                if match_labels.get("condition") != condition:
                    errors.append(f"{client_manifest_path.name}: affinity must target condition={condition}")
                if match_labels.get("segment-index") != "1":
                    errors.append(f"{client_manifest_path.name}: affinity must target segment-index=1")
                if match_labels.get("workload-role") != "service":
                    errors.append(f"{client_manifest_path.name}: affinity must target workload-role=service")

        if errors:
            raise PipelineError("Generated manifest validation failed:\n- " + "\n- ".join(errors))

    def client_manifest_path(self, condition_name: str) -> Path:
        condition_specific = GENERATED_DIR / (
            f"99_benchmark_client_{sanitize_k8s_name_component(condition_name)}.yaml"
        )
        if condition_specific.exists():
            return condition_specific
        return GENERATED_DIR / "99_benchmark_client.yaml"

    def kubectl_text(self, args: list[str], *, check: bool = True) -> str:
        result = run_command(["kubectl", *args], capture_output=True, check=check)
        return (result.stdout or "").strip()

    def namespace_exists(self) -> bool:
        result = run_command(["kubectl", "get", "namespace", self.namespace], check=False, capture_output=True)
        return result.returncode == 0

    def wait_for_namespace_deletion(self, timeout_seconds: int = 180) -> None:
        deadline = time.monotonic() + timeout_seconds
        while self.namespace_exists():
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for namespace {self.namespace} to terminate")
            time.sleep(2)

    def cleanup_existing_namespace(self) -> None:
        if not self.namespace_exists():
            return
        log(f"Deleting existing namespace {self.namespace} to guarantee a clean rerun.")
        run_command(["kubectl", "delete", "namespace", self.namespace, "--wait=false"])
        self.wait_for_namespace_deletion()

    def deploy_base_resources(self) -> None:
        self.cleanup_existing_namespace()
        log("Applying namespace manifest.")
        run_command(["kubectl", "apply", "-f", str(GENERATED_DIR / "00_namespace.yaml")])
        self.state.resources_deployed = True

    def deploy_client_resources(self, condition_name: str) -> None:
        manifest_path = self.client_manifest_path(condition_name)
        log(f"Applying benchmark client pod manifest for {condition_name}.")
        run_command(["kubectl", "apply", "-f", str(manifest_path)])

    def wait_for_pod_exists(self, pod_name: str, timeout_seconds: int = 60) -> None:
        deadline = time.monotonic() + timeout_seconds
        while True:
            result = run_command(
                ["kubectl", "get", "pod", "-n", self.namespace, pod_name],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for pod {pod_name} to appear in namespace {self.namespace}")
            time.sleep(2)

    def wait_for_client_ready(self) -> None:
        self.wait_for_pod_exists(self.args.client_pod)
        log(f"Waiting for client pod {self.args.client_pod} to become Ready.")
        run_command(
            [
                "kubectl", "wait",
                "--for=condition=Ready",
                f"pod/{self.args.client_pod}",
                "-n", self.namespace,
                "--timeout=120s",
            ]
        )

    def condition_expected_remote_services(self, condition_name: str) -> int:
        spec = self.condition_specs.get(condition_name)
        if spec is None:
            raise PipelineError(f"Unknown condition: {condition_name}")
        return int(spec["remote_service_count"])

    def deploy_condition_resources(self, condition_name: str) -> None:
        expected_count = self.condition_expected_remote_services(condition_name)
        if expected_count == 0:
            log(f"Condition {condition_name} is client-only; no remote Kubernetes resources to deploy.")
            return
        manifest_path = GENERATED_DIR / f"{condition_name}.yaml"
        log(f"Applying {condition_name}.")
        run_command(["kubectl", "apply", "-f", str(manifest_path)])

    def wait_for_condition_ready(self, condition_name: str, expected_count: int) -> None:
        if expected_count == 0:
            return

        timeout_seconds = int(float(self.raw_config["kubernetes"]["readiness_timeout"])) + 60
        deadline = time.monotonic() + timeout_seconds
        deployment_names: list[str] = []

        while True:
            deployment_output = self.kubectl_text(
                [
                    "get", "deployments",
                    "-n", self.namespace,
                    "-l", f"condition={condition_name}",
                    "-o", "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
                ],
                check=False,
            )
            deployment_names = [line.strip() for line in deployment_output.splitlines() if line.strip()]
            if len(deployment_names) == expected_count:
                break
            if time.monotonic() >= deadline:
                raise PipelineError(
                    f"Timed out waiting for {expected_count} deployment objects for {condition_name}"
                )
            time.sleep(2)

        for deployment_name in deployment_names:
            log(f"Waiting for deployment {deployment_name} rollout.")
            run_command(
                [
                    "kubectl", "rollout", "status",
                    f"deployment/{deployment_name}",
                    "-n", self.namespace,
                    f"--timeout={timeout_seconds}s",
                ]
            )

        log(f"Waiting for condition {condition_name} pods to become Ready.")
        run_command(
            [
                "kubectl", "wait",
                "--for=condition=Ready",
                "pod",
                "-n", self.namespace,
                "-l", f"condition={condition_name}",
                f"--timeout={timeout_seconds}s",
            ]
        )

    def condition_resources_remaining(self, condition_name: str) -> bool:
        deployments = self.kubectl_text(
            [
                "get", "deployments",
                "-n", self.namespace,
                "-l", f"condition={condition_name},workload-role=service",
                "-o", "name",
            ],
            check=False,
        )
        pods = self.kubectl_text(
            [
                "get", "pods",
                "-n", self.namespace,
                "-l", f"condition={condition_name},workload-role=service",
                "-o", "name",
            ],
            check=False,
        )
        return bool(deployments.strip() or pods.strip())

    def wait_for_condition_removal(self, condition_name: str, timeout_seconds: int = 180) -> None:
        deadline = time.monotonic() + timeout_seconds
        while self.condition_resources_remaining(condition_name):
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for {condition_name} resources to terminate")
            time.sleep(2)

    def delete_condition_resources(self, condition_name: str) -> None:
        expected_count = self.condition_expected_remote_services(condition_name)
        if expected_count == 0:
            return
        manifest_path = GENERATED_DIR / f"{condition_name}.yaml"
        log(f"Deleting {condition_name} resources before the next rolling step.")
        run_command(["kubectl", "delete", "-f", str(manifest_path), "--ignore-not-found=true"], check=False)
        self.wait_for_condition_removal(condition_name)

    def delete_client_resources(self) -> None:
        log("Deleting benchmark client pod before the next rolling step.")
        run_command(
            [
                "kubectl", "delete", "pod",
                "-n", self.namespace,
                self.args.client_pod,
                "--ignore-not-found=true",
                "--wait=true",
            ],
            check=False,
        )

    def _service_pod_records(self, condition_name: str) -> list[dict[str, str]]:
        result = run_command(
            [
                "kubectl", "get", "pods",
                "-n", self.namespace,
                "-l", f"condition={condition_name},workload-role=service,segment-index=1",
                "-o", "json",
            ],
            capture_output=True,
        )
        payload = json.loads(result.stdout or "{}")
        records = []
        for item in payload.get("items", []):
            records.append({
                "pod_name": str(item.get("metadata", {}).get("name") or "unknown"),
                "node_name": str(item.get("spec", {}).get("nodeName") or "unknown"),
            })
        return records

    def validate_condition_placement(self, condition_name: str) -> dict[str, Any]:
        condition_dir = self.state.host_partial_results_dir / condition_name
        condition_dir.mkdir(parents=True, exist_ok=True)

        spec = self.condition_specs[condition_name]
        result: dict[str, Any] = {
            "condition": condition_name,
            "strategy": self.placement_policy.get("strategy") or "none",
            "checked": spec["type"] == "split" and str(self.placement_policy.get("strategy") or "none") != "none",
            "required": spec["type"] == "split" and bool(self.placement_policy.get("require_same_node")),
            "fail_if_not_colocated": bool(self.placement_policy.get("fail_if_not_colocated")),
            "status": "not_applicable",
            "colocated": None,
            "client_pod": self.args.client_pod,
            "client_node": "unknown",
            "service_pods": [],
            "service_nodes": [],
        }

        if spec["type"] == "split":
            client_node = self.kubectl_text(
                [
                    "get", "pod", self.args.client_pod,
                    "-n", self.namespace,
                    "-o", "jsonpath={.spec.nodeName}",
                ],
                check=False,
            ) or "unknown"
            service_pods = self._service_pod_records(condition_name)
            service_nodes = sorted(
                {
                    pod["node_name"]
                    for pod in service_pods
                    if pod.get("node_name") and pod["node_name"] != "unknown"
                }
            )
            colocated = (
                len(service_pods) == 1
                and client_node != "unknown"
                and len(service_nodes) == 1
                and client_node == service_nodes[0]
            )

            result.update({
                "client_node": client_node,
                "service_pods": service_pods,
                "service_nodes": service_nodes,
                "colocated": colocated,
                "status": "pass" if colocated else "fail",
            })

        placement_log_path = condition_dir / "placement_validation_host.json"
        with placement_log_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)

        if result["checked"] and result["status"] != "pass" and (
            result["required"] or result["fail_if_not_colocated"]
        ):
            raise PipelineError(
                f"Placement validation failed for {condition_name}: "
                f"client node {result['client_node']}, service nodes {result['service_nodes'] or ['unknown']}"
            )
        return result

    def write_file_into_pod(self, remote_path: str, content: str) -> None:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        code = (
            "import base64, pathlib, sys; "
            "path = pathlib.Path(sys.argv[2]); "
            "path.parent.mkdir(parents=True, exist_ok=True); "
            "path.write_bytes(base64.b64decode(sys.argv[1]))"
        )
        run_command(
            [
                "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                "python", "-c", code, encoded, remote_path,
            ]
        )

    def copy_effective_config_to_pod(self) -> None:
        log(f"Copying effective config into the client pod at {self.state.pod_config_path}.")
        content = self.state.effective_config_path.read_text(encoding="utf-8")
        self.write_file_into_pod(self.state.pod_config_path, content)

    def inject_runtime_metadata(self) -> None:
        log("Injecting live runtime metadata into the benchmark client pod.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py"),
                "--config", str(self.state.effective_config_path),
                "--namespace", self.namespace,
                "--client-pod", self.args.client_pod,
            ]
        )

    def condition_service_target(self, condition_name: str) -> tuple[str, str, str]:
        service_name = format_k8s_service_name(
            str(self.raw_config["kubernetes"]["service_name_template"]),
            condition_name,
            1,
        )
        service_host = f"{service_name}.{self.namespace}.svc.cluster.local"
        service_address = f"{service_host}:{int(self.raw_config['kubernetes']['grpc_port'])}"
        return service_name, service_host, service_address

    def copy_results_with_fallback(self, source_path: str, destination_path: Path) -> None:
        destination_parent = destination_path.parent
        destination_parent.mkdir(parents=True, exist_ok=True)
        if destination_path.exists():
            shutil.rmtree(destination_path)

        result = run_command(
            ["kubectl", "cp", f"{self.namespace}/{self.args.client_pod}:{source_path}", str(destination_path)],
            check=False,
        )
        if result.returncode == 0:
            return

        warn(f"kubectl cp failed for {source_path}; attempting a Python tar-stream fallback.")
        code = (
            "import os, sys, tarfile; "
            "source_path = os.path.abspath(sys.argv[1]); "
            "archive = tarfile.open(fileobj=sys.stdout.buffer, mode='w|'); "
            "archive.add(source_path, arcname=os.path.basename(source_path)); "
            "archive.close()"
        )
        process = subprocess.Popen(
            [
                "kubectl", "exec", "-i", "-n", self.namespace, self.args.client_pod, "--",
                "python", "-c", code, source_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            archive.extractall(path=destination_parent)
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
        if return_code != 0:
            raise PipelineError(
                f"kubectl tar-stream fallback failed for {source_path}: {stderr.strip() or return_code}"
            )

    def run_condition_benchmark(self, condition_name: str) -> None:
        condition_log_path = self.state.host_benchmark_log_dir / f"{condition_name}.log"
        pod_output_dir = f"{self.state.pod_partial_results_root}/{condition_name}"
        host_condition_results_dir = self.state.host_partial_results_dir / condition_name

        self.copy_effective_config_to_pod()
        self.inject_runtime_metadata()

        log(f"Running the in-cluster RQ1.1 benchmark for {condition_name}.")
        run_command(
            [
                "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                "rm", "-rf", pod_output_dir,
            ],
            check=False,
        )

        command = [
            "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
            "python", "-m", "src.benchmark.k8s_split_experiment",
            "--config", self.state.pod_config_path,
            "--condition", condition_name,
            "--output-dir", pod_output_dir,
        ]
        if self.condition_expected_remote_services(condition_name) > 0:
            _, service_host, _ = self.condition_service_target(condition_name)
            command.extend([
                "--grpc-host", service_host,
                "--grpc-port", str(int(self.raw_config["kubernetes"]["grpc_port"])),
            ])

        stream_command(command, condition_log_path)

        run_command(
            [
                "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                "test", "-d", pod_output_dir,
            ]
        )
        log(f"Copying results for {condition_name} from pod path {pod_output_dir}.")
        self.copy_results_with_fallback(pod_output_dir, host_condition_results_dir)
        run_command(
            [
                "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                "rm", "-rf", pod_output_dir,
            ],
            check=False,
        )

    def merge_results(self) -> None:
        log(f"Merging per-condition artifacts into {self.state.merged_results_dir}.")
        self.state.merged_results_dir.mkdir(parents=True, exist_ok=True)

        fieldnames: list[str] | None = None
        rows: list[dict[str, Any]] = []
        local_validation: dict[str, Any] = {}
        grpc_validation: dict[str, Any] = {}
        warmup_calibration: dict[str, Any] = {}
        deployment_metadata: dict[str, Any] = {}
        environment: dict[str, Any] | None = None

        for condition in self.conditions:
            condition_dir = self.state.host_partial_results_dir / condition
            if not condition_dir.is_dir():
                raise PipelineError(f"Missing partial results directory: {condition_dir}")

            raw_path = condition_dir / "raw_iterations.csv"
            parity_path = condition_dir / "parity_validation.json"
            warmup_path = condition_dir / "warmup_calibration.json"
            deployment_path = condition_dir / "deployment_metadata.json"
            environment_path = condition_dir / "environment.json"

            with raw_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                elif reader.fieldnames != fieldnames:
                    raise PipelineError(
                        f"raw_iterations.csv header mismatch for {condition}: {reader.fieldnames} != {fieldnames}"
                    )
                rows.extend(list(reader))

            with parity_path.open("r", encoding="utf-8") as handle:
                parity = json.load(handle)
            local_validation.update(parity.get("local_validation", {}))
            grpc_validation.update(parity.get("grpc_validation", {}))

            with warmup_path.open("r", encoding="utf-8") as handle:
                warmup_calibration.update(json.load(handle))

            with deployment_path.open("r", encoding="utf-8") as handle:
                deployment_metadata.update(json.load(handle))

            if environment is None:
                with environment_path.open("r", encoding="utf-8") as handle:
                    environment = json.load(handle)

        if not rows or fieldnames is None:
            raise PipelineError("Merge failed: no raw iterations were collected")

        raw_output_path = self.state.merged_results_dir / "raw_iterations.csv"
        with raw_output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        shutil.copy2(self.state.effective_config_path, self.state.merged_results_dir / "config.yaml")
        resolved_config = asdict(load_config(str(self.state.effective_config_path)))
        with (self.state.merged_results_dir / "resolved_config.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "source_config_path": str(self.state.effective_config_path.resolve()),
                    "resolved_config": resolved_config,
                },
                handle,
                indent=2,
            )

        if environment is None:
            environment = {}
        deployment_section = build_environment_deployment_section(deployment_metadata)
        if deployment_section:
            environment["deployment"] = deployment_section
        environment["rolling_orchestration"] = {
            "enabled": True,
            "deployment_target": "aks",
            "benchmark_mode": "rq1_1_split",
            "conditions": self.conditions,
            "remote_service_counts": {
                condition: self.condition_expected_remote_services(condition)
                for condition in self.conditions
            },
            "partial_results_root": str(self.state.host_partial_results_dir.resolve()),
            "teardown_between_conditions": True,
        }
        with (self.state.merged_results_dir / "environment.json").open("w", encoding="utf-8") as handle:
            json.dump(environment, handle, indent=2)
        with (self.state.merged_results_dir / "parity_validation.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "local_validation": local_validation,
                    "grpc_validation": grpc_validation,
                },
                handle,
                indent=2,
            )
        with (self.state.merged_results_dir / "warmup_calibration.json").open("w", encoding="utf-8") as handle:
            json.dump(warmup_calibration, handle, indent=2)
        with (self.state.merged_results_dir / "deployment_metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(deployment_metadata, handle, indent=2)

        self.state.final_results_dir = self.state.merged_results_dir

    def run_host_analysis(self) -> None:
        if self.state.final_results_dir is None:
            raise PipelineError("No merged results directory is available for analysis")
        log("Running host-side analysis on merged RQ1.1 Azure results.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "run_analysis.py"),
                str(self.state.final_results_dir),
            ]
        )

    def run_rolling_benchmark(self) -> None:
        self.deploy_base_resources()

        for condition_name in self.conditions:
            expected_services = self.condition_expected_remote_services(condition_name)
            self.deploy_condition_resources(condition_name)
            self.wait_for_condition_ready(condition_name, expected_services)
            self.deploy_client_resources(condition_name)
            self.wait_for_client_ready()
            self.validate_condition_placement(condition_name)
            self.run_condition_benchmark(condition_name)
            self.delete_client_resources()
            self.delete_condition_resources(condition_name)

        self.merge_results()
        self.run_host_analysis()

    def gather_diagnostics(self) -> None:
        if not self.namespace_exists():
            warn(f"Namespace {self.namespace} no longer exists; skipping cluster diagnostics.")
            return
        log(f"Gathering Kubernetes diagnostics under {self.state.diagnostics_dir}.")
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        with (self.state.diagnostics_dir / "kubectl_get_pods.txt").open("w", encoding="utf-8") as handle:
            result = run_command(["kubectl", "get", "pods", "-n", self.namespace, "-o", "wide"], capture_output=True)
            handle.write(result.stdout or "")
        with (self.state.diagnostics_dir / "kubectl_get_svc.txt").open("w", encoding="utf-8") as handle:
            result = run_command(["kubectl", "get", "svc", "-n", self.namespace], capture_output=True)
            handle.write(result.stdout or "")

        pod_names = self.kubectl_text(
            [
                "get", "pods",
                "-n", self.namespace,
                "-o", "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
            ],
            check=False,
        )
        for pod_name in [name.strip() for name in pod_names.splitlines() if name.strip()]:
            describe_path = self.state.diagnostics_dir / f"{pod_name}.describe.txt"
            logs_path = self.state.diagnostics_dir / f"{pod_name}.log.txt"
            with describe_path.open("w", encoding="utf-8") as handle:
                result = run_command(
                    ["kubectl", "describe", "pod", "-n", self.namespace, pod_name],
                    capture_output=True,
                    check=False,
                )
                handle.write((result.stdout or "") + (result.stderr or ""))
            with logs_path.open("w", encoding="utf-8") as handle:
                result = run_command(
                    ["kubectl", "logs", "-n", self.namespace, pod_name, "--tail=200"],
                    capture_output=True,
                    check=False,
                )
                handle.write((result.stdout or "") + (result.stderr or ""))

    def cleanup_namespace(self) -> None:
        if not self.state.resources_deployed:
            return
        log("Cleaning up benchmark resources in reverse deployment order.")
        run_command(
            ["kubectl", "delete", "pod", "-n", self.namespace, self.args.client_pod, "--ignore-not-found=true"],
            check=False,
        )
        for condition_name in reversed(self.conditions):
            if self.condition_expected_remote_services(condition_name) == 0:
                continue
            run_command(
                ["kubectl", "delete", "-f", str(GENERATED_DIR / f"{condition_name}.yaml"), "--ignore-not-found=true"],
                check=False,
            )
        run_command(
            ["kubectl", "delete", "namespace", self.namespace, "--ignore-not-found=true", "--wait=false"],
            check=False,
        )
        if self.namespace_exists():
            self.wait_for_namespace_deletion()
        self.state.resources_deployed = False

    def destroy_infrastructure(self) -> None:
        if not self.state.infra_provisioned:
            return
        self.destroy_with_terraform()
        self.state.infra_provisioned = False

    def handle_failure(self) -> None:
        if self.state.resources_deployed:
            try:
                self.gather_diagnostics()
            except Exception as exc:  # pragma: no cover - diagnostic best effort
                warn(f"Failed to gather diagnostics: {exc}")

        if self.args.keep_infra:
            if self.state.resources_deployed:
                warn(f"Preserving namespace {self.namespace} for inspection.")
            if self.state.infra_provisioned:
                warn("Preserving Terraform-managed Azure resources for inspection.")
            warn(f"Run failed. Host artifacts directory: {self.state.host_export_dir}")
            return

        if self.state.resources_deployed:
            try:
                self.cleanup_namespace()
            except Exception as exc:  # pragma: no cover - cleanup best effort
                warn(f"Failed to clean up the namespace after an error: {exc}")
        if self.state.infra_provisioned:
            try:
                self.destroy_infrastructure()
            except Exception as exc:  # pragma: no cover - cleanup best effort
                warn(f"Failed to destroy Terraform-managed infrastructure after an error: {exc}")
        warn(f"Run failed. Host artifacts directory: {self.state.host_export_dir}")

    def run(self) -> None:
        self.prepare_artifact_dirs()
        self.verify_required_files()
        self.verify_host_prerequisites()
        self.maybe_provision_cluster()
        self.refresh_cluster_context()
        self.write_effective_config()
        self.validate_effective_config(require_pinned_image=False)
        self.load_conditions()
        self.run_cluster_preflight()
        self.effective_image_ref = self.resolve_image_reference()
        self.write_effective_config(self.effective_image_ref)
        self.validate_effective_config(require_pinned_image=True)
        self.generate_manifests()
        self.validate_generated_manifests()
        self.run_rolling_benchmark()
        if not self.args.keep_infra:
            self.cleanup_namespace()
            self.destroy_infrastructure()
        if self.state.final_results_dir is None:
            raise PipelineError("Run completed without a final results directory")
        log(
            "RQ1.1 Azure fully controlled run finished successfully. "
            f"Final results directory: {self.state.final_results_dir}"
        )


def main() -> int:
    args = parse_args()
    orchestrator = RQ11AzureOrchestrator(args)
    try:
        orchestrator.run()
    except Exception as exc:
        orchestrator.handle_failure()
        print(f"[{timestamp()}] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())