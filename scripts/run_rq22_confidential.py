from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tarfile
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import preflight_rq22_confidential as rq22_preflight  # noqa: E402
from scripts.run_rq21_fully_controlled import (  # noqa: E402
    DEFAULT_CLIENT_POD,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_RESOURCE_GROUP,
    DEFAULT_SYSTEM_NODE_COUNT,
    DEFAULT_SYSTEM_NODE_VM_SIZE,
    DEFAULT_SYSTEM_NODEPOOL,
    INFRA_DIR,
    PipelineError,
    az_cli_kubeconfig_path,
    default_kubeconfig_path,
    ensure_command,
    load_yaml,
    log,
    run_command,
    utc_run_stamp,
    warn,
)


DEFAULT_CONFIG = "configs/rq2/2.2/rq2_2_confidential_amd_sev_snp.yaml"
DEFAULT_SERVICE1_NODEPOOL = "r22s1std"
DEFAULT_SERVICE1_CONFIDENTIAL_NODEPOOL = "r22s1cvm"
DEFAULT_SERVICE2_STANDARD_NODEPOOL = "r22s2std"
DEFAULT_SERVICE2_CONFIDENTIAL_NODEPOOL = "r22s2cvm"
DEFAULT_RESULTS_ROOT = str(REPO_ROOT / "results")
DEFAULT_REGION = rq22_preflight.APPROVED_REGION
DEFAULT_STANDARD_SIZE = rq22_preflight.APPROVED_STANDARD_SIZE
DEFAULT_CONFIDENTIAL_SIZE = rq22_preflight.APPROVED_CONFIDENTIAL_SIZE
STANDARD_CONDITION = "chain_2svc_mtls_standard"
CONFIDENTIAL_CONDITION = "chain_2svc_mtls_confidential_service2"


@dataclass(frozen=True)
class RollingNodePoolSpec:
    role: str
    nodepool: str
    vm_size: str
    labels: dict[str, str]


@dataclass(frozen=True)
class RQ22ConditionSpec:
    key: str
    condition_name: str
    rolling_nodepools: tuple[RollingNodePoolSpec, ...]
    service1_nodepool: str
    service1_vm_size: str
    service1_confidential: bool
    service2_nodepool: str
    service2_vm_size: str
    service2_confidential: bool


@dataclass
class ConditionContext:
    key: str
    pass_index: int
    execution_index: int
    condition_name: str
    effective_config_path: Path
    condition_dir: Path
    manifest_dir: Path
    benchmark_dir: Path
    service_namespace: str
    client_namespace: str


def save_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def command_record(result: subprocess.CompletedProcess, started_at: str, finished_at: str) -> dict[str, Any]:
    return {
        "args": list(result.args) if isinstance(result.args, list) else result.args,
        "returncode": int(result.returncode),
        "stdout": result.stdout or "",
        "stderr": result.stderr or "",
        "started_at": started_at,
        "finished_at": finished_at,
    }


def stream_command(args: list[str], log_path: Path, *, cwd: Path | None = None) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            args,
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
            raise PipelineError(f"Command failed with exit code {exit_code}: {' '.join(args)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "RQ2.2 AMD SEV-SNP rolling runner. Provisions the shared service1 AKS foundation, "
            "then alternates standard and confidential node pools so quota stays bounded."
        )
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--results-root", default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--provision", action="store_true")
    parser.add_argument("--provisioner", choices=["terraform"], default="terraform")
    parser.add_argument("--acr-name", default=None)
    parser.add_argument("--image-ref", default=None, help="Pinned digest image to inject into the RQ2.2 effective configs.")
    parser.add_argument("--push", action="store_true", help="Push a thesis-inference image to the target ACR before running.")
    parser.add_argument("--build", action="store_true", help="Build the local thesis-inference image before pushing.")
    parser.add_argument("--image-tag", default=f"rq22-{utc_run_stamp().lower()}")
    parser.add_argument("--local-image", default="thesis-inference:latest")
    parser.add_argument(
        "--no-auto-push-missing-image",
        action="store_true",
        help="Disable the provisioned-run default that builds and pushes a fresh image to the new ACR.",
    )
    parser.set_defaults(attach_image_acr=True)
    parser.add_argument(
        "--no-attach-image-acr",
        dest="attach_image_acr",
        action="store_false",
        help="Do not attach the ACR named in the effective image reference to the AKS cluster.",
    )
    parser.add_argument("--resource-group", default="rg-thesis-rq22")
    parser.add_argument("--cluster-name", default="thesis-rq22")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--system-nodepool", default=DEFAULT_SYSTEM_NODEPOOL)
    parser.add_argument("--system-node-count", type=int, default=DEFAULT_SYSTEM_NODE_COUNT)
    parser.add_argument("--system-node-vm-size", default=DEFAULT_SYSTEM_NODE_VM_SIZE)
    parser.add_argument("--service1-nodepool", default=DEFAULT_SERVICE1_NODEPOOL)
    parser.add_argument("--service1-confidential-nodepool", default=DEFAULT_SERVICE1_CONFIDENTIAL_NODEPOOL)
    parser.add_argument("--service1-size", default=DEFAULT_STANDARD_SIZE)
    parser.add_argument("--service2-standard-nodepool", default=DEFAULT_SERVICE2_STANDARD_NODEPOOL)
    parser.add_argument("--service2-confidential-nodepool", default=DEFAULT_SERVICE2_CONFIDENTIAL_NODEPOOL)
    parser.add_argument("--standard-size", default=DEFAULT_STANDARD_SIZE)
    parser.add_argument("--confidential-size", default=DEFAULT_CONFIDENTIAL_SIZE)
    parser.add_argument("--service2-zone", default="1", help="Availability zone for rolling service2 pools.")
    parser.add_argument("--paired-passes", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=42)
    parser.add_argument(
        "--order",
        choices=["seeded", "standard-first", "confidential-first"],
        default="standard-first",
        help="Execution order for pass 1; later passes alternate that order.",
    )
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD)
    parser.add_argument("--readiness-timeout", type=int, default=None)
    parser.add_argument("--skip-mesh-enable", action="store_true")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--preserve-namespaces", action="store_true")
    parser.add_argument("--keep-service2-nodepools", action="store_true")
    parser.add_argument("--destroy-infrastructure-on-success", action="store_true")
    parser.add_argument("--destroy-infrastructure-on-failure", action="store_true")
    args = parser.parse_args()
    if args.paired_passes < 1:
        parser.error("--paired-passes must be at least 1")
    if args.provision and not args.acr_name:
        parser.error("--acr-name is required with --provision")
    if args.build and not args.push:
        parser.error("--build requires --push")
    if args.image_ref and (args.push or args.build):
        parser.error("--image-ref cannot be combined with --push/--build")
    if (args.destroy_infrastructure_on_success or args.destroy_infrastructure_on_failure) and not args.provision:
        parser.error("infrastructure destroy flags require --provision")
    return args


class RQ22ConfidentialRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.repo_root = REPO_ROOT
        self.config_path = (self.repo_root / args.config).resolve()
        self.raw_config = load_yaml(self.config_path)
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))

        self.run_stamp = utc_run_stamp()
        self.artifact_dir = Path(args.results_root).resolve() / f"rq2_2_confidential_{self.run_stamp}"
        self.config_dir = self.artifact_dir / "effective_configs"
        self.conditions_root = self.artifact_dir / "conditions"
        self.lifecycle_path = self.artifact_dir / "infrastructure_lifecycle.json"
        self.summary_path = self.artifact_dir / "rq22_rolling_summary.json"
        self.tfvars_path = self.artifact_dir / "rq22_terraform.tfvars.json"
        self.commands: list[dict[str, Any]] = []
        self.completed: list[dict[str, Any]] = []
        self.infrastructure_provisioned = False
        self.infrastructure_destroyed = False
        self.active_service2_pool: str | None = None
        self.active_rolling_pools: list[str] = []
        self.effective_pinned_image_ref = ""
        self._existing_acr_resource_group: str | None = None
        self._resource_group_exists: bool | None = None

    def standard_condition_name(self) -> str:
        cc = self.raw_config.get("confidential_compute") or {}
        return str(cc.get("standard_condition") or STANDARD_CONDITION)

    def confidential_condition_name(self) -> str:
        cc = self.raw_config.get("confidential_compute") or {}
        return str(cc.get("confidential_condition") or CONFIDENTIAL_CONDITION)

    def confidential_target_indices(self) -> set[str]:
        cc = self.raw_config.get("confidential_compute") or {}
        target_indices = cc.get("target_service_indices")
        if isinstance(target_indices, list):
            return {str(item) for item in target_indices if item not in (None, "")}
        if target_indices not in (None, ""):
            return {str(target_indices)}
        return {str(cc.get("target_service_index") or "2")}

    def tee_scope(self) -> str:
        targets = self.confidential_target_indices()
        if targets == {"1", "2"}:
            return "full_2svc"
        if targets == {"2"}:
            return "service2_only"
        return "selected_segments_" + "_".join(sorted(targets))

    def rolling_nodepool_specs(self) -> dict[str, RollingNodePoolSpec]:
        return {
            "service1_confidential": RollingNodePoolSpec(
                role="service1_confidential",
                nodepool=self.args.service1_confidential_nodepool,
                vm_size=self.args.confidential_size,
                labels={
                    "rq": "2.2",
                    "rq22-role": "service1-confidential",
                    "confidential-compute": "amd-sev-snp",
                    "purpose": "rq22",
                },
            ),
            "service2_standard": RollingNodePoolSpec(
                role="service2_standard",
                nodepool=self.args.service2_standard_nodepool,
                vm_size=self.args.standard_size,
                labels={
                    "rq": "2.2",
                    "rq22-role": "service2-standard",
                    "purpose": "rq22",
                },
            ),
            "service2_confidential": RollingNodePoolSpec(
                role="service2_confidential",
                nodepool=self.args.service2_confidential_nodepool,
                vm_size=self.args.confidential_size,
                labels={
                    "rq": "2.2",
                    "rq22-role": "service2-confidential",
                    "confidential-compute": "amd-sev-snp",
                    "purpose": "rq22",
                },
            ),
        }

    def condition_specs(self) -> dict[str, RQ22ConditionSpec]:
        rolling = self.rolling_nodepool_specs()
        confidential_targets = self.confidential_target_indices()
        confidential_nodepools: list[RollingNodePoolSpec] = []
        if "1" in confidential_targets:
            confidential_nodepools.append(rolling["service1_confidential"])
        if "2" in confidential_targets:
            confidential_nodepools.append(rolling["service2_confidential"])
        return {
            "standard": RQ22ConditionSpec(
                key="standard",
                condition_name=self.standard_condition_name(),
                rolling_nodepools=(rolling["service2_standard"],),
                service1_nodepool=self.args.service1_nodepool,
                service1_vm_size=self.args.service1_size,
                service1_confidential=False,
                service2_nodepool=self.args.service2_standard_nodepool,
                service2_vm_size=self.args.standard_size,
                service2_confidential=False,
            ),
            "confidential": RQ22ConditionSpec(
                key="confidential",
                condition_name=self.confidential_condition_name(),
                rolling_nodepools=tuple(confidential_nodepools),
                service1_nodepool=(
                    self.args.service1_confidential_nodepool
                    if "1" in confidential_targets
                    else self.args.service1_nodepool
                ),
                service1_vm_size=(
                    self.args.confidential_size
                    if "1" in confidential_targets
                    else self.args.service1_size
                ),
                service1_confidential="1" in confidential_targets,
                service2_nodepool=(
                    self.args.service2_confidential_nodepool
                    if "2" in confidential_targets
                    else self.args.service2_standard_nodepool
                ),
                service2_vm_size=(
                    self.args.confidential_size
                    if "2" in confidential_targets
                    else self.args.standard_size
                ),
                service2_confidential="2" in confidential_targets,
            ),
        }

    def service2_specs(self) -> dict[str, RQ22ConditionSpec]:
        return self.condition_specs()

    def execution_plan(self) -> dict[str, Any]:
        if self.args.order == "standard-first":
            first_order = ["standard", "confidential"]
        elif self.args.order == "confidential-first":
            first_order = ["confidential", "standard"]
        else:
            first_order = ["standard", "confidential"]
            random.Random(self.args.order_seed).shuffle(first_order)
        passes = []
        for pass_index in range(1, self.args.paired_passes + 1):
            order = first_order if pass_index % 2 == 1 else list(reversed(first_order))
            passes.append({"pass": pass_index, "order": list(order)})
        return {
            "paired_passes": self.args.paired_passes,
            "order": self.args.order,
            "order_seed": self.args.order_seed,
            "passes": passes,
        }

    def run_logged(
        self,
        args: list[str],
        *,
        cwd: Path | None = REPO_ROOT,
        capture_output: bool = True,
        check: bool = True,
        timeout_seconds: int | None = None,
    ) -> subprocess.CompletedProcess:
        started_at = datetime.now(timezone.utc).isoformat()
        result = run_command(
            args,
            cwd=cwd,
            capture_output=capture_output,
            check=False,
            timeout_seconds=timeout_seconds,
        )
        finished_at = datetime.now(timezone.utc).isoformat()
        self.commands.append(command_record(result, started_at, finished_at))
        if check and result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(f"Command failed: {' '.join(args)}\n{detail or result.returncode}")
        return result

    def validate_approved_plan(self) -> None:
        checks, gate_errors = rq22_preflight.config_hard_gate(self.raw_config)
        preserved, semantic_errors = rq22_preflight.rq21_security_semantics(self.raw_config)
        errors = list(gate_errors) + list(semantic_errors)
        if self.args.region != rq22_preflight.APPROVED_REGION:
            errors.append(f"--region must be {rq22_preflight.APPROVED_REGION}, observed={self.args.region}")
        if self.args.service1_size != rq22_preflight.APPROVED_STANDARD_SIZE:
            errors.append(f"--service1-size must be {rq22_preflight.APPROVED_STANDARD_SIZE}")
        if self.args.standard_size != rq22_preflight.APPROVED_STANDARD_SIZE:
            errors.append(f"--standard-size must be {rq22_preflight.APPROVED_STANDARD_SIZE}")
        if self.args.confidential_size != rq22_preflight.APPROVED_CONFIDENTIAL_SIZE:
            errors.append(f"--confidential-size must be {rq22_preflight.APPROVED_CONFIDENTIAL_SIZE}")
        if errors:
            raise PipelineError("RQ2.2 approved AMD plan validation failed:\n- " + "\n- ".join(errors))
        (self.artifact_dir / "approved_plan_checks.json").write_text(
            json.dumps({"config_checks": checks, "rq21_mtls_authz_preserved": preserved}, indent=2),
            encoding="utf-8",
        )

    def verify_prerequisites(self) -> None:
        self.require_command("python")
        if self.args.generate_only:
            return
        self.require_command("az")
        self.require_command("kubectl")
        self.require_command("kubelogin")
        if self.args.provision:
            self.require_command("terraform")
        if self.image_push_required():
            self.require_command("docker")
            self.verify_docker_ready()

    def linux_kube_tool_hint(self) -> str:
        return (
            "Install Linux kubectl and kubelogin in this shell, then rerun the same RQ2.2 command.\n"
            "If `az aks install-cli` downloaded Windows binaries under WSL, remove them first:\n"
            "  rm -f ~/.local/bin/kubectl ~/.local/bin/kubelogin /tmp/kubelogin-linux-amd64.zip\n"
            "Then install Linux binaries without sudo:\n"
            "  mkdir -p ~/.local/bin\n"
            "  curl -L -o ~/.local/bin/kubectl "
            "\"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"\n"
            "  chmod +x ~/.local/bin/kubectl\n"
            "  curl -L -o /tmp/kubelogin-linux-amd64.zip "
            "https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-linux-amd64.zip\n"
            "  python - <<'PY'\n"
            "import pathlib, stat, zipfile\n"
            "dst = pathlib.Path.home() / '.local/bin/kubelogin'\n"
            "with zipfile.ZipFile('/tmp/kubelogin-linux-amd64.zip') as zf:\n"
            "    name = next(name for name in zf.namelist() if name.endswith('/kubelogin') or name == 'kubelogin')\n"
            "    dst.write_bytes(zf.read(name))\n"
            "dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)\n"
            "PY\n"
            "  export PATH=\"$HOME/.local/bin:$PATH\"\n"
            "  hash -r\n"
            "  file ~/.local/bin/kubectl ~/.local/bin/kubelogin\n"
            "  kubectl version --client\n"
            "  kubelogin --version\n"
            "Persist PATH for new shells with:\n"
            "  echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc"
        )

    def docker_wsl_hint(self) -> str:
        return (
            "Docker is required before RQ2.2 can build or push the benchmark image. "
            "If you are running from WSL, enable Docker Desktop Settings > Resources > WSL Integration "
            "for this distro, then run `wsl.exe --shutdown` from PowerShell and reopen WSL. "
            "Verify with `docker info` before rerunning."
        )

    def require_command(self, command_name: str) -> None:
        try:
            ensure_command(command_name)
        except PipelineError as exc:
            if command_name in {"kubectl", "kubelogin"}:
                raise PipelineError(
                    f"Required command not found: {command_name}.\n{self.linux_kube_tool_hint()}"
                ) from exc
            raise
        if command_name in {"kubectl", "kubelogin"}:
            version_args = [command_name, "version", "--client"] if command_name == "kubectl" else [command_name, "--version"]
            try:
                result = run_command(version_args, capture_output=True, check=False)
            except OSError as exc:
                raise PipelineError(
                    f"Found {command_name}, but it is not executable in this shell: {exc}\n"
                    f"{self.linux_kube_tool_hint()}"
                ) from exc
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise PipelineError(
                    f"Found {command_name}, but `{ ' '.join(version_args) }` failed: "
                    f"{detail or result.returncode}\n{self.linux_kube_tool_hint()}"
                )

    def verify_docker_ready(self) -> None:
        try:
            result = run_command(["docker", "info"], capture_output=True, check=False)
        except OSError as exc:
            raise PipelineError(
                f"Found docker, but it is not executable in this shell: {exc}\n{self.docker_wsl_hint()}"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(
                "Docker is required for RQ2.2 image build/push, but `docker info` failed:\n"
                f"{detail or result.returncode}\n{self.docker_wsl_hint()}"
            )

    def image_push_required(self) -> bool:
        return bool(
            self.args.push
            or (
                self.args.provision
                and not self.args.image_ref
                and not self.args.no_auto_push_missing_image
            )
        )

    def prepare_artifacts(self) -> None:
        for path in (self.artifact_dir, self.config_dir, self.conditions_root):
            path.mkdir(parents=True, exist_ok=True)
        (self.artifact_dir / "execution_plan.json").write_text(
            json.dumps(self.execution_plan(), indent=2),
            encoding="utf-8",
        )

    def terraform_vars(self) -> dict[str, Any]:
        payload = {
            "resource_group_name": self.args.resource_group,
            "location": self.args.region,
            "acr_name": self.args.acr_name,
            "cluster_name": self.args.cluster_name,
            "enable_benchmark_pool": True,
            "system_nodepool_name": self.args.system_nodepool,
            "system_node_count": self.args.system_node_count,
            "system_node_vm_size": self.args.system_node_vm_size,
            "nodepool_name": self.args.service1_nodepool,
            "node_count": 1,
            "node_vm_size": self.args.service1_size,
            "benchmark_node_taint": "",
            "benchmark_node_labels": {
                "rq": "2.2",
                "rq22-role": "service1-standard",
            },
            "experiment_tag": "rq22-amd-rolling",
        }
        if not self._terraform_creates_resource_group():
            payload["create_resource_group"] = False
        if self._terraform_uses_existing_acr():
            payload["create_acr"] = False
            payload["acr_resource_group_name"] = self._existing_acr_group()
        return payload

    def _az_tsv(self, args: list[str], *, check: bool = False) -> str:
        result = self.run_logged(
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
        if not self.args.acr_name:
            raise PipelineError("ACR name is required before resolving existing ACR resource group")
        group = self._az_tsv(
            ["acr", "show", "--name", self.args.acr_name, "--query", "resourceGroup"],
            check=False,
        )
        if not group:
            raise PipelineError(
                f"ACR {self.args.acr_name} was not found in the current Azure subscription. "
                "The uniform-image run passes --image-ref, so the registry must already exist."
            )
        self._existing_acr_resource_group = group
        return group

    def _terraform_var_file_args(self) -> list[str]:
        return ["-var-file", str(self.tfvars_path)]

    def _terraform_state_addresses(self) -> set[str]:
        result = self.run_logged(
            ["terraform", "state", "list"],
            cwd=INFRA_DIR,
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
        self.run_logged(
            ["terraform", "import", *self._terraform_var_file_args(), address, resource_id],
            cwd=INFRA_DIR,
            capture_output=False,
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
            self.run_logged(
                ["terraform", "state", "rm", address],
                cwd=INFRA_DIR,
                capture_output=False,
            )
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
        elif self.args.acr_name:
            acr_id = self._az_tsv(
                ["acr", "show", "--name", self.args.acr_name, "--query", "id"],
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
                    self.args.service1_nodepool,
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

    def write_lifecycle(self, extra: dict[str, Any] | None = None) -> None:
        payload = {
            "provision_requested": bool(self.args.provision),
            "provisioned": self.infrastructure_provisioned,
            "destroyed": self.infrastructure_destroyed,
            "resource_group": self.args.resource_group,
            "cluster_name": self.args.cluster_name,
            "acr_name": self.args.acr_name,
            "region": self.args.region,
            "service1_nodepool": self.args.service1_nodepool,
            "service1_confidential_nodepool": self.args.service1_confidential_nodepool,
            "service1_size": self.args.service1_size,
            "service2_standard_nodepool": self.args.service2_standard_nodepool,
            "service2_confidential_nodepool": self.args.service2_confidential_nodepool,
            "service2_zone": self.args.service2_zone,
            "tee_scope": self.tee_scope(),
            "effective_image_ref": self.effective_pinned_image_ref,
        }
        if extra:
            payload.update(extra)
        self.lifecycle_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def provision_foundation(self) -> None:
        if not self.args.provision:
            return
        self.tfvars_path.write_text(json.dumps(self.terraform_vars(), indent=2), encoding="utf-8")
        log("Provisioning RQ2.2 service1 AKS foundation with Terraform.")
        self.run_logged(["terraform", "init", "-input=false"], cwd=INFRA_DIR, capture_output=False)
        self.prepare_terraform_state()
        self.run_logged(
            ["terraform", "apply", "-auto-approve", "-input=false", *self._terraform_var_file_args()],
            cwd=INFRA_DIR,
            capture_output=False,
        )
        result = self.run_logged(["terraform", "output", "-json"], cwd=INFRA_DIR, capture_output=True)
        outputs = json.loads(result.stdout or "{}")
        self.args.resource_group = str(outputs.get("resource_group_name", {}).get("value") or self.args.resource_group)
        self.args.cluster_name = str(outputs.get("cluster_name", {}).get("value") or self.args.cluster_name)
        self.args.acr_name = str(outputs.get("acr_name", {}).get("value") or self.args.acr_name)
        self.infrastructure_provisioned = True
        self.write_lifecycle({"tfvars_file": str(self.tfvars_path)})
        self.refresh_kubeconfig()

    def destroy_infrastructure(self, reason: str) -> None:
        if self.infrastructure_destroyed or not self.args.provision:
            return
        log(f"Destroying RQ2.2 Terraform foundation after {reason}.")
        if not self.tfvars_path.exists():
            self.tfvars_path.write_text(json.dumps(self.terraform_vars(), indent=2), encoding="utf-8")
        self.run_logged(["terraform", "init", "-input=false"], cwd=INFRA_DIR, capture_output=False)
        self.run_logged(
            ["terraform", "destroy", "-auto-approve", "-input=false", *self._terraform_var_file_args()],
            cwd=INFRA_DIR,
            capture_output=False,
        )
        self.infrastructure_destroyed = True
        self.write_lifecycle({"destroy_reason": reason, "destroyed_at": datetime.now(timezone.utc).isoformat()})

    def refresh_kubeconfig(self) -> None:
        self.kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_logged(
            [
                "az",
                "aks",
                "get-credentials",
                "--resource-group",
                self.args.resource_group,
                "--name",
                self.args.cluster_name,
                "--overwrite-existing",
                "--file",
                az_cli_kubeconfig_path(self.kubeconfig_path),
            ],
            capture_output=True,
        )

    def effective_image_ref(self) -> str:
        return str(
            self.effective_pinned_image_ref
            or self.args.image_ref
            or ((self.raw_config.get("kubernetes") or {}).get("image"))
            or ""
        ).strip()

    def image_acr_name(self) -> str | None:
        match = re.match(r"^([a-zA-Z0-9]+)\.azurecr\.io/", self.effective_image_ref())
        return match.group(1) if match else None

    def configured_image_ref(self) -> str:
        return str(((self.raw_config.get("kubernetes") or {}).get("image")) or "").strip()

    def validate_image_plan_before_provision(self) -> None:
        if self.args.generate_only:
            return
        image = self.effective_image_ref()
        if self.args.image_ref and "@sha256:" not in image:
            raise PipelineError("--image-ref must be pinned with @sha256:<digest>")
        if self.image_push_required():
            return
        if "@sha256:" not in image:
            raise PipelineError(
                "RQ2.2 live runs require a pinned image digest. Rerun with --push --build, "
                "omit --no-auto-push-missing-image when provisioning, or pass --image-ref <acr>.azurecr.io/thesis-inference@sha256:<digest>."
            )
        image_acr = self.image_acr_name()
        if self.args.attach_image_acr and image_acr and image_acr != self.args.acr_name:
            result = self.run_logged(
                ["az", "acr", "show", "--name", image_acr, "--query", "id", "-o", "tsv"],
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise PipelineError(
                    f"The image ACR {image_acr} is not visible in this subscription before provisioning: "
                    f"{detail or result.returncode}. Use --push --build, omit --no-auto-push-missing-image, "
                    "or pass an image in an ACR this subscription can access."
                )

    def push_image_to_acr(self, *, build: bool, reason: str) -> str:
        if not self.args.acr_name:
            raise PipelineError("ACR name is required before pushing the RQ2.2 image")
        if build:
            log(f"Building local image {self.args.local_image} before {reason}.")
            self.run_logged(["docker", "build", "-t", self.args.local_image, "."], capture_output=False)
        log(f"Logging in to ACR {self.args.acr_name}.azurecr.io.")
        self.run_logged(["az", "acr", "login", "--name", self.args.acr_name], capture_output=True)
        remote_image = f"{self.args.acr_name}.azurecr.io/thesis-inference:{self.args.image_tag}"
        log(f"Tagging {self.args.local_image} as {remote_image}.")
        self.run_logged(["docker", "tag", self.args.local_image, remote_image], capture_output=False)
        log(f"Pushing {remote_image}.")
        self.run_logged(["docker", "push", remote_image], capture_output=False)
        result = self.run_logged(
            [
                "az",
                "acr",
                "repository",
                "show",
                "--name",
                self.args.acr_name,
                "--image",
                f"thesis-inference:{self.args.image_tag}",
                "--query",
                "digest",
                "--output",
                "tsv",
            ],
            capture_output=True,
        )
        digest = (result.stdout or "").strip().strip('"')
        if not digest.startswith("sha256:"):
            raise PipelineError(f"Unexpected ACR digest response after push: {digest!r}")
        pinned_ref = f"{self.args.acr_name}.azurecr.io/thesis-inference@{digest}"
        self.effective_pinned_image_ref = pinned_ref
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        (self.artifact_dir / "image_reference.txt").write_text(pinned_ref + "\n", encoding="utf-8")
        (self.artifact_dir / "image_resolution.json").write_text(
            json.dumps(
                {
                    "reason": reason,
                    "acr_name": self.args.acr_name,
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
        if self.args.image_ref:
            self.effective_pinned_image_ref = self.args.image_ref
            (self.artifact_dir / "image_reference.txt").write_text(self.args.image_ref + "\n", encoding="utf-8")
            return self.args.image_ref
        if self.args.push:
            return self.push_image_to_acr(build=self.args.build, reason="explicit --push")
        if self.args.provision and not self.args.no_auto_push_missing_image:
            configured = self.configured_image_ref()
            if configured:
                warn(
                    f"Provisioned RQ2.2 run will publish a fresh image to {self.args.acr_name}.azurecr.io "
                    f"instead of using configured image {configured}."
                )
            return self.push_image_to_acr(build=True, reason="provisioned RQ2.2 run uses fresh target ACR image")
        image = self.configured_image_ref()
        if "@sha256:" not in image:
            raise PipelineError("RQ2.2 live runs require a pinned kubernetes.image digest")
        self.effective_pinned_image_ref = image
        (self.artifact_dir / "image_reference.txt").write_text(image + "\n", encoding="utf-8")
        return image

    def attach_image_acr_if_needed(self) -> None:
        if self.args.generate_only or not self.args.attach_image_acr:
            return
        image_acr = self.image_acr_name()
        if not image_acr or image_acr == self.args.acr_name:
            return
        log(f"Attaching image ACR {image_acr} to AKS cluster {self.args.cluster_name}.")
        self.run_logged(
            [
                "az",
                "aks",
                "update",
                "--resource-group",
                self.args.resource_group,
                "--name",
                self.args.cluster_name,
                "--attach-acr",
                image_acr,
            ],
            capture_output=True,
        )

    def mesh_revision(self) -> str:
        revision = str(((self.raw_config.get("kubernetes") or {}).get("mesh") or {}).get("revision") or "").strip()
        if not revision:
            raise PipelineError("RQ2.2 config must pin kubernetes.mesh.revision")
        return revision

    def cluster_mesh_revisions(self) -> list[str]:
        result = self.run_logged(
            [
                "az",
                "aks",
                "show",
                "--resource-group",
                self.args.resource_group,
                "--name",
                self.args.cluster_name,
                "--query",
                "serviceMeshProfile.istio.revisions",
                "-o",
                "json",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(f"Unable to inspect AKS managed Istio state: {detail or result.returncode}")
        payload = json.loads(result.stdout or "null")
        if payload is None:
            return []
        if isinstance(payload, list):
            return [str(item) for item in payload if item not in (None, "")]
        return [str(payload)]

    def ensure_managed_istio(self) -> None:
        if self.args.generate_only:
            return
        revision = self.mesh_revision()
        observed = self.cluster_mesh_revisions()
        if revision in observed:
            log(f"AKS managed Istio add-on already has revision {revision}.")
            return
        if observed:
            raise PipelineError(f"AKS managed Istio revision mismatch: expected={revision} observed={observed}")
        if self.args.skip_mesh_enable:
            raise PipelineError(f"AKS managed Istio is not enabled and --skip-mesh-enable was set; expected {revision}.")
        log(f"Enabling AKS managed Istio revision {revision}.")
        self.run_logged(
            [
                "az",
                "aks",
                "mesh",
                "enable",
                "--resource-group",
                self.args.resource_group,
                "--name",
                self.args.cluster_name,
                "--revision",
                revision,
            ],
            capture_output=True,
        )

    def effective_base_config(self) -> dict[str, Any]:
        raw = deepcopy(self.raw_config)
        raw.setdefault("kubernetes", {})
        image_ref = self.effective_image_ref()
        if image_ref:
            raw["kubernetes"]["image"] = image_ref
        raw["kubernetes"].setdefault("placement", {})
        placement = raw["kubernetes"]["placement"]
        placement["node_pools"] = {
            "service1_standard": self.args.service1_nodepool,
            "service1_confidential": self.args.service1_confidential_nodepool,
            "service2_standard": self.args.service2_standard_nodepool,
            "service2_confidential": self.args.service2_confidential_nodepool,
        }
        placement["node_selectors"] = {
            "service1_standard": {"rq": "2.2", "rq22-role": "service1-standard"},
            "service1_confidential": {
                "rq": "2.2",
                "rq22-role": "service1-confidential",
                "confidential-compute": "amd-sev-snp",
            },
            "service2_standard": {"rq": "2.2", "rq22-role": "service2-standard"},
            "service2_confidential": {
                "rq": "2.2",
                "rq22-role": "service2-confidential",
                "confidential-compute": "amd-sev-snp",
            },
        }
        placement["node_pool"] = self.args.service1_nodepool
        placement["node_selector"] = {"rq": "2.2", "rq22-role": "service1-standard"}
        if self.args.readiness_timeout is not None:
            raw["kubernetes"]["readiness_timeout"] = float(self.args.readiness_timeout)
        return raw

    def condition_config(self, key: str) -> dict[str, Any]:
        specs = self.condition_specs()
        if key not in specs:
            raise PipelineError(f"Unknown RQ2.2 condition key: {key}")
        raw = self.effective_base_config()
        raw["conditions"] = [
            condition
            for condition in raw.get("conditions") or []
            if isinstance(condition, dict) and condition.get("name") == specs[key].condition_name
        ]
        if len(raw["conditions"]) != 1:
            raise PipelineError(f"Condition {specs[key].condition_name} was not found in {self.config_path}")
        return raw

    def condition_context(self, key: str, pass_index: int, execution_index: int) -> ConditionContext:
        spec = self.condition_specs()[key]
        condition_dir = self.conditions_root / f"pass{pass_index:02d}_{execution_index:02d}_{spec.condition_name}"
        effective_path = self.config_dir / f"{spec.condition_name}_pass{pass_index:02d}_effective.yaml"
        config = self.condition_config(key)
        save_yaml(effective_path, config)
        k8s = config.get("kubernetes") or {}
        return ConditionContext(
            key=key,
            pass_index=pass_index,
            execution_index=execution_index,
            condition_name=spec.condition_name,
            effective_config_path=effective_path,
            condition_dir=condition_dir,
            manifest_dir=condition_dir / "manifests",
            benchmark_dir=condition_dir / "benchmark",
            service_namespace=str(k8s.get("namespace")),
            client_namespace=str(k8s.get("client_namespace") or k8s.get("namespace")),
        )

    def add_rolling_nodepool(self, spec: RollingNodePoolSpec) -> dict[str, Any]:
        args = [
            "az",
            "aks",
            "nodepool",
            "add",
            "--resource-group",
            self.args.resource_group,
            "--cluster-name",
            self.args.cluster_name,
            "--name",
            spec.nodepool,
            "--node-count",
            "1",
            "--node-vm-size",
            spec.vm_size,
            "--mode",
            "User",
            "--zones",
            str(self.args.service2_zone),
            "--labels",
        ]
        for key, value in spec.labels.items():
            args.append(f"{key}={value}")
        args.extend(["--output", "json"])
        result = self.run_logged(args, capture_output=True, timeout_seconds=1800)
        self.active_service2_pool = spec.nodepool
        if spec.nodepool not in self.active_rolling_pools:
            self.active_rolling_pools.append(spec.nodepool)
        return json.loads(result.stdout or "{}")

    def delete_rolling_nodepool(self, nodepool: str) -> None:
        self.run_logged(
            [
                "az",
                "aks",
                "nodepool",
                "delete",
                "--resource-group",
                self.args.resource_group,
                "--cluster-name",
                self.args.cluster_name,
                "--name",
                nodepool,
            ],
            capture_output=True,
            check=False,
            timeout_seconds=1800,
        )
        if self.active_service2_pool == nodepool:
            self.active_service2_pool = None
        if nodepool in self.active_rolling_pools:
            self.active_rolling_pools.remove(nodepool)

    def add_service2_nodepool(self, spec: RollingNodePoolSpec) -> dict[str, Any]:
        return self.add_rolling_nodepool(spec)

    def delete_service2_nodepool(self, nodepool: str) -> None:
        self.delete_rolling_nodepool(nodepool)

    def generate_manifests(self, context: ConditionContext) -> None:
        context.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.run_logged(
            [
                sys.executable,
                str(self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py"),
                "--config",
                str(context.effective_config_path),
                "--output-dir",
                str(context.manifest_dir),
            ],
            capture_output=True,
        )

    def namespace_exists(self, namespace: str) -> bool:
        result = self.run_logged(["kubectl", "get", "namespace", namespace], capture_output=True, check=False)
        return result.returncode == 0

    def wait_for_namespace_deletion(self, namespace: str, timeout_seconds: int = 180) -> None:
        deadline = time.monotonic() + timeout_seconds
        while self.namespace_exists(namespace):
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for namespace deletion: {namespace}")
            time.sleep(2)

    def cleanup_namespaces(self, context: ConditionContext) -> None:
        for namespace in sorted({context.service_namespace, context.client_namespace}):
            self.run_logged(
                ["kubectl", "delete", "namespace", namespace, "--ignore-not-found=true", "--wait=false"],
                capture_output=True,
                check=False,
            )
        for namespace in sorted({context.service_namespace, context.client_namespace}):
            self.wait_for_namespace_deletion(namespace)

    def apply_manifests(self, context: ConditionContext) -> None:
        self.cleanup_namespaces(context)
        client_specific = context.manifest_dir / f"99_benchmark_client_{context.condition_name.replace('_', '-')}.yaml"
        ordered_files = [
            context.manifest_dir / "00_namespace.yaml",
            context.manifest_dir / "01_service_accounts.yaml",
            context.manifest_dir / f"{context.condition_name}.yaml",
            client_specific if client_specific.exists() else context.manifest_dir / "99_benchmark_client.yaml",
        ]
        for path in ordered_files:
            if path.exists():
                self.run_logged(["kubectl", "apply", "-f", str(path)], capture_output=True)

    def wait_for_ready(self, context: ConditionContext) -> None:
        timeout_seconds = int(self.args.readiness_timeout or ((self.raw_config.get("kubernetes") or {}).get("readiness_timeout") or 180))
        deadline_seconds = timeout_seconds + 60
        self.run_logged(
            [
                "kubectl",
                "rollout",
                "status",
                "deployment",
                "-n",
                context.service_namespace,
                "-l",
                f"condition={context.condition_name},workload-role=service",
                f"--timeout={deadline_seconds}s",
            ],
            capture_output=True,
        )
        self.run_logged(
            [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                "pod",
                "-n",
                context.service_namespace,
                "-l",
                f"condition={context.condition_name},workload-role=service",
                f"--timeout={deadline_seconds}s",
            ],
            capture_output=True,
        )
        self.run_logged(
            [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                f"pod/{self.args.client_pod}",
                "-n",
                context.client_namespace,
                f"--timeout={deadline_seconds}s",
            ],
            capture_output=True,
        )

    def copy_results(self, context: ConditionContext, remote_output: str) -> None:
        context.benchmark_dir.parent.mkdir(parents=True, exist_ok=True)
        if context.benchmark_dir.exists():
            shutil.rmtree(context.benchmark_dir)
        result = self.run_logged(
            ["kubectl", "cp", f"{context.client_namespace}/{self.args.client_pod}:{remote_output}", str(context.benchmark_dir)],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return
        warn(f"kubectl cp failed for {remote_output}; attempting tar-stream fallback.")
        code = (
            "import os, sys, tarfile; "
            "source_path = os.path.abspath(sys.argv[1]); "
            "archive = tarfile.open(fileobj=sys.stdout.buffer, mode='w|'); "
            "archive.add(source_path, arcname=os.path.basename(source_path)); "
            "archive.close()"
        )
        process = subprocess.Popen(
            [
                "kubectl",
                "exec",
                "-i",
                "-n",
                context.client_namespace,
                self.args.client_pod,
                "--",
                "python",
                "-c",
                code,
                remote_output,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        extracted_path = context.benchmark_dir.parent / Path(remote_output).name
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            archive.extractall(path=context.benchmark_dir.parent)
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
        if return_code != 0:
            raise PipelineError(f"kubectl tar-stream fallback failed: {stderr.strip() or return_code}")
        if extracted_path.exists() and extracted_path != context.benchmark_dir:
            shutil.move(str(extracted_path), str(context.benchmark_dir))

    def run_benchmark(self, context: ConditionContext) -> str:
        remote_root = "/tmp/rq22_confidential"
        remote_config = f"{remote_root}/{context.condition_name}_config.yaml"
        remote_output = f"{remote_root}/{context.condition_name}_pass{context.pass_index:02d}_{utc_run_stamp()}"
        self.run_logged(["kubectl", "exec", "-n", context.client_namespace, self.args.client_pod, "--", "mkdir", "-p", remote_root])
        self.run_logged(["kubectl", "cp", str(context.effective_config_path), f"{context.client_namespace}/{self.args.client_pod}:{remote_config}"])
        self.run_logged(["kubectl", "exec", "-n", context.client_namespace, self.args.client_pod, "--", "rm", "-rf", remote_output], check=False)
        stream_command(
            [
                "kubectl",
                "exec",
                "-n",
                context.client_namespace,
                self.args.client_pod,
                "--",
                "python",
                "run_k8s_experiment.py",
                "--config",
                remote_config,
                "--condition",
                context.condition_name,
                "--output-dir",
                remote_output,
            ],
            context.condition_dir / "benchmark_command.log",
            cwd=self.repo_root,
        )
        self.copy_results(context, remote_output)
        self.run_logged(["kubectl", "exec", "-n", context.client_namespace, self.args.client_pod, "--", "rm", "-rf", remote_output], check=False)
        return remote_output

    def run_condition(self, key: str, pass_index: int, execution_index: int) -> dict[str, Any]:
        spec = self.condition_specs()[key]
        context = self.condition_context(key, pass_index, execution_index)
        self.generate_manifests(context)
        record = {
            "pass": pass_index,
            "execution_index": execution_index,
            "condition_key": key,
            "condition_name": context.condition_name,
            "tee_scope": self.tee_scope(),
            "service1_nodepool": spec.service1_nodepool,
            "service1_vm_size": spec.service1_vm_size,
            "service1_confidential": spec.service1_confidential,
            "service2_nodepool": spec.service2_nodepool,
            "service2_vm_size": spec.service2_vm_size,
            "service2_confidential": spec.service2_confidential,
            "service2_zone": self.args.service2_zone,
            "rolling_nodepools": [
                {
                    "role": pool.role,
                    "nodepool": pool.nodepool,
                    "vm_size": pool.vm_size,
                    "labels": pool.labels,
                }
                for pool in spec.rolling_nodepools
            ],
            "effective_config": str(context.effective_config_path),
            "manifest_dir": str(context.manifest_dir),
            "benchmark_dir": str(context.benchmark_dir),
            "status": "planned" if self.args.generate_only else "started",
        }
        if self.args.generate_only:
            return record

        nodepool_payloads: list[dict[str, Any]] = []
        try:
            for pool in spec.rolling_nodepools:
                add_payload = self.add_rolling_nodepool(pool)
                nodepool_payloads.append(
                    {
                        "role": pool.role,
                        "name": add_payload.get("name"),
                        "vm_size": add_payload.get("vmSize"),
                        "provisioning_state": add_payload.get("provisioningState"),
                        "availability_zones": add_payload.get("availabilityZones"),
                        "node_labels": add_payload.get("nodeLabels"),
                    }
                )
            record["nodepool_create_response"] = nodepool_payloads
            self.apply_manifests(context)
            self.wait_for_ready(context)
            remote_output = self.run_benchmark(context)
            record["remote_output"] = remote_output
            record["status"] = "completed"
            return record
        finally:
            if not self.args.preserve_namespaces:
                try:
                    self.cleanup_namespaces(context)
                except Exception as exc:  # noqa: BLE001 - preserve cleanup issue in summary.
                    record.setdefault("cleanup_errors", []).append(str(exc))
            if not self.args.keep_service2_nodepools:
                for pool in reversed(spec.rolling_nodepools):
                    self.delete_rolling_nodepool(pool.nodepool)

    def write_summary(self, status: str, error: str | None = None) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "error": error,
            "artifact_dir": str(self.artifact_dir),
            "config": str(self.config_path),
            "execution_plan": self.execution_plan(),
            "completed": self.completed,
            "commands_attempted": self.commands,
            "effective_image_ref": self.effective_image_ref(),
            "infrastructure": {
                "provisioned": self.infrastructure_provisioned,
                "destroyed": self.infrastructure_destroyed,
                "resource_group": self.args.resource_group,
                "cluster_name": self.args.cluster_name,
            },
        }
        self.summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def run(self) -> None:
        self.prepare_artifacts()
        try:
            self.validate_approved_plan()
            self.verify_prerequisites()
            self.validate_image_plan_before_provision()
            self.provision_foundation()
            if not self.args.generate_only:
                if not self.args.provision:
                    self.refresh_kubeconfig()
                self.resolve_image_reference()
                self.attach_image_acr_if_needed()
                self.ensure_managed_istio()

            execution_index = 0
            plan = self.execution_plan()
            for pass_record in plan["passes"]:
                for key in pass_record["order"]:
                    execution_index += 1
                    record = self.run_condition(key, int(pass_record["pass"]), execution_index)
                    self.completed.append(record)
                    self.write_summary("running")
            self.write_summary("completed")
            if self.args.destroy_infrastructure_on_success:
                self.destroy_infrastructure("successful RQ2.2 rolling run")
                self.write_summary("completed")
        except Exception as exc:  # noqa: BLE001 - top-level artifact capture.
            self.write_summary("failed", str(exc))
            if self.active_rolling_pools and not self.args.keep_service2_nodepools:
                for nodepool in reversed(list(self.active_rolling_pools)):
                    try:
                        self.delete_rolling_nodepool(nodepool)
                    except Exception as cleanup_exc:  # noqa: BLE001
                        warn(f"Failed to delete active rolling nodepool {nodepool} after failure: {cleanup_exc}")
            if self.args.destroy_infrastructure_on_failure:
                try:
                    self.destroy_infrastructure("failed RQ2.2 rolling run")
                    self.write_summary("failed", str(exc))
                except Exception as destroy_exc:  # noqa: BLE001
                    warn(f"Failed to destroy infrastructure after failure: {destroy_exc}")
            raise


def main() -> int:
    args = parse_args()
    try:
        runner = RQ22ConfidentialRunner(args)
        runner.run()
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
