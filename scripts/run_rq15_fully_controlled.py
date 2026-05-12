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

from src.benchmark.config import load_config
from src.benchmark.deployment_metadata import (
    build_environment_deployment_section,
    validate_multi_node_placement,
)


DEFAULT_CONFIG_REL = "configs/rq1/1.5/rq1_5_full.yaml"
DEFAULT_CLIENT_POD = "benchmark-client"
DEFAULT_NODEPOOL = "rq15pool"
DEFAULT_RESOURCE_GROUP = "rg-thesis-rq15"
DEFAULT_CLUSTER_NAME = "thesis-rq15"
DEFAULT_LOCATION = "swedencentral"
DEFAULT_NODE_VM_SIZE = "Standard_D8s_v3"
DEFAULT_NODE_COUNT = 1
GENERATED_DIR = REPO_ROOT / "k8s" / "aks" / "generated"
INFRA_DIR = REPO_ROOT / "infra"


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


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def log(message: str) -> None:
    print(f"[{timestamp()}] {message}")


def warn(message: str) -> None:
    print(f"[{timestamp()}] WARN: {message}", file=sys.stderr)


def ensure_command(command_name: str) -> None:
    if shutil.which(command_name) is None:
        raise PipelineError(f"Required command not found: {command_name}")


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
    text: bool = True,
) -> subprocess.CompletedProcess:
    resolved_args = list(args)
    executable = shutil.which(resolved_args[0])
    if executable:
        resolved_args[0] = executable
    result = subprocess.run(
        resolved_args,
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
    resolved_args = list(args)
    executable = shutil.which(resolved_args[0])
    if executable:
        resolved_args[0] = executable
    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            resolved_args,
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
            "Provision, deploy, benchmark, and export the thesis-facing RQ1.5 "
            "AKS experiment in rolling mode."
        )
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_REL, help="Source experiment config YAML")
    parser.add_argument(
        "--results-root",
        default=str(REPO_ROOT / "results"),
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
        default="/tmp/rq15_effective_config.yaml",
        help="Path inside the client pod where the effective config is copied",
    )
    parser.add_argument(
        "--nodepool",
        default=DEFAULT_NODEPOOL,
        help="AKS nodepool label used for preflight and manifest generation",
    )
    parser.add_argument(
        "--provisioner",
        choices=["terraform", "az"],
        default="terraform",
        help="Provisioning backend used when --provision is enabled (default: terraform)",
    )
    parser.add_argument(
        "--provision",
        action="store_true",
        help="Create or reuse the resource group, ACR, AKS cluster, and kubeconfig before the run",
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
        "--image-ref",
        default=None,
        help="Existing pinned image reference to use for this run, e.g. <acr>.azurecr.io/thesis-inference@sha256:<digest>.",
    )
    parser.add_argument(
        "--acr-name",
        default=None,
        help="ACR name without the .azurecr.io suffix. Derived from kubernetes.image when omitted.",
    )
    parser.add_argument(
        "--image-tag",
        default=f"rq15-{utc_run_stamp().lower()}",
        help="Tag to push when --push is used",
    )
    parser.add_argument(
        "--local-image",
        default="thesis-inference:latest",
        help="Local Docker image to tag and push",
    )
    parser.add_argument("--resource-group", default=DEFAULT_RESOURCE_GROUP, help="Azure resource group name")
    parser.add_argument("--cluster-name", default=DEFAULT_CLUSTER_NAME, help="AKS cluster name")
    parser.add_argument(
        "--skip-kubeconfig-refresh",
        action="store_true",
        help="Use the current kubectl context as-is instead of refreshing credentials for --cluster-name.",
    )
    parser.add_argument(
        "--resume-artifact-dir",
        default=None,
        help=(
            "Reuse an existing RQ1.5 export directory. Complete per-condition "
            "partials are skipped; incomplete partials are rerun and then merged."
        ),
    )
    parser.add_argument(
        "--condition-retries",
        type=int,
        default=1,
        help="Retry an individual rolling condition when copied artifacts are incomplete.",
    )
    parser.add_argument("--location", default=DEFAULT_LOCATION, help="Azure region for provisioning")
    parser.add_argument("--node-count", type=int, default=DEFAULT_NODE_COUNT, help="Node count for AKS provisioning")
    parser.add_argument(
        "--node-vm-size",
        default=DEFAULT_NODE_VM_SIZE,
        help="VM SKU used when provisioning the AKS cluster",
    )
    parser.add_argument(
        "--cleanup-on-failure",
        action="store_true",
        help="Delete the RQ1.5 namespace if the run fails after resources were deployed",
    )
    parser.add_argument(
        "--delete-aks-on-success",
        action="store_true",
        help="Delete the AKS cluster after a successful run",
    )
    parser.add_argument(
        "--delete-resource-group-on-success",
        action="store_true",
        help="Delete the entire resource group after a successful run",
    )
    parser.add_argument(
        "--delete-resource-group-on-failure",
        action="store_true",
        help=(
            "Delete the entire resource group on failure. Bounds Azure cost when "
            "the orchestrator dies mid-run with --provision."
        ),
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the fail-closed cluster preflight. Not recommended for thesis-facing runs.",
    )
    args = parser.parse_args()

    if args.build and not args.push:
        parser.error("--build requires --push")
    if args.image_ref and (args.push or args.build):
        parser.error("--image-ref cannot be combined with --push/--build")
    if args.delete_aks_on_success and args.provisioner == "terraform":
        parser.error(
            "--delete-aks-on-success is not supported with --provisioner terraform because it would leave Terraform state inconsistent; "
            "use --delete-resource-group-on-success instead"
        )
    if args.delete_resource_group_on_success and not args.provision:
        warn(
            "--delete-resource-group-on-success is enabled without --provision; "
            "the script will still delete the named group after a successful run."
        )
    if args.delete_resource_group_on_failure and not args.provision:
        warn(
            "--delete-resource-group-on-failure is enabled without --provision; "
            "the script will still delete the named group if a failure occurs."
        )
    if args.condition_retries < 0:
        parser.error("--condition-retries must be >= 0")
    return args


class RQ15Orchestrator:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))
        self.repo_root = REPO_ROOT
        self.infra_dir = INFRA_DIR
        self.source_config_path = (self.repo_root / args.config).resolve()
        self.source_config_rel = self.source_config_path.relative_to(self.repo_root)
        self.run_ts = utc_run_stamp()

        # Read placement strategy before computing the export dir so the
        # output folder name reflects single-node vs multi-node mode.
        self.raw_config = self._load_raw_config(self.source_config_path)
        placement_raw = (self.raw_config.get("kubernetes") or {}).get("placement") or {}
        self.placement_strategy = str(placement_raw.get("strategy") or "none")
        self.is_multinode = self.placement_strategy == "multi_node_anti_affinity"

        # Distinct folder prefix per mode keeps RQ1.5 and RQ1.5b artifacts
        # immediately distinguishable on disk.
        self.experiment_signature = (
            "rq1_5b_multinode" if self.is_multinode else "rq1_5_fully_controlled"
        )
        host_export_dir = (
            Path(args.resume_artifact_dir).resolve()
            if args.resume_artifact_dir
            else Path(args.results_root).resolve() / f"{self.experiment_signature}_{self.run_ts}"
        )
        self.state = RunnerState(
            host_export_dir=host_export_dir,
            diagnostics_dir=host_export_dir / "diagnostics",
            host_partial_results_dir=host_export_dir / "partial_results",
            host_benchmark_log_dir=host_export_dir / "condition_logs",
            merged_results_dir=host_export_dir / "merged_results",
            effective_config_path=host_export_dir / "effective_config.yaml",
            pod_partial_results_root=f"/tmp/{self.experiment_signature}_rolling_{self.run_ts}",
            pod_config_path=args.pod_config_path,
        )
        self.namespace = args.namespace or str(self.raw_config["kubernetes"]["namespace"])
        self.conditions: list[str] = []
        self.acr_name = (
            args.acr_name
            or self._derive_acr_name_from_image_ref(args.image_ref)
            or self._derive_acr_name_from_config()
        )
        self.effective_image_ref = ""
        self.current_context = ""
        self.terraform_outputs: dict[str, Any] = {}
        self._existing_acr_resource_group: str | None = None
        self._resource_group_exists: bool | None = None

        config_min_nodes = placement_raw.get("min_nodes")
        if (
            self.is_multinode
            and args.node_count == DEFAULT_NODE_COUNT
            and config_min_nodes not in (None, "")
        ):
            try:
                args.node_count = int(config_min_nodes)
            except (TypeError, ValueError):
                pass

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

    def _derive_acr_name_from_config(self) -> str | None:
        image = str(self.raw_config.get("kubernetes", {}).get("image", "")).strip()
        return self._derive_acr_name_from_image_ref(image)

    def _derive_acr_name_from_image_ref(self, image: str | None) -> str | None:
        if not image:
            return None
        image = str(image).strip()
        match = re.match(r"^([a-zA-Z0-9]+)\.azurecr\.io/", image)
        return match.group(1) if match else None

    def prepare_artifact_dirs(self) -> None:
        if self.args.resume_artifact_dir and not self.state.host_export_dir.is_dir():
            raise PipelineError(f"--resume-artifact-dir does not exist: {self.state.host_export_dir}")
        self.state.host_export_dir.mkdir(parents=True, exist_ok=True)
        self.state.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self.state.host_partial_results_dir.mkdir(parents=True, exist_ok=True)
        self.state.host_benchmark_log_dir.mkdir(parents=True, exist_ok=True)

    def verify_required_files(self) -> None:
        required_paths = [
            self.source_config_path,
            self.repo_root / "run_k8s_experiment.py",
            self.repo_root / "run_analysis.py",
            self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py",
            self.repo_root / "scripts" / "preflight_rq15_full.py",
            self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py",
        ]
        if self.args.provision and self.args.provisioner == "terraform":
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
        if not self.args.skip_kubeconfig_refresh:
            ensure_command("az")
        if self.args.push:
            ensure_command("docker")
            ensure_command("az")
        if self.args.provisioner == "terraform" and (self.args.provision or self.args.delete_resource_group_on_success):
            ensure_command("terraform")
            ensure_command("az")
        if self.args.provisioner == "az" and (self.args.provision or self.args.delete_aks_on_success or self.args.delete_resource_group_on_success):
            ensure_command("az")
        require_python_modules(["yaml", "scipy", "matplotlib"])

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
        return bool(self.args.image_ref)

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
        else:
            self._terraform_state_rm_if_present(
                [
                    "azurerm_kubernetes_cluster.rq15",
                    "azurerm_kubernetes_cluster_node_pool.benchmark[0]",
                    "azurerm_role_assignment.aks_acr_pull",
                ],
                state_addresses,
            )

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
        self.prepare_terraform_state()
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

    def ensure_resource_group(self) -> None:
        log(f"Ensuring resource group {self.args.resource_group} in {self.args.location}.")
        run_command(
            [
                "az", "group", "create",
                "--name", self.args.resource_group,
                "--location", self.args.location,
            ]
        )

    def ensure_acr(self) -> None:
        if not self.acr_name:
            raise PipelineError("ACR name is required for provisioning or pushing an image")

        show = run_command(
            [
                "az", "acr", "show",
                "--resource-group", self.args.resource_group,
                "--name", self.acr_name,
            ],
            capture_output=True,
            check=False,
        )
        if show.returncode == 0:
            log(f"Using existing ACR {self.acr_name}.")
            return

        log(f"Creating ACR {self.acr_name}.")
        run_command(
            [
                "az", "acr", "create",
                "--resource-group", self.args.resource_group,
                "--name", self.acr_name,
                "--sku", "Basic",
                "--location", self.args.location,
            ]
        )

    def ensure_cluster(self) -> None:
        if not self.acr_name:
            raise PipelineError("ACR name is required when provisioning the AKS cluster")

        show = run_command(
            [
                "az", "aks", "show",
                "--resource-group", self.args.resource_group,
                "--name", self.args.cluster_name,
            ],
            capture_output=True,
            check=False,
        )
        if show.returncode != 0:
            log(
                "Creating AKS cluster "
                f"{self.args.cluster_name} with nodepool {self.args.nodepool} "
                f"({self.args.node_vm_size}, count={self.args.node_count})."
            )
            run_command(
                [
                    "az", "aks", "create",
                    "--resource-group", self.args.resource_group,
                    "--name", self.args.cluster_name,
                    "--node-count", str(self.args.node_count),
                    "--node-vm-size", self.args.node_vm_size,
                    "--nodepool-name", self.args.nodepool,
                    "--attach-acr", self.acr_name,
                    "--generate-ssh-keys",
                ]
            )
        else:
            cluster = json.loads(show.stdout or "{}")
            nodepool = self._extract_nodepool_profile(cluster)
            actual_vm_size = str(nodepool.get("vmSize", "unknown"))
            actual_count = int(nodepool.get("count", 0))
            if actual_vm_size != self.args.node_vm_size or actual_count != self.args.node_count:
                raise PipelineError(
                    "Existing AKS cluster does not match the thesis-facing full-run requirements. "
                    f"Nodepool {self.args.nodepool} is {actual_vm_size} x{actual_count}, "
                    f"but this run requested {self.args.node_vm_size} x{self.args.node_count}. "
                    "Delete and recreate the cluster with the required nodepool, or rerun with explicit "
                    "flags that match the existing cluster if you only intend to inspect it."
                )
            log(f"Using existing AKS cluster {self.args.cluster_name}.")
            log(f"Ensuring ACR pull attachment for {self.acr_name}.")
            run_command(
                [
                    "az", "aks", "update",
                    "--resource-group", self.args.resource_group,
                    "--name", self.args.cluster_name,
                    "--attach-acr", self.acr_name,
                ]
            )

        self.refresh_kubeconfig()

    def _extract_nodepool_profile(self, cluster: dict[str, Any]) -> dict[str, Any]:
        for nodepool in cluster.get("agentPoolProfiles", []):
            if nodepool.get("name") == self.args.nodepool:
                return nodepool
        raise PipelineError(
            f"AKS cluster {self.args.cluster_name} does not contain nodepool {self.args.nodepool}"
        )

    def maybe_provision_cluster(self) -> None:
        if not self.args.provision:
            return
        if self.args.provisioner == "terraform":
            self.provision_with_terraform()
            return
        self.azure_quota_preflight()
        self.ensure_resource_group()
        self.ensure_acr()
        self.ensure_cluster()

    def resolve_image_reference(self) -> str:
        configured_image = str(self.raw_config.get("kubernetes", {}).get("image", "")).strip()
        if self.args.image_ref:
            if "@sha256:" not in self.args.image_ref:
                raise PipelineError("--image-ref must be pinned with @sha256:<digest>")
            log(f"Using pinned image from --image-ref: {self.args.image_ref}")
            return self.args.image_ref

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
        service = k8s.get("resources") or {}
        client = k8s.get("client_resources") or service
        threading = (raw.get("cpu_stabilisation") or {}).get("threading") or {}
        errors: list[str] = []

        image = str(k8s.get("image", ""))
        if require_pinned_image and "@sha256:" not in image:
            errors.append("kubernetes.image must be a pinned digest reference for the thesis-facing run")
        if str(k8s.get("image_pull_policy", "")) != "Always":
            errors.append("kubernetes.image_pull_policy must be Always for the thesis-facing run")

        for label, resources in (("service", service), ("client", client)):
            if str(resources.get("cpu_request")) != str(resources.get("cpu_limit")):
                errors.append(f"{label} cpu_request must equal cpu_limit for fully controlled QoS")
            if str(resources.get("memory_request")) != str(resources.get("memory_limit")):
                errors.append(f"{label} memory_request must equal memory_limit for fully controlled QoS")

        if not re.fullmatch(r"[0-9]+", str(service.get("cpu_request", ""))):
            errors.append("service cpu_request must be an integer core value for the thesis-facing run")

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

        if errors:
            raise PipelineError("Effective config validation failed:\n- " + "\n- ".join(errors))

    def load_conditions(self) -> None:
        config = load_config(str(self.state.effective_config_path))
        self.conditions = [condition.name for condition in config.conditions]
        if not self.conditions:
            raise PipelineError("No conditions were found in the effective config")

    def run_cluster_preflight(self) -> None:
        if self.args.skip_preflight:
            warn("Skipping scripts/preflight_rq15_full.py at user request.")
            return

        log("Running fail-closed cluster preflight for the rolling thesis-facing profile.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "scripts" / "preflight_rq15_full.py"),
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
        log("Validating generated manifests against the effective full-run config.")
        with self.state.effective_config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)

        threading = raw["cpu_stabilisation"]["threading"]
        k8s = raw["kubernetes"]
        resources = k8s["resources"]
        client_resources = k8s["client_resources"]
        expected_env = {
            "PYTORCH_INTRA_OP_THREADS": str(threading["pytorch_intra_op"]),
            "PYTORCH_INTER_OP_THREADS": str(threading["pytorch_inter_op"]),
            "OMP_NUM_THREADS": str(threading["omp_num_threads"]),
            "MKL_NUM_THREADS": str(threading["mkl_num_threads"]),
            "OPENBLAS_NUM_THREADS": str(threading["openblas_num_threads"]),
        }
        condition_to_services = {
            cond["name"]: len(cond.get("chain_split_points") or []) + 1
            for cond in raw["conditions"]
        }

        errors: list[str] = []
        required_files = ["00_namespace.yaml", "99_benchmark_client.yaml"] + [f"{name}.yaml" for name in self.conditions]
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
            expected_deployments = condition_to_services[condition]
            if len(deployments) != expected_deployments:
                errors.append(
                    f"{condition}: expected {expected_deployments} Deployment docs, found {len(deployments)}"
                )
                continue
            for doc in deployments:
                name = doc.get("metadata", {}).get("name", "<unknown>")
                container = doc["spec"]["template"]["spec"]["containers"][0]
                env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
                requests = container.get("resources", {}).get("requests", {})
                limits = container.get("resources", {}).get("limits", {})
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

        client_path = GENERATED_DIR / "99_benchmark_client.yaml"
        if client_path.exists():
            with client_path.open("r", encoding="utf-8") as handle:
                client_doc = yaml.safe_load(handle)
            container = client_doc["spec"]["containers"][0]
            env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
            requests = container.get("resources", {}).get("requests", {})
            limits = container.get("resources", {}).get("limits", {})
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

        if errors:
            raise PipelineError("Generated manifest validation failed:\n- " + "\n- ".join(errors))

    def kubectl_text(self, args: list[str], *, check: bool = True) -> str:
        result = run_command(["kubectl", *args], capture_output=True, check=check)
        return (result.stdout or "").strip()

    def namespace_exists(self) -> bool:
        result = run_command(["kubectl", "get", "namespace", self.namespace], check=False, capture_output=True)
        return result.returncode == 0

    def refresh_cluster_context(self, *, retry_seconds: int = 180, retry_interval: int = 10) -> None:
        self.current_context = self.kubectl_text(["config", "current-context"])
        log(f"Kubernetes context: {self.current_context}")
        # After fresh provisioning the AKS API server DNS name may take up to a few
        # minutes to become resolvable from WSL2's internal DNS resolver.  Retry with
        # backoff rather than failing immediately.
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
        log("Applying benchmark client pod manifest.")
        run_command(["kubectl", "apply", "-f", str(GENERATED_DIR / "99_benchmark_client.yaml")])

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

    def deploy_condition_resources(self, condition_name: str) -> None:
        manifest_path = GENERATED_DIR / f"{condition_name}.yaml"
        log(f"Applying {condition_name}.")
        run_command(["kubectl", "apply", "-f", str(manifest_path)])

    def condition_expected_pods(self, condition_name: str) -> int:
        if condition_name == "monolithic_k8s_1svc":
            return 1
        match = re.fullmatch(r"chain_([0-9]+)svc", condition_name)
        if not match:
            raise PipelineError(f"Cannot infer expected pod count for condition {condition_name}")
        return int(match.group(1))

    def wait_for_condition_ready(self, condition_name: str, expected_count: int) -> None:
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
                "-l", f"condition={condition_name}",
                "-o", "name",
            ],
            check=False,
        )
        pods = self.kubectl_text(
            [
                "get", "pods",
                "-n", self.namespace,
                "-l", f"condition={condition_name}",
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
        manifest_path = GENERATED_DIR / f"{condition_name}.yaml"
        log(f"Deleting {condition_name} resources before the next rolling step.")
        run_command(["kubectl", "delete", "-f", str(manifest_path), "--ignore-not-found=true"], check=False)
        self.wait_for_condition_removal(condition_name)

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

    def expected_rows_per_condition(self) -> int:
        benchmark = self.raw_config.get("benchmark") or {}
        try:
            rounds = int(benchmark["rounds"])
            measured_iterations = int(benchmark["measured_iterations"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineError(
                "Cannot determine expected per-condition row count from benchmark.rounds "
                "and benchmark.measured_iterations"
            ) from exc
        return rounds * measured_iterations

    def raw_iteration_row_count(self, raw_path: Path) -> int:
        with raw_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return 0
            return sum(1 for _ in reader)

    def validate_condition_artifacts(self, condition_name: str, condition_dir: Path) -> list[str]:
        errors: list[str] = []
        if not condition_dir.is_dir():
            return [f"missing partial results directory: {condition_dir}"]

        required_files = [
            "raw_iterations.csv",
            "parity_validation.json",
            "warmup_calibration.json",
            "deployment_metadata.json",
            "environment.json",
        ]
        for file_name in required_files:
            path = condition_dir / file_name
            if not path.is_file():
                errors.append(f"missing {file_name}")

        raw_path = condition_dir / "raw_iterations.csv"
        if raw_path.is_file():
            expected_rows = self.expected_rows_per_condition()
            try:
                actual_rows = self.raw_iteration_row_count(raw_path)
            except Exception as exc:
                errors.append(f"could not read raw_iterations.csv: {exc}")
            else:
                if actual_rows != expected_rows:
                    errors.append(
                        f"raw_iterations.csv has {actual_rows} rows; expected {expected_rows}"
                    )

        return errors

    def run_condition_benchmark(self, condition_name: str) -> None:
        condition_log_path = self.state.host_benchmark_log_dir / f"{condition_name}.log"
        pod_output_dir = f"{self.state.pod_partial_results_root}/{condition_name}"
        host_condition_results_dir = self.state.host_partial_results_dir / condition_name

        self.copy_effective_config_to_pod()
        self.inject_runtime_metadata()

        max_attempts = self.args.condition_retries + 1
        last_errors: list[str] = []
        last_exception: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            attempt_suffix = f" (attempt {attempt}/{max_attempts})" if max_attempts > 1 else ""
            attempt_log_path = (
                condition_log_path
                if attempt == 1
                else self.state.host_benchmark_log_dir / f"{condition_name}.attempt{attempt}.log"
            )
            log(f"Running the in-cluster rolling benchmark for {condition_name}{attempt_suffix}.")
            run_command(
                [
                    "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                    "rm", "-rf", pod_output_dir,
                ],
                check=False,
            )

            try:
                stream_command(
                    [
                        "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                        "python", "run_k8s_experiment.py",
                        "--config", self.state.pod_config_path,
                        "--condition", condition_name,
                        "--output-dir", pod_output_dir,
                    ],
                    attempt_log_path,
                )

                run_command(
                    [
                        "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                        "test", "-d", pod_output_dir,
                    ]
                )
                log(f"Copying rolling results for {condition_name} from pod path {pod_output_dir}.")
                self.copy_results_with_fallback(pod_output_dir, host_condition_results_dir)
                last_errors = self.validate_condition_artifacts(condition_name, host_condition_results_dir)
                if not last_errors:
                    run_command(
                        [
                            "kubectl", "exec", "-n", self.namespace, self.args.client_pod, "--",
                            "rm", "-rf", pod_output_dir,
                        ],
                        check=False,
                    )
                    return
                warn(
                    f"{condition_name} artifacts are incomplete after attempt {attempt}: "
                    + "; ".join(last_errors)
                )
            except Exception as exc:
                last_exception = exc
                warn(f"{condition_name} attempt {attempt} failed: {exc}")

            if attempt < max_attempts:
                log(f"Retrying {condition_name} before tearing down condition resources.")

        details = "; ".join(last_errors) if last_errors else str(last_exception or "unknown error")
        raise PipelineError(
            f"{condition_name} did not produce a complete partial result after {max_attempts} attempt(s): {details}"
        )

    def merge_rolling_results(self) -> None:
        log(f"Merging rolling per-condition artifacts into {self.state.merged_results_dir}.")
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
            artifact_errors = self.validate_condition_artifacts(condition, condition_dir)
            if artifact_errors:
                raise PipelineError(
                    f"Incomplete partial results for {condition}: " + "; ".join(artifact_errors)
                )

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
            raise PipelineError("Rolling merge failed: no raw iterations were collected")

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
            if self.is_multinode:
                passed, errors = validate_multi_node_placement(
                    deployment_metadata,
                    require_dedicated_client_node=True,
                )
                if not passed:
                    raise PipelineError(
                        "Multi-node placement validation failed:\n- "
                        + "\n- ".join(errors)
                    )
                environment["multi_node_validation"] = {
                    "strategy": self.placement_strategy,
                    "passed": True,
                }
            elif not deployment_section.get("pod_colocation_enforced", False):
                raise PipelineError(
                    "Rolling merge detected missing or non-colocated service pod placement. "
                    "RQ1.5 requires verifiable same-node colocation for each condition."
                )
        environment["rolling_orchestration"] = {
            "enabled": True,
            "conditions": self.conditions,
            "partial_results_root": str(self.state.host_partial_results_dir.resolve()),
            "teardown_between_conditions": True,
        }
        environment["experiment_signature"] = {
            "signature": self.experiment_signature,
            "stage": "RQ1.5b" if self.is_multinode else "RQ1.5",
            "mode": "multi_node" if self.is_multinode else "single_node",
            "placement_strategy": self.placement_strategy,
            "namespace": self.namespace,
            "host_export_dir": str(self.state.host_export_dir.resolve()),
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
        log("Running host-side analysis on merged rolling results.")
        run_command(
            [
                sys.executable,
                str(self.repo_root / "run_analysis.py"),
                str(self.state.final_results_dir),
            ]
        )

    def run_rolling_benchmark(self) -> None:
        self.deploy_base_resources()
        self.wait_for_client_ready()

        for condition_name in self.conditions:
            if self.args.resume_artifact_dir:
                existing_dir = self.state.host_partial_results_dir / condition_name
                artifact_errors = self.validate_condition_artifacts(condition_name, existing_dir)
                if not artifact_errors:
                    log(f"Skipping {condition_name}; complete partial results already exist.")
                    continue
                if existing_dir.exists():
                    warn(
                        f"Rerunning {condition_name}; existing partial is incomplete: "
                        + "; ".join(artifact_errors)
                    )

            self.deploy_condition_resources(condition_name)
            self.wait_for_condition_ready(condition_name, self.condition_expected_pods(condition_name))
            self.run_condition_benchmark(condition_name)
            self.delete_condition_resources(condition_name)

        self.merge_rolling_results()
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

    def delete_cluster_on_success(self) -> None:
        if self.args.delete_resource_group_on_success:
            if self.args.provisioner == "terraform":
                self.destroy_with_terraform()
                return
            log(f"Deleting resource group {self.args.resource_group}.")
            run_command(
                [
                    "az", "group", "delete",
                    "--name", self.args.resource_group,
                    "--yes",
                    "--no-wait",
                ]
            )
            return
        if self.args.delete_aks_on_success:
            log(f"Deleting AKS cluster {self.args.cluster_name}.")
            run_command(
                [
                    "az", "aks", "delete",
                    "--resource-group", self.args.resource_group,
                    "--name", self.args.cluster_name,
                    "--yes",
                ]
            )

    def handle_failure(self) -> None:
        if self.state.resources_deployed:
            try:
                self.gather_diagnostics()
            except Exception as exc:  # pragma: no cover - diagnostic best effort
                warn(f"Failed to gather diagnostics: {exc}")
            if self.args.cleanup_on_failure:
                try:
                    log(f"Cleanup-on-failure enabled; tearing down namespace {self.namespace}.")
                    self.cleanup_namespace()
                except Exception as exc:  # pragma: no cover - cleanup best effort
                    warn(f"Failed to clean up the namespace after an error: {exc}")
            else:
                warn(f"Preserving namespace {self.namespace} for inspection.")
        if self.args.delete_resource_group_on_failure:
            try:
                log("Cost-bound failure cleanup: destroying Terraform-managed infrastructure.")
                self._destroy_resource_group_unconditional()
            except Exception as exc:  # pragma: no cover - destroy best effort
                warn(f"Failed to delete resource group on failure: {exc}")
        warn(f"Run failed. Host artifacts directory: {self.state.host_export_dir}")

    def _destroy_resource_group_unconditional(self) -> None:
        if self.args.provisioner == "terraform":
            try:
                self.destroy_with_terraform()
                return
            except Exception as exc:  # pragma: no cover - fall back to az
                warn(
                    f"Terraform destroy failed during failure cleanup ({exc}); "
                    "falling back to az group delete."
                )
                if not self._terraform_creates_resource_group():
                    warn(
                        "Skipping fallback resource-group deletion because this run uses "
                        "an existing/shared resource group."
                    )
                    return
        run_command(
            [
                "az", "group", "delete",
                "--name", self.args.resource_group,
                "--yes",
                "--no-wait",
            ],
            check=False,
        )

    def run(self) -> None:
        self.prepare_artifact_dirs()
        self.verify_required_files()
        self.verify_host_prerequisites()
        self.maybe_provision_cluster()
        if not self.args.provision and not self.args.skip_kubeconfig_refresh:
            self.refresh_kubeconfig()
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
        self.cleanup_namespace()
        self.delete_cluster_on_success()
        if self.state.final_results_dir is None:
            raise PipelineError("Run completed without a final results directory")
        log(
            "RQ1.5 rolling fully controlled run finished successfully. "
            f"Final results directory: {self.state.final_results_dir}"
        )


def main() -> int:
    args = parse_args()
    orchestrator = RQ15Orchestrator(args)
    try:
        orchestrator.run()
    except Exception as exc:
        orchestrator.handle_failure()
        print(f"[{timestamp()}] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
