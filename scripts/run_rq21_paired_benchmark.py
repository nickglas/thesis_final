from __future__ import annotations

import argparse
import base64
from collections import Counter
import csv
import json
import math
import os
import random
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

from scripts.run_rq21_fully_controlled import (  # noqa: E402
    DEFAULT_CLIENT_POD,
    DEFAULT_CLUSTER_NAME,
    DEFAULT_LOCATION,
    DEFAULT_NODE_COUNT,
    DEFAULT_NODE_VM_SIZE,
    DEFAULT_NODEPOOL,
    DEFAULT_RESOURCE_GROUP,
    INFRA_DIR,
    PipelineError,
    RQ21PreflightRunner,
    default_kubeconfig_path,
    ensure_command,
    kubectl_json,
    kubectl_json_or_none,
    load_yaml,
    log,
    run_command,
    timestamp,
    utc_run_stamp,
    warn,
)


DEFAULT_PLAIN_CONFIG = "configs/rq2/2.1/rq2_1_chain2_plain.yaml"
DEFAULT_MTLS_CONFIG = "configs/rq2/2.1/rq2_1_chain2_mtls.yaml"

RESOURCE_METRIC_CATEGORIES = (
    "service_app_cpu_mcores",
    "service_app_memory_mib",
    "sidecar_cpu_mcores",
    "sidecar_memory_mib",
    "total_pod_cpu_mcores",
    "total_pod_memory_mib",
    "client_cpu_mcores",
    "client_memory_mib",
)


@dataclass
class ConditionContext:
    key: str
    condition_name: str
    source_config_path: Path
    effective_config_path: Path
    service_namespace: str
    client_namespace: str
    service_count: int
    condition_dir: Path
    manifest_dir: Path
    benchmark_dir: Path
    diagnostics_dir: Path
    resource_samples_path: Path


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
            raise PipelineError(
                f"Command failed with exit code {exit_code}: {' '.join(args)}"
            )


def save_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def load_manifest_documents(manifest_dir: Path) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for path in sorted(manifest_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            for document in yaml.safe_load_all(handle):
                if isinstance(document, dict):
                    item = dict(document)
                    item["_manifest_file"] = path.name
                    documents.append(item)
    return documents


def first_condition(raw_config: dict[str, Any]) -> dict[str, Any]:
    conditions = raw_config.get("conditions") or []
    if len(conditions) != 1 or not isinstance(conditions[0], dict):
        raise PipelineError("RQ2.1 paired configs must contain exactly one condition")
    return conditions[0]


def service_count_for_condition(condition: dict[str, Any]) -> int:
    if condition.get("type") != "chain":
        raise PipelineError("RQ2.1 paired runner supports only chain conditions")
    return len(condition.get("chain_split_points") or []) + 1


def container_specs(pod: dict[str, Any]) -> list[dict[str, Any]]:
    spec = pod.get("spec") or {}
    return [
        container
        for container in list(spec.get("containers") or []) + list(spec.get("initContainers") or [])
        if isinstance(container, dict)
    ]


def app_container_specs(pod: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        container
        for container in (pod.get("spec") or {}).get("containers") or []
        if isinstance(container, dict)
    ]


def init_container_specs(pod: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        container
        for container in (pod.get("spec") or {}).get("initContainers") or []
        if isinstance(container, dict)
    ]


def metric_container_specs(pod: dict[str, Any]) -> list[dict[str, Any]]:
    """Containers that must appear in steady-state resource samples."""
    containers = list(app_container_specs(pod))
    containers.extend(
        container
        for container in init_container_specs(pod)
        if str(container.get("name") or "") == "istio-proxy"
    )
    return containers


def container_names(containers: list[dict[str, Any]]) -> list[str]:
    return [
        str(container.get("name") or "")
        for container in containers
        if str(container.get("name") or "").strip()
    ]


def istio_proxy_container_type(pod: dict[str, Any]) -> str | None:
    if any(str(container.get("name") or "") == "istio-proxy" for container in app_container_specs(pod)):
        return "app"
    if any(str(container.get("name") or "") == "istio-proxy" for container in init_container_specs(pod)):
        return "init"
    return None


def status_by_container(pod: dict[str, Any]) -> dict[str, dict[str, Any]]:
    status = pod.get("status") or {}
    statuses = list(status.get("containerStatuses") or []) + list(status.get("initContainerStatuses") or [])
    return {
        str(item.get("name")): item
        for item in statuses
        if isinstance(item, dict)
    }


def container_ready(pod: dict[str, Any], name: str) -> bool:
    return bool(status_by_container(pod).get(name, {}).get("ready", False))


def pod_name(pod: dict[str, Any]) -> str:
    return str((pod.get("metadata") or {}).get("name") or "unknown")


def bad_pod_states(pod: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    name = pod_name(pod)
    phase = str((pod.get("status") or {}).get("phase") or "unknown")
    if phase in {"Pending", "Failed", "Unknown"}:
        errors.append(f"{name}: pod phase is {phase}")

    for condition in (pod.get("status") or {}).get("conditions") or []:
        if condition.get("type") == "PodScheduled" and condition.get("status") == "False":
            errors.append(f"{name}: pod scheduling failed ({condition.get('reason') or 'unknown'})")

    for status in status_by_container(pod).values():
        waiting = ((status.get("state") or {}).get("waiting") or {})
        reason = waiting.get("reason")
        if reason in {
            "CrashLoopBackOff",
            "ImagePullBackOff",
            "ErrImagePull",
            "CreateContainerConfigError",
            "CreateContainerError",
        }:
            errors.append(f"{name}/{status.get('name')}: container waiting reason is {reason}")
    return errors


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * (pct / 100.0)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[int(position)])
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return float(lower_value + (upper_value - lower_value) * (position - lower))


def maybe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_cpu_mcores(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("n"):
            return float(text[:-1]) / 1_000_000.0
        if text.endswith("u"):
            return float(text[:-1]) / 1000.0
        if text.endswith("m"):
            return float(text[:-1])
        return float(text) * 1000.0
    except ValueError:
        return None


def parse_memory_mib(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    suffixes = {
        "Ki": 1 / 1024,
        "Mi": 1,
        "Gi": 1024,
        "Ti": 1024 * 1024,
        "K": 1 / 1000,
        "M": 1_000_000 / (1024 * 1024),
        "G": 1_000_000_000 / (1024 * 1024),
    }
    for suffix, factor in suffixes.items():
        if text.endswith(suffix):
            try:
                return float(text[: -len(suffix)]) * factor
            except ValueError:
                return None
    try:
        return float(text) / (1024 * 1024)
    except ValueError:
        return None


def mean_or_none(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def stdev_or_none(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return float(math.sqrt(variance))


def numeric_summary(values: list[float]) -> dict[str, Any]:
    clean_values = [float(value) for value in values if isinstance(value, (int, float))]
    if not clean_values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "stdev": None,
            "min": None,
            "max": None,
        }
    return {
        "n": len(clean_values),
        "mean": mean_or_none(clean_values),
        "median": percentile(clean_values, 50),
        "p95": percentile(clean_values, 95),
        "p99": percentile(clean_values, 99),
        "stdev": stdev_or_none(clean_values),
        "min": min(clean_values),
        "max": max(clean_values),
    }


def empty_resource_metric_sample() -> dict[str, float]:
    return {category: 0.0 for category in RESOURCE_METRIC_CATEGORIES}


def parse_k8s_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text or text == "unknown":
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def seconds_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return float((end - start).total_seconds())


def pod_condition_timestamp(
    pod: dict[str, Any],
    condition_type: str,
    *,
    required_status: str = "True",
) -> datetime | None:
    for condition in (pod.get("status") or {}).get("conditions") or []:
        if condition.get("type") != condition_type:
            continue
        if required_status and str(condition.get("status") or "") != required_status:
            continue
        return parse_k8s_timestamp(condition.get("lastTransitionTime"))
    return None


def container_started_timestamp(pod: dict[str, Any], name: str) -> datetime | None:
    status = status_by_container(pod).get(name, {})
    running = ((status.get("state") or {}).get("running") or {})
    return parse_k8s_timestamp(running.get("startedAt"))


def pod_request_totals(pod: dict[str, Any]) -> dict[str, float]:
    totals = {
        "app_cpu_mcores_total": 0.0,
        "app_memory_mib_total": 0.0,
        "sidecar_cpu_mcores_total": 0.0,
        "sidecar_memory_mib_total": 0.0,
    }
    for container in metric_container_specs(pod):
        requests = (container.get("resources") or {}).get("requests") or {}
        cpu = parse_cpu_mcores(str(requests.get("cpu") or "")) or 0.0
        memory = parse_memory_mib(str(requests.get("memory") or "")) or 0.0
        if str(container.get("name") or "") == "istio-proxy":
            totals["sidecar_cpu_mcores_total"] += cpu
            totals["sidecar_memory_mib_total"] += memory
        else:
            totals["app_cpu_mcores_total"] += cpu
            totals["app_memory_mib_total"] += memory

    totals["pod_cpu_mcores_total"] = (
        totals["app_cpu_mcores_total"] + totals["sidecar_cpu_mcores_total"]
    )
    totals["pod_memory_mib_total"] = (
        totals["app_memory_mib_total"] + totals["sidecar_memory_mib_total"]
    )
    return totals


def mesh_control_plane_pods() -> list[dict[str, Any]]:
    payload = kubectl_json_or_none(["get", "pods", "-A", "-o", "json"])
    if not isinstance(payload, dict):
        return []

    records: list[dict[str, Any]] = []
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
        })
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "RQ2.1 paired performance runner for chain_2svc_plain vs "
            "chain_2svc_mtls. This does not run RQ2.2 and does not add chain_5svc."
        )
    )
    parser.add_argument("--plain-config", default=DEFAULT_PLAIN_CONFIG)
    parser.add_argument("--mtls-config", default=DEFAULT_MTLS_CONFIG)
    parser.add_argument("--results-root", default=str(REPO_ROOT / "results_exports"))
    parser.add_argument("--client-pod", default=DEFAULT_CLIENT_POD)
    parser.add_argument("--nodepool", default=DEFAULT_NODEPOOL)
    parser.add_argument("--provision", action="store_true")
    parser.add_argument("--provisioner", choices=["terraform"], default="terraform")
    parser.add_argument("--acr-name", default=None)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument(
        "--image-ref",
        default=None,
        help="Pinned image reference to use for both paired configs, bypassing image resolution/push.",
    )
    parser.add_argument("--image-tag", default=f"rq21-paired-{utc_run_stamp().lower()}")
    parser.add_argument("--local-image", default="thesis-inference:latest")
    parser.add_argument("--no-auto-push-missing-image", action="store_true")
    parser.add_argument("--resource-group", default=DEFAULT_RESOURCE_GROUP)
    parser.add_argument("--cluster-name", default=DEFAULT_CLUSTER_NAME)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--node-count", type=int, default=DEFAULT_NODE_COUNT)
    parser.add_argument("--node-vm-size", default=DEFAULT_NODE_VM_SIZE)
    parser.add_argument("--skip-mesh-enable", action="store_true")
    parser.add_argument(
        "--mesh-revision",
        default=None,
        help="Override mTLS kubernetes.mesh.revision. Use auto/latest/supported to select from AKS.",
    )
    parser.add_argument("--readiness-timeout", type=int, default=None)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use a tiny benchmark profile before running the full paired benchmark.",
    )
    parser.add_argument("--paired-passes", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=42)
    parser.add_argument(
        "--order",
        choices=["seeded", "plain-first", "mtls-first"],
        default="seeded",
        help="Execution order for pass 1; later passes alternate that order.",
    )
    parser.add_argument(
        "--preserve-namespaces",
        action="store_true",
        help="Keep condition namespaces after successful condition runs.",
    )
    parser.add_argument("--cleanup-on-failure", action="store_true")
    parser.add_argument(
        "--destroy-infrastructure-on-success",
        action="store_true",
        help="After a successful paired run, destroy the Terraform-managed AKS/ACR infrastructure.",
    )
    parser.add_argument(
        "--destroy-infrastructure-on-failure",
        action="store_true",
        help="After a failed paired run, destroy the Terraform-managed AKS/ACR infrastructure after diagnostics/namespace cleanup.",
    )
    parser.add_argument(
        "--disable-resource-sampling",
        action="store_true",
        help="Disable kubectl top based per-container resource sampling.",
    )
    parser.add_argument(
        "--resource-sample-interval-seconds",
        type=float,
        default=5.0,
    )
    parser.add_argument("--resource-sample-max-samples", type=int, default=100000)
    parser.add_argument(
        "--resource-metric-prime-timeout-seconds",
        type=float,
        default=180.0,
        help="Wait this long for kubectl top to expose benchmark pod/container metrics before each leg.",
    )
    parser.add_argument(
        "--resource-metric-prime-interval-seconds",
        type=float,
        default=5.0,
        help="Polling interval while waiting for benchmark pod/container metrics to appear.",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Write effective configs/manifests and static validation only; no live AKS benchmark.",
    )
    args = parser.parse_args()
    if args.build and not args.push:
        parser.error("--build requires --push")
    if args.image_ref and (args.push or args.build):
        parser.error("--image-ref cannot be combined with --push/--build")
    if (args.destroy_infrastructure_on_success or args.destroy_infrastructure_on_failure) and not args.provision:
        parser.error("infrastructure destroy flags require --provision")
    if args.paired_passes < 1:
        parser.error("--paired-passes must be at least 1")
    if args.resource_sample_interval_seconds < 0:
        parser.error("--resource-sample-interval-seconds must be non-negative")
    if args.resource_metric_prime_timeout_seconds <= 0:
        parser.error("--resource-metric-prime-timeout-seconds must be greater than 0")
    if args.resource_metric_prime_interval_seconds <= 0:
        parser.error("--resource-metric-prime-interval-seconds must be greater than 0")
    return args


class RQ21PairedBenchmarkRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.repo_root = REPO_ROOT
        self.kubeconfig_path = default_kubeconfig_path()
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig_path))

        self.source_paths = {
            "plain": (self.repo_root / args.plain_config).resolve(),
            "mtls": (self.repo_root / args.mtls_config).resolve(),
        }
        self.raw_configs = {
            "plain": load_yaml(self.source_paths["plain"]),
            "mtls": load_yaml(self.source_paths["mtls"]),
        }
        self.condition_names = {
            key: str(first_condition(config).get("name"))
            for key, config in self.raw_configs.items()
        }
        self.service_counts = {
            key: service_count_for_condition(first_condition(config))
            for key, config in self.raw_configs.items()
        }
        self.run_stamp = utc_run_stamp()
        self.artifact_dir = Path(args.results_root).resolve() / f"rq2_1_paired_{self.run_stamp}"
        self.config_dir = self.artifact_dir / "effective_configs"
        self.conditions_root = self.artifact_dir / "conditions"
        self.merged_dir = self.artifact_dir / "merged"
        self.static_dir = self.artifact_dir / "static_validation"
        self.run_metadata_path = self.artifact_dir / "rq21_paired_run_metadata.json"

        self.effective_config_paths: dict[str, Path] = {}
        self.effective_image_ref = ""
        self.mesh_revision = ""
        self.acr_name = args.acr_name or self._derive_acr_name()
        self.execution_plan = self._build_execution_plan()
        self.completed_conditions: list[dict[str, Any]] = []
        self.current_context: ConditionContext | None = None
        self.resources_deployed = False
        self.lifecycle_runner: RQ21PreflightRunner | None = None
        self.infrastructure_provisioned = False
        self.infrastructure_destroyed = False

    def _derive_acr_name(self) -> str | None:
        for config in (self.raw_configs["mtls"], self.raw_configs["plain"]):
            image = str((config.get("kubernetes") or {}).get("image") or "")
            if ".azurecr.io/" in image:
                return image.split(".azurecr.io/", 1)[0]
        return None

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

    def _build_execution_plan(self) -> dict[str, Any]:
        if self.args.order == "plain-first":
            first_order = ["plain", "mtls"]
        elif self.args.order == "mtls-first":
            first_order = ["mtls", "plain"]
        else:
            first_order = ["plain", "mtls"]
            random.Random(self.args.order_seed).shuffle(first_order)

        passes = []
        for pass_index in range(1, self.args.paired_passes + 1):
            order = list(first_order if pass_index % 2 == 1 else reversed(first_order))
            passes.append({"pass": pass_index, "order": order})
        return {
            "order_mode": self.args.order,
            "order_seed": self.args.order_seed,
            "paired_passes": self.args.paired_passes,
            "passes": passes,
        }

    def validate_configs(self) -> None:
        errors: list[str] = []
        if self.condition_names.get("plain") != "chain_2svc_plain":
            errors.append("Plain config must contain condition chain_2svc_plain")
        if self.condition_names.get("mtls") != "chain_2svc_mtls":
            errors.append("mTLS config must contain condition chain_2svc_mtls")
        if self.service_counts.get("plain") != 2 or self.service_counts.get("mtls") != 2:
            errors.append("RQ2.1 paired runner supports only chain_2svc")

        plain_condition = first_condition(self.raw_configs["plain"])
        mtls_condition = first_condition(self.raw_configs["mtls"])
        if (plain_condition.get("chain_split_points") or []) != (mtls_condition.get("chain_split_points") or []):
            errors.append("Plain and mTLS configs must use the same chain_split_points")

        for section in ("model", "benchmark", "grpc", "cpu_stabilisation", "carry_forward", "parity", "warmup_calibration"):
            if self.raw_configs["plain"].get(section) != self.raw_configs["mtls"].get(section):
                errors.append(f"Plain and mTLS configs must match section '{section}'")

        benchmark = self.raw_configs["plain"].get("benchmark") or {}
        if int(benchmark.get("rounds") or 0) != 1:
            errors.append(
                "RQ2.1 paired configs must set benchmark.rounds=1; use --paired-passes to interleave thesis-facing rounds"
            )

        plain_k8s = self.raw_configs["plain"].get("kubernetes") or {}
        mtls_k8s = self.raw_configs["mtls"].get("kubernetes") or {}
        for section in ("resources", "client_resources", "placement", "service_name_template", "grpc_port", "max_message_bytes"):
            if plain_k8s.get(section) != mtls_k8s.get(section):
                errors.append(f"Plain and mTLS kubernetes.{section} must match")
        if plain_k8s.get("security_condition") != "plain":
            errors.append("Plain config must set kubernetes.security_condition=plain")
        if bool((plain_k8s.get("mesh") or {}).get("enabled", False)):
            errors.append("Plain config must set kubernetes.mesh.enabled=false")
        mtls_mesh = mtls_k8s.get("mesh") or {}
        if mtls_k8s.get("security_condition") != "mtls":
            errors.append("mTLS config must set kubernetes.security_condition=mtls")
        if not bool(mtls_mesh.get("enabled", False)):
            errors.append("mTLS config must set kubernetes.mesh.enabled=true")
        if not bool(((mtls_mesh.get("authorization_policy") or {}).get("enabled", False))):
            errors.append("mTLS config must enable kubernetes.mesh.authorization_policy.enabled")

        if errors:
            raise PipelineError("RQ2.1 paired config validation failed:\n- " + "\n- ".join(errors))

    def verify_required_files(self) -> None:
        required_paths = [
            self.source_paths["plain"],
            self.source_paths["mtls"],
            self.repo_root / "run_k8s_experiment.py",
            self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py",
            self.repo_root / "scripts" / "run_rq21_fully_controlled.py",
            self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py",
        ]
        if self.args.provision:
            required_paths.extend([
                INFRA_DIR / "main.tf",
                INFRA_DIR / "variables.tf",
                INFRA_DIR / "outputs.tf",
            ])
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

    def prepare_artifact_dirs(self) -> None:
        for path in (
            self.artifact_dir,
            self.config_dir,
            self.conditions_root,
            self.merged_dir,
            self.static_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        (self.artifact_dir / "execution_order.json").write_text(
            json.dumps(self.execution_plan, indent=2),
            encoding="utf-8",
        )

    def lifecycle_helper(self) -> RQ21PreflightRunner:
        if self.lifecycle_runner is None:
            lifecycle_root = self.artifact_dir / "lifecycle"
            lifecycle_manifest_dir = lifecycle_root / "manifests"
            self.lifecycle_runner = RQ21PreflightRunner(
                self._helper_args(
                    config_path=self.source_paths["mtls"],
                    results_root=lifecycle_root,
                    manifest_output_dir=lifecycle_manifest_dir,
                    preserve_existing=True,
                )
            )
            self.lifecycle_runner.prepare_artifact_dirs()
        return self.lifecycle_runner

    def _configured_mtls_image_ref(self) -> str:
        return str((self.raw_configs["mtls"].get("kubernetes") or {}).get("image") or "").strip()

    def _configured_mesh_revision(self) -> str:
        return str(
            self.args.mesh_revision
            or ((self.raw_configs["mtls"].get("kubernetes") or {}).get("mesh") or {}).get("revision")
            or ""
        ).strip()

    def _is_auto_mesh_revision(self, revision: str) -> bool:
        return revision.lower() in {"auto", "latest", "supported"}

    def prepare_infrastructure(self) -> None:
        lifecycle: RQ21PreflightRunner | None = None
        if (
            self.args.provision
            or self.args.push
            or self.args.build
            or self._is_auto_mesh_revision(self._configured_mesh_revision())
        ):
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
            image_resolution = {
                "reason": "explicit --image-ref",
                "pinned_ref": self.effective_image_ref,
            }
        elif self.args.provision or self.args.push or self.args.build:
            lifecycle = self.lifecycle_helper()
            self.effective_image_ref = lifecycle.resolve_image_reference()
            image_resolution_path = lifecycle.state.artifact_dir / "image_resolution.json"
            if image_resolution_path.exists():
                image_resolution = json.loads(image_resolution_path.read_text(encoding="utf-8"))
            else:
                image_resolution = {
                    "reason": "lifecycle image resolution",
                    "pinned_ref": self.effective_image_ref,
                }
        else:
            self.effective_image_ref = self._configured_mtls_image_ref()
            image_resolution = {
                "reason": "existing pinned image",
                "pinned_ref": self.effective_image_ref,
            }

        if "@sha256:" not in self.effective_image_ref:
            raise PipelineError(
                "RQ2.1 paired runner requires a pinned digest image reference; update the configs, pass --image-ref, "
                "or rerun with --push --build."
            )

        revision = self._configured_mesh_revision()
        if not revision:
            raise PipelineError("RQ2.1 mTLS config must pin kubernetes.mesh.revision")

        if lifecycle is not None:
            lifecycle.prepare_effective_config(
                resolve_live_revision=True,
                image_ref=self.effective_image_ref,
            )
            self.mesh_revision = str(lifecycle.mesh.get("revision") or lifecycle.args.mesh_revision or revision)
            lifecycle.ensure_managed_istio()
        else:
            self.mesh_revision = revision

        (self.artifact_dir / "image_reference.txt").write_text(
            self.effective_image_ref + "\n",
            encoding="utf-8",
        )
        image_resolution.update({
            "paired_artifact_dir": str(self.artifact_dir),
            "pinned_ref": self.effective_image_ref,
        })
        (self.artifact_dir / "image_resolution.json").write_text(
            json.dumps(image_resolution, indent=2),
            encoding="utf-8",
        )
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
                    "mesh_revision": self.mesh_revision,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def destroy_infrastructure(self, reason: str) -> None:
        if self.infrastructure_destroyed:
            return
        if not self.args.provision:
            warn("Skipping infrastructure destroy because --provision was not used for this paired run.")
            return

        lifecycle = self.lifecycle_helper()
        log(f"Destroying Terraform-managed AKS/ACR infrastructure after {reason}.")
        lifecycle._terraform_init()
        run_command(
            [
                "terraform",
                "destroy",
                "-auto-approve",
                "-input=false",
                *lifecycle._terraform_var_args(),
            ],
            cwd=INFRA_DIR,
        )
        self.infrastructure_destroyed = True
        (self.artifact_dir / "infrastructure_lifecycle.json").write_text(
            json.dumps(
                {
                    "provision_requested": bool(self.args.provision),
                    "provisioned": self.infrastructure_provisioned,
                    "destroyed": self.infrastructure_destroyed,
                    "destroy_reason": reason,
                    "destroyed_at": datetime.now(timezone.utc).isoformat(),
                    "resource_group": self.args.resource_group,
                    "cluster_name": self.args.cluster_name,
                    "acr_name": self.acr_name,
                    "nodepool": self.args.nodepool,
                    "node_count": self.args.node_count,
                    "node_vm_size": self.args.node_vm_size,
                    "mesh_revision": self.mesh_revision,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def write_effective_configs(self) -> None:
        for key in ("plain", "mtls"):
            raw = deepcopy(self.raw_configs[key])
            raw.setdefault("kubernetes", {})
            raw["kubernetes"]["image"] = self.effective_image_ref
            raw["kubernetes"].setdefault("placement", {})
            raw["kubernetes"]["placement"]["node_pool"] = self.args.nodepool
            if self.args.readiness_timeout is not None:
                raw["kubernetes"]["readiness_timeout"] = float(self.args.readiness_timeout)
            if key == "mtls":
                raw["kubernetes"].setdefault("mesh", {})
                raw["kubernetes"]["mesh"]["revision"] = self.mesh_revision
            if self.args.smoke:
                self._apply_smoke_profile(raw)
            path = self.config_dir / f"rq2_1_chain2_{key}_effective.yaml"
            save_yaml(path, raw)
            self.effective_config_paths[key] = path

    def _apply_smoke_profile(self, raw: dict[str, Any]) -> None:
        raw.setdefault("benchmark", {})
        raw["benchmark"].update({
            "rounds": 1,
            "warmup_iterations": 2,
            "measured_iterations": 3,
            "cooldown_seconds": 0,
        })
        raw.setdefault("parity", {})
        raw["parity"]["num_inputs"] = 1
        raw.setdefault("warmup_calibration", {})
        raw["warmup_calibration"].update({
            "window": 2,
            "cv_threshold": 1.0,
            "max_extra_iterations": 0,
        })

    def verify_cluster_reachable(self) -> None:
        result = run_command(["kubectl", "cluster-info"], capture_output=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PipelineError(f"Kubernetes cluster is not reachable: {detail or result.returncode}")
        context = run_command(["kubectl", "config", "current-context"], capture_output=True, check=False)
        log(f"Kubernetes context: {(context.stdout or '').strip() or 'unknown'}")
        first_line = (result.stdout or "").splitlines()[0] if result.stdout else "unknown"
        log(f"Cluster endpoint: {first_line}")

    def condition_context(self, key: str, pass_index: int, execution_index: int) -> ConditionContext:
        raw = load_yaml(self.effective_config_paths[key])
        condition = first_condition(raw)
        k8s = raw.get("kubernetes") or {}
        condition_name = str(condition["name"])
        condition_dir = self.conditions_root / f"pass{pass_index:02d}_{execution_index:02d}_{condition_name}"
        return ConditionContext(
            key=key,
            condition_name=condition_name,
            source_config_path=self.source_paths[key],
            effective_config_path=self.effective_config_paths[key],
            service_namespace=str(k8s.get("namespace")),
            client_namespace=str(k8s.get("client_namespace") or k8s.get("namespace")),
            service_count=service_count_for_condition(condition),
            condition_dir=condition_dir,
            manifest_dir=condition_dir / "manifests",
            benchmark_dir=condition_dir / "benchmark",
            diagnostics_dir=condition_dir / "diagnostics",
            resource_samples_path=condition_dir / "resource_samples.csv",
        )

    def generate_manifests(self, context: ConditionContext) -> dict[str, Any]:
        context.manifest_dir.mkdir(parents=True, exist_ok=True)
        log(f"Generating manifests for {context.condition_name} into {context.manifest_dir}.")
        run_command([
            sys.executable,
            str(self.repo_root / "k8s" / "aks" / "generate_aks_manifests.py"),
            "--config",
            str(context.effective_config_path),
            "--nodepool",
            self.args.nodepool,
            "--output-dir",
            str(context.manifest_dir),
        ])
        return self.static_manifest_validation(context)

    def static_manifest_validation(self, context: ConditionContext) -> dict[str, Any]:
        docs = load_manifest_documents(context.manifest_dir)
        errors: list[str] = []
        kinds = [str(doc.get("kind") or "") for doc in docs]
        namespaces = {
            str((doc.get("metadata") or {}).get("name")): doc
            for doc in docs
            if doc.get("kind") == "Namespace"
        }
        deployments = [doc for doc in docs if doc.get("kind") == "Deployment"]

        if context.key == "plain":
            forbidden = {"PeerAuthentication", "AuthorizationPolicy", "ServiceAccount"}
            observed_forbidden = sorted(kind for kind in kinds if kind in forbidden)
            if observed_forbidden:
                errors.append(f"Plain manifests generated mesh resources: {observed_forbidden}")
            service_labels = ((namespaces.get(context.service_namespace) or {}).get("metadata") or {}).get("labels") or {}
            client_labels = ((namespaces.get(context.client_namespace) or {}).get("metadata") or {}).get("labels") or {}
            for namespace_name, labels in (
                (context.service_namespace, service_labels),
                (context.client_namespace, client_labels),
            ):
                if labels.get("istio.io/rev") or labels.get("istio-injection") == "enabled":
                    errors.append(f"Plain namespace {namespace_name} has a mesh injection label")
            for deployment in deployments:
                annotations = (
                    ((deployment.get("spec") or {}).get("template") or {})
                    .get("metadata", {})
                    .get("annotations", {})
                    or {}
                )
                sidecar_keys = sorted(key for key in annotations if key.startswith("sidecar.istio.io/"))
                if sidecar_keys:
                    errors.append(
                        f"Plain deployment {(deployment.get('metadata') or {}).get('name')} has sidecar annotations {sidecar_keys}"
                    )
        else:
            service_labels = ((namespaces.get(context.service_namespace) or {}).get("metadata") or {}).get("labels") or {}
            client_labels = ((namespaces.get(context.client_namespace) or {}).get("metadata") or {}).get("labels") or {}
            if service_labels.get("istio.io/rev") != self.mesh_revision:
                errors.append(
                    f"mTLS service namespace missing istio.io/rev={self.mesh_revision}; found {service_labels.get('istio.io/rev')}"
                )
            if client_labels.get("istio.io/rev") or client_labels.get("istio-injection") == "enabled":
                errors.append("mTLS client namespace must remain non-mesh")
            service_accounts = [doc for doc in docs if doc.get("kind") == "ServiceAccount"]
            if len(service_accounts) != context.service_count:
                errors.append(f"mTLS manifests should include {context.service_count} explicit ServiceAccounts")
            if "PeerAuthentication" not in kinds:
                errors.append("mTLS manifests missing PeerAuthentication")
            if "AuthorizationPolicy" not in kinds:
                errors.append("mTLS manifests missing AuthorizationPolicy")
            required_annotations = {
                "sidecar.istio.io/proxyCPU",
                "sidecar.istio.io/proxyCPULimit",
                "sidecar.istio.io/proxyMemory",
                "sidecar.istio.io/proxyMemoryLimit",
            }
            for deployment in deployments:
                annotations = (
                    ((deployment.get("spec") or {}).get("template") or {})
                    .get("metadata", {})
                    .get("annotations", {})
                    or {}
                )
                missing = sorted(required_annotations - set(annotations))
                if missing:
                    errors.append(
                        f"mTLS deployment {(deployment.get('metadata') or {}).get('name')} missing proxy annotations {missing}"
                    )

        summary = {
            "condition": context.condition_name,
            "manifest_dir": str(context.manifest_dir),
            "kinds": kinds,
            "passed": not errors,
            "errors": errors,
        }
        out_path = self.static_dir / f"{context.condition_name}.json"
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if errors:
            raise PipelineError(
                f"Static manifest validation failed for {context.condition_name}:\n- "
                + "\n- ".join(errors)
            )
        return summary

    def namespace_exists(self, namespace: str) -> bool:
        result = run_command(
            ["kubectl", "get", "namespace", namespace],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    def wait_for_namespace_deletion(self, namespace: str, timeout_seconds: int = 180) -> None:
        deadline = time.monotonic() + timeout_seconds
        while self.namespace_exists(namespace):
            if time.monotonic() >= deadline:
                raise PipelineError(f"Timed out waiting for namespace deletion: {namespace}")
            time.sleep(2)

    def cleanup_namespaces(self, context: ConditionContext) -> None:
        for namespace in sorted({context.service_namespace, context.client_namespace}):
            if self.namespace_exists(namespace):
                log(f"Force-deleting pods in namespace {namespace}.")
                run_command(
                    [
                        "kubectl",
                        "delete",
                        "pod",
                        "--all",
                        "-n",
                        namespace,
                        "--ignore-not-found=true",
                        "--force",
                        "--grace-period=0",
                        "--wait=false",
                    ],
                    check=False,
                )
            log(f"Deleting namespace {namespace}.")
            run_command(
                ["kubectl", "delete", "namespace", namespace, "--ignore-not-found=true", "--wait=false"],
                check=False,
            )
        for namespace in sorted({context.service_namespace, context.client_namespace}):
            self.wait_for_namespace_deletion(namespace)
        self.resources_deployed = False

    def apply_manifests(self, context: ConditionContext) -> None:
        self.cleanup_namespaces(context)
        ordered_files = [
            context.manifest_dir / "00_namespace.yaml",
            context.manifest_dir / "01_service_accounts.yaml",
            context.manifest_dir / f"{context.condition_name}.yaml",
            context.manifest_dir / "99_benchmark_client.yaml",
        ]
        for path in ordered_files:
            if not path.exists():
                if path.name == "01_service_accounts.yaml":
                    continue
                raise PipelineError(f"Generated manifest is missing: {path}")
            log(f"Applying {path.name} for {context.condition_name}.")
            run_command(["kubectl", "apply", "-f", str(path)])
        self.resources_deployed = True

    def wait_for_ready(self, context: ConditionContext) -> None:
        timeout_seconds = int(self.args.readiness_timeout or 180)
        deadline_seconds = timeout_seconds + 60
        deployments = self._deployment_names(context)
        if len(deployments) != context.service_count:
            raise PipelineError(
                f"Expected {context.service_count} deployments for {context.condition_name}, found {len(deployments)}"
            )
        for deployment in deployments:
            log(f"Waiting for deployment {deployment} rollout.")
            run_command([
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment}",
                "-n",
                context.service_namespace,
                f"--timeout={deadline_seconds}s",
            ])
        log(f"Waiting for service pods for {context.condition_name} to become Ready.")
        run_command([
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-n",
            context.service_namespace,
            "-l",
            f"condition={context.condition_name},workload-role=service",
            f"--timeout={deadline_seconds}s",
        ])
        log(f"Waiting for benchmark client for {context.condition_name} to become Ready.")
        run_command([
            "kubectl",
            "wait",
            "--for=condition=Ready",
            f"pod/{self.args.client_pod}",
            "-n",
            context.client_namespace,
            f"--timeout={deadline_seconds}s",
        ])

    def _deployment_names(self, context: ConditionContext) -> list[str]:
        result = run_command([
            "kubectl",
            "get",
            "deployments",
            "-n",
            context.service_namespace,
            "-l",
            f"condition={context.condition_name},workload-role=service",
            "-o",
            "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
        ], capture_output=True, check=False)
        return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]

    def service_pods(self, context: ConditionContext) -> list[dict[str, Any]]:
        payload = kubectl_json([
            "get",
            "pods",
            "-n",
            context.service_namespace,
            "-l",
            f"condition={context.condition_name},workload-role=service",
            "-o",
            "json",
        ])
        return list(payload.get("items") or [])

    def client_pod(self, context: ConditionContext) -> dict[str, Any]:
        return kubectl_json([
            "get",
            "pod",
            self.args.client_pod,
            "-n",
            context.client_namespace,
            "-o",
            "json",
        ])

    def validate_plain_runtime(self, context: ConditionContext) -> dict[str, Any]:
        errors: list[str] = []
        service_pods = self.service_pods(context)
        client_pod = self.client_pod(context)
        namespace = kubectl_json(["get", "namespace", context.service_namespace, "-o", "json"])
        labels = (namespace.get("metadata") or {}).get("labels") or {}
        if labels.get("istio.io/rev") or labels.get("istio-injection") == "enabled":
            errors.append("Plain service namespace has a mesh injection label")
        peer_auths = kubectl_json_or_none([
            "get",
            "peerauthentication.security.istio.io",
            "-n",
            context.service_namespace,
            "-o",
            "json",
        ])
        authz = kubectl_json_or_none([
            "get",
            "authorizationpolicy.security.istio.io",
            "-n",
            context.service_namespace,
            "-o",
            "json",
        ])
        if (peer_auths or {}).get("items"):
            errors.append("Plain namespace unexpectedly contains PeerAuthentication resources")
        if (authz or {}).get("items"):
            errors.append("Plain namespace unexpectedly contains AuthorizationPolicy resources")

        nodes = set()
        for pod in service_pods:
            name = pod_name(pod)
            nodes.add(str((pod.get("spec") or {}).get("nodeName") or "unknown"))
            names = [str(container.get("name")) for container in container_specs(pod)]
            app_names = [str(container.get("name")) for container in app_container_specs(pod)]
            if "istio-proxy" in names:
                errors.append(f"{name}: plain service pod contains istio-proxy")
            if "inference" not in app_names or not container_ready(pod, "inference"):
                errors.append(f"{name}: inference app container is not Ready")
            errors.extend(bad_pod_states(pod))
        nodes.discard("unknown")
        if len(nodes) != 1:
            errors.append(f"Plain service pods are not strictly colocated on one node: {sorted(nodes)}")

        client_container_names = [str(container.get("name")) for container in app_container_specs(client_pod)]
        all_client_names = [str(container.get("name")) for container in container_specs(client_pod)]
        if client_container_names != ["client"]:
            errors.append(f"Plain benchmark client must have one app container named client; found {client_container_names}")
        if "istio-proxy" in all_client_names:
            errors.append("Plain benchmark client contains istio-proxy")
        errors.extend(bad_pod_states(client_pod))

        result = {
            "condition": context.condition_name,
            "passed": not errors,
            "errors": errors,
            "service_pod_nodes": sorted(nodes),
            "client_node": (client_pod.get("spec") or {}).get("nodeName"),
        }
        (context.diagnostics_dir / "plain_runtime_validation.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        if errors:
            raise PipelineError("Plain runtime validation failed:\n- " + "\n- ".join(errors))
        return result

    def mtls_mesh_config(self) -> dict[str, Any]:
        config_path = self.effective_config_paths.get("mtls") or self.source_paths["mtls"]
        config = load_yaml(config_path)
        mesh = ((config.get("kubernetes") or {}).get("mesh") or {})
        return mesh if isinstance(mesh, dict) else {}

    def expected_mtls_authorization_principal(self, context: ConditionContext) -> str:
        mesh = self.mtls_mesh_config()
        authz = mesh.get("authorization_policy") or {}
        source_segment = str(authz.get("source_segment_index") or "1")
        service_accounts = mesh.get("service_accounts") or {}
        source_service_account = str(service_accounts.get(source_segment) or "")
        return f"cluster.local/ns/{context.service_namespace}/sa/{source_service_account}"

    def authorization_policy_principals(self, policy: dict[str, Any]) -> list[str]:
        principals: list[str] = []
        for rule in (policy.get("spec") or {}).get("rules") or []:
            for source in rule.get("from") or []:
                source_block = source.get("source") or {}
                principals.extend(str(item) for item in source_block.get("principals") or [])
        return principals

    def validate_mtls_authorization_policy(
        self,
        context: ConditionContext,
        authz_items: list[dict[str, Any]],
    ) -> tuple[list[str], dict[str, Any]]:
        errors: list[str] = []
        mesh = self.mtls_mesh_config()
        authz = mesh.get("authorization_policy") or {}
        expected_name = str(authz.get("name") or "downstream-service1-only")
        downstream_segment = str(authz.get("downstream_segment_index") or "2")
        expected_principal = self.expected_mtls_authorization_principal(context)
        policy = next(
            (
                item
                for item in authz_items
                if str((item.get("metadata") or {}).get("name") or "") == expected_name
            ),
            None,
        )
        summary = {
            "expected_policy_name": expected_name,
            "expected_downstream_segment_index": downstream_segment,
            "expected_allowed_principal": expected_principal,
            "observed_policy_names": [
                str((item.get("metadata") or {}).get("name") or "")
                for item in authz_items
            ],
            "selects_downstream_service2": False,
            "allows_only_service1_principal": False,
        }
        if not policy:
            errors.append(f"mTLS runtime missing AuthorizationPolicy {expected_name}")
            return errors, summary

        spec = policy.get("spec") or {}
        selector = (spec.get("selector") or {}).get("matchLabels") or {}
        observed_principals = sorted(set(self.authorization_policy_principals(policy)))
        rules = spec.get("rules") or []
        unrestricted_source_rule = False
        unexpected_source_constraints: list[dict[str, Any]] = []
        for rule in rules:
            from_entries = rule.get("from") or []
            if not from_entries:
                unrestricted_source_rule = True
                continue
            for source in from_entries:
                source_block = source.get("source") or {}
                principals = [str(item) for item in source_block.get("principals") or []]
                unsupported_keys = sorted(
                    key
                    for key in source_block
                    if key not in {"principals"}
                )
                if principals != [expected_principal] or unsupported_keys:
                    unexpected_source_constraints.append({
                        "principals": principals,
                        "unsupported_source_keys": unsupported_keys,
                    })
        summary.update({
            "observed_selector": selector,
            "observed_action": str(spec.get("action") or "ALLOW"),
            "observed_allowed_principals": observed_principals,
            "unrestricted_source_rule": unrestricted_source_rule,
            "unexpected_source_constraints": unexpected_source_constraints,
        })

        selector_ok = (
            selector.get("condition") == context.condition_name
            and selector.get("segment-index") == downstream_segment
            and selector.get("workload-role") == "service"
        )
        summary["selects_downstream_service2"] = selector_ok
        if not selector_ok:
            errors.append(
                f"AuthorizationPolicy {expected_name} must select condition={context.condition_name}, "
                f"segment-index={downstream_segment}, workload-role=service"
            )
        if str(spec.get("action") or "ALLOW") != "ALLOW":
            errors.append(f"AuthorizationPolicy {expected_name} must use action=ALLOW")

        principal_ok = (
            observed_principals == [expected_principal]
            and not unrestricted_source_rule
            and not unexpected_source_constraints
        )
        summary["allows_only_service1_principal"] = principal_ok
        if not principal_ok:
            errors.append(
                f"AuthorizationPolicy {expected_name} must allow only source principal {expected_principal}; "
                f"observed {observed_principals}"
            )
        return errors, summary

    def validate_mtls_runtime(self, context: ConditionContext) -> dict[str, Any]:
        errors: list[str] = []
        service_pods = self.service_pods(context)
        client_pod = self.client_pod(context)
        namespace = kubectl_json(["get", "namespace", context.service_namespace, "-o", "json"])
        client_namespace = kubectl_json(["get", "namespace", context.client_namespace, "-o", "json"])
        service_labels = (namespace.get("metadata") or {}).get("labels") or {}
        client_labels = (client_namespace.get("metadata") or {}).get("labels") or {}
        if service_labels.get("istio.io/rev") != self.mesh_revision:
            errors.append(
                f"mTLS service namespace missing istio.io/rev={self.mesh_revision}; found {service_labels.get('istio.io/rev')}"
            )
        if client_labels.get("istio.io/rev") or client_labels.get("istio-injection") == "enabled":
            errors.append("mTLS client namespace must remain non-mesh")

        peer_auths = kubectl_json_or_none([
            "get",
            "peerauthentication.security.istio.io",
            "-n",
            context.service_namespace,
            "-o",
            "json",
        ])
        authz = kubectl_json_or_none([
            "get",
            "authorizationpolicy.security.istio.io",
            "-n",
            context.service_namespace,
            "-o",
            "json",
        ])
        peer_items = list((peer_auths or {}).get("items") or [])
        authz_items = list((authz or {}).get("items") or [])
        default_peer = False
        strict_peer = False
        for item in peer_items:
            spec = item.get("spec") or {}
            selector = (spec.get("selector") or {}).get("matchLabels") or {}
            mode = str(((spec.get("mtls") or {}).get("mode") or "")).upper()
            if not selector and mode == "PERMISSIVE":
                default_peer = True
            if selector.get("segment-index") == "2" and selector.get("condition") == context.condition_name and mode == "STRICT":
                strict_peer = True
        if not default_peer:
            errors.append("mTLS runtime missing namespace-default PERMISSIVE PeerAuthentication")
        if not strict_peer:
            errors.append("mTLS runtime missing downstream STRICT PeerAuthentication for segment 2")
        if not authz_items:
            errors.append("mTLS runtime missing AuthorizationPolicy")
        authz_errors, authz_summary = self.validate_mtls_authorization_policy(context, authz_items)
        errors.extend(authz_errors)

        nodes = set()
        required_annotations = {
            "sidecar.istio.io/proxyCPU",
            "sidecar.istio.io/proxyCPULimit",
            "sidecar.istio.io/proxyMemory",
            "sidecar.istio.io/proxyMemoryLimit",
        }
        for pod in service_pods:
            name = pod_name(pod)
            nodes.add(str((pod.get("spec") or {}).get("nodeName") or "unknown"))
            names = [str(container.get("name")) for container in container_specs(pod)]
            app_names = [str(container.get("name")) for container in app_container_specs(pod)]
            if "istio-proxy" not in names:
                errors.append(f"{name}: mTLS service pod is missing istio-proxy")
            if "inference" not in app_names or not container_ready(pod, "inference"):
                errors.append(f"{name}: inference app container is not Ready")
            if not container_ready(pod, "istio-proxy"):
                errors.append(f"{name}: istio-proxy is not Ready")
            if str((pod.get("spec") or {}).get("serviceAccountName") or "") in {"", "default"}:
                errors.append(f"{name}: service pod is missing an explicit ServiceAccount")
            annotations = (pod.get("metadata") or {}).get("annotations") or {}
            missing = sorted(required_annotations - set(annotations))
            if missing:
                errors.append(f"{name}: missing proxy annotations {missing}")
            errors.extend(bad_pod_states(pod))
        nodes.discard("unknown")
        if len(nodes) != 1:
            errors.append(f"mTLS service pods are not strictly colocated on one node: {sorted(nodes)}")

        client_container_names = [str(container.get("name")) for container in app_container_specs(client_pod)]
        all_client_names = [str(container.get("name")) for container in container_specs(client_pod)]
        if client_container_names != ["client"]:
            errors.append(
                f"mTLS benchmark client must have one app container named client; found {client_container_names}"
            )
        if "istio-proxy" in all_client_names:
            errors.append("mTLS benchmark client contains istio-proxy")
        errors.extend(bad_pod_states(client_pod))

        result = {
            "condition": context.condition_name,
            "passed": not errors,
            "errors": errors,
            "service_pod_nodes": sorted(nodes),
            "client_node": (client_pod.get("spec") or {}).get("nodeName"),
            "peer_authentication_count": len(peer_items),
            "authorization_policy_count": len(authz_items),
            "authorization_policy_validation": authz_summary,
        }
        (context.diagnostics_dir / "mtls_runtime_validation.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        if errors:
            raise PipelineError("mTLS runtime validation failed:\n- " + "\n- ".join(errors))
        return result

    def namespace_pod_events(self, namespace: str) -> dict[str, list[dict[str, Any]]]:
        payload = kubectl_json_or_none(["get", "events", "-n", namespace, "-o", "json"])
        if not isinstance(payload, dict):
            return {}
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in payload.get("items") or []:
            involved = item.get("involvedObject") or {}
            if involved.get("kind") != "Pod":
                continue
            pod_ref = str(involved.get("name") or "")
            if not pod_ref:
                continue
            grouped.setdefault(pod_ref, []).append(
                {
                    "reason": str(item.get("reason") or ""),
                    "type": str(item.get("type") or ""),
                    "message": str(item.get("message") or ""),
                    "timestamp": str(
                        item.get("eventTime")
                        or item.get("lastTimestamp")
                        or item.get("firstTimestamp")
                        or ((item.get("metadata") or {}).get("creationTimestamp") or "")
                    ),
                }
            )
        return grouped

    def node_allocatable(self, node_name: str) -> dict[str, Any]:
        payload = kubectl_json_or_none(["get", "node", node_name, "-o", "json"])
        if not isinstance(payload, dict):
            return {"node_name": node_name, "cpu_mcores": None, "memory_mib": None}
        allocatable = ((payload.get("status") or {}).get("allocatable") or {})
        return {
            "node_name": node_name,
            "cpu_mcores": parse_cpu_mcores(str(allocatable.get("cpu") or "")),
            "memory_mib": parse_memory_mib(str(allocatable.get("memory") or "")),
        }

    def capture_operational_overhead(self, context: ConditionContext) -> dict[str, Any]:
        service_pods = self.service_pods(context)
        client_pod = self.client_pod(context)
        events_by_pod = self.namespace_pod_events(context.service_namespace)
        service_nodes = sorted(
            {
                str((pod.get("spec") or {}).get("nodeName") or "unknown")
                for pod in service_pods
                if str((pod.get("spec") or {}).get("nodeName") or "unknown") not in {"", "unknown"}
            }
        )
        node_allocatable = {
            node_name: self.node_allocatable(node_name)
            for node_name in service_nodes
        }

        service_records: list[dict[str, Any]] = []
        for pod in service_pods:
            pod_meta = pod.get("metadata") or {}
            pod_spec = pod.get("spec") or {}
            pod_name_value = str(pod_meta.get("name") or "unknown")
            all_container_names = container_names(container_specs(pod))
            sidecar_container_type = istio_proxy_container_type(pod)
            creation_at = parse_k8s_timestamp(pod_meta.get("creationTimestamp"))
            scheduled_at = pod_condition_timestamp(pod, "PodScheduled")
            ready_at = pod_condition_timestamp(pod, "Ready")
            app_names = [
                str(container.get("name") or "")
                for container in app_container_specs(pod)
                if str(container.get("name") or "") != "istio-proxy"
            ]
            app_started_candidates = [
                timestamp_value
                for timestamp_value in (
                    container_started_timestamp(pod, name)
                    for name in app_names
                )
                if timestamp_value is not None
            ]
            app_started_at = max(app_started_candidates) if app_started_candidates else None
            sidecar_started_at = container_started_timestamp(pod, "istio-proxy")
            requests = pod_request_totals(pod)
            pod_events = events_by_pod.get(pod_name_value, [])
            failed_scheduling_events = [
                event
                for event in pod_events
                if event.get("reason") in {"FailedScheduling", "NotTriggerScaleUp"}
                or (
                    event.get("type") == "Warning"
                    and "schedul" in str(event.get("message") or "").lower()
                )
            ]
            status = status_by_container(pod)
            sidecar_status = status.get("istio-proxy", {})
            service_records.append(
                {
                    "pod_name": pod_name_value,
                    "node_name": str(pod_spec.get("nodeName") or "unknown"),
                    "creation_timestamp": pod_meta.get("creationTimestamp"),
                    "scheduled_timestamp": scheduled_at.isoformat() if scheduled_at else None,
                    "ready_timestamp": ready_at.isoformat() if ready_at else None,
                    "app_started_timestamp": app_started_at.isoformat() if app_started_at else None,
                    "sidecar_started_timestamp": sidecar_started_at.isoformat() if sidecar_started_at else None,
                    "scheduling_delay_seconds": seconds_between(creation_at, scheduled_at),
                    "schedule_to_ready_seconds": seconds_between(scheduled_at, ready_at),
                    "app_started_delay_seconds": seconds_between(scheduled_at, app_started_at),
                    "sidecar_started_delay_seconds": seconds_between(scheduled_at, sidecar_started_at),
                    "sidecar_present": "istio-proxy" in all_container_names,
                    "sidecar_container_type": sidecar_container_type,
                    "sidecar_native_init": sidecar_container_type == "init",
                    "sidecar_ready": bool(sidecar_status.get("ready", False)),
                    "sidecar_restart_count": int(sidecar_status.get("restartCount") or 0),
                    "failed_scheduling_events": failed_scheduling_events,
                    **requests,
                }
            )

        client_requests = pod_request_totals(client_pod)
        client_node_name = str((client_pod.get("spec") or {}).get("nodeName") or "unknown")
        service_app_requested_cpu = sum(record["app_cpu_mcores_total"] for record in service_records)
        service_sidecar_requested_cpu = sum(record["sidecar_cpu_mcores_total"] for record in service_records)
        service_app_requested_memory = sum(record["app_memory_mib_total"] for record in service_records)
        service_sidecar_requested_memory = sum(record["sidecar_memory_mib_total"] for record in service_records)
        service_total_requested_cpu = sum(record["pod_cpu_mcores_total"] for record in service_records)
        service_total_requested_memory = sum(record["pod_memory_mib_total"] for record in service_records)
        benchmark_requested_cpu_total = service_total_requested_cpu + (
            client_requests["pod_cpu_mcores_total"] if client_node_name in service_nodes else 0.0
        )
        benchmark_requested_memory_total = service_total_requested_memory + (
            client_requests["pod_memory_mib_total"] if client_node_name in service_nodes else 0.0
        )

        primary_node = service_nodes[0] if len(service_nodes) == 1 else None
        primary_allocatable = node_allocatable.get(primary_node) if primary_node else None
        headroom_cpu = None
        headroom_memory = None
        if primary_allocatable and isinstance(primary_allocatable.get("cpu_mcores"), (int, float)):
            headroom_cpu = float(primary_allocatable["cpu_mcores"]) - benchmark_requested_cpu_total
        if primary_allocatable and isinstance(primary_allocatable.get("memory_mib"), (int, float)):
            headroom_memory = float(primary_allocatable["memory_mib"]) - benchmark_requested_memory_total

        docs = load_manifest_documents(context.manifest_dir)
        kind_counts = dict(sorted(Counter(str(doc.get("kind") or "") for doc in docs).items()))
        control_plane_pods = mesh_control_plane_pods() if context.key == "mtls" else []
        benchmark_nodes = set(service_nodes)
        if client_node_name not in {"", "unknown"}:
            benchmark_nodes.add(client_node_name)
        shared_control_plane_pods = [
            pod
            for pod in control_plane_pods
            if str(pod.get("node_name") or "") in benchmark_nodes
        ]
        control_plane_colocation = {
            "shares_benchmark_node": bool(shared_control_plane_pods),
            "benchmark_node_names": sorted(benchmark_nodes),
            "shared_node_names": sorted(
                {
                    str(pod.get("node_name") or "")
                    for pod in shared_control_plane_pods
                    if str(pod.get("node_name") or "").strip()
                }
            ),
            "control_plane_pod_names": [
                f"{pod.get('namespace')}/{pod.get('pod_name')}"
                for pod in shared_control_plane_pods
            ],
            "control_plane_pods_on_shared_nodes": shared_control_plane_pods,
        }
        sidecar_total = sum(
            1
            for record in service_records
            if record.get("sidecar_present")
        )
        summary = {
            "service_pod_count": len(service_records),
            "service_nodes": service_nodes,
            "service_scheduling_delay_seconds_mean": mean_or_none(
                [
                    value
                    for value in (record.get("scheduling_delay_seconds") for record in service_records)
                    if isinstance(value, (int, float))
                ]
            ),
            "service_schedule_to_ready_seconds_mean": mean_or_none(
                [
                    value
                    for value in (record.get("schedule_to_ready_seconds") for record in service_records)
                    if isinstance(value, (int, float))
                ]
            ),
            "service_app_started_delay_seconds_mean": mean_or_none(
                [
                    value
                    for value in (record.get("app_started_delay_seconds") for record in service_records)
                    if isinstance(value, (int, float))
                ]
            ),
            "service_sidecar_started_delay_seconds_mean": mean_or_none(
                [
                    value
                    for value in (record.get("sidecar_started_delay_seconds") for record in service_records)
                    if isinstance(value, (int, float))
                ]
            ),
            "service_failed_scheduling_event_count": sum(
                len(record.get("failed_scheduling_events") or [])
                for record in service_records
            ),
            "service_app_requested_cpu_mcores_total": service_app_requested_cpu,
            "service_sidecar_requested_cpu_mcores_total": service_sidecar_requested_cpu,
            "service_total_requested_cpu_mcores_total": service_total_requested_cpu,
            "service_app_requested_memory_mib_total": service_app_requested_memory,
            "service_sidecar_requested_memory_mib_total": service_sidecar_requested_memory,
            "service_total_requested_memory_mib_total": service_total_requested_memory,
            "client_requested_cpu_mcores_total": client_requests["pod_cpu_mcores_total"],
            "client_requested_memory_mib_total": client_requests["pod_memory_mib_total"],
            "benchmark_requested_cpu_mcores_total": benchmark_requested_cpu_total,
            "benchmark_requested_memory_mib_total": benchmark_requested_memory_total,
            "node_request_headroom_cpu_mcores": headroom_cpu,
            "node_request_headroom_memory_mib": headroom_memory,
            "mesh_control_plane_shares_benchmark_node": control_plane_colocation["shares_benchmark_node"],
            "mesh_control_plane_shared_node_names": control_plane_colocation["shared_node_names"],
            "mesh_control_plane_shared_pod_names": control_plane_colocation["control_plane_pod_names"],
        }
        deployment_complexity = {
            "aks_enablement_step_count": 1 if context.key == "mtls" else 0,
            "kubernetes_object_count": len(docs),
            "kubernetes_object_counts_by_kind": kind_counts,
            "always_on_control_plane_pod_count": len(control_plane_pods),
            "per_workload_injected_container_count": (
                float(sidecar_total) / float(len(service_records)) if service_records else 0.0
            ),
            "total_injected_container_count": sidecar_total,
        }
        operational_complexity = {
            "mesh_revision": self.mesh_revision if context.key == "mtls" else None,
            "sidecar_readiness_failure_count": sum(
                1
                for record in service_records
                if record.get("sidecar_present") and not record.get("sidecar_ready")
            ),
            "sidecar_restart_total": sum(int(record.get("sidecar_restart_count") or 0) for record in service_records),
        }
        payload = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "condition": context.condition_name,
            "condition_key": context.key,
            "service_pods": service_records,
            "client": {
                "pod_name": pod_name(client_pod),
                "node_name": client_node_name,
                **client_requests,
            },
            "node_allocatable": node_allocatable,
            "summary": summary,
            "deployment_complexity": deployment_complexity,
            "operational_complexity": operational_complexity,
            "control_plane_colocation": control_plane_colocation,
        }
        (context.diagnostics_dir / "operational_overhead.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        return payload

    def run_mtls_security_preflight(self, context: ConditionContext) -> Path:
        log("Running existing RQ2.1 mTLS/security preflight before the mTLS benchmark.")
        preflight_root = context.condition_dir / "security_preflight"
        preflight_manifest_dir = context.condition_dir / "security_preflight_manifests"
        preflight = RQ21PreflightRunner(
            self._helper_args(
                config_path=context.effective_config_path,
                results_root=preflight_root,
                manifest_output_dir=preflight_manifest_dir,
                preserve_existing=True,
            )
        )
        preflight.args.provision = False
        preflight.args.push = False
        preflight.args.build = False
        preflight.args.skip_mesh_enable = True
        preflight.args.no_auto_push_missing_image = True
        try:
            preflight.run()
        except Exception as exc:
            preflight.handle_failure(exc)
            raise
        marker = context.condition_dir / "security_preflight_artifact.txt"
        marker.write_text(str(preflight.state.artifact_dir) + "\n", encoding="utf-8")
        return preflight.state.artifact_dir

    def read_mtls_security_preflight_result(self, artifact_dir: Path | None) -> dict[str, Any]:
        if artifact_dir is None:
            return {
                "passed": False,
                "artifact_path": None,
                "reason": "mTLS security preflight was not run",
            }
        metadata_path = artifact_dir / "rq21_preflight_metadata.json"
        if not metadata_path.exists():
            return {
                "passed": False,
                "artifact_path": str(artifact_dir),
                "metadata_path": str(metadata_path),
                "reason": "mTLS security preflight metadata was not created",
            }
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        enforcement = metadata.get("enforcement_validation") or {}
        full_chain = enforcement.get("full_chain_probe") or {}
        direct_denial = enforcement.get("non_mesh_direct_denial_probe") or {}
        passed = (
            bool(metadata.get("preflight_passed"))
            and bool(enforcement.get("passed"))
            and bool(full_chain.get("succeeded"))
            and bool(direct_denial.get("blocked_as_expected"))
        )
        return {
            "passed": passed,
            "artifact_path": str(artifact_dir),
            "metadata_path": str(metadata_path),
            "preflight_passed": bool(metadata.get("preflight_passed")),
            "enforcement_validation_passed": bool(enforcement.get("passed")),
            "full_chain_positive_probe_passed": bool(full_chain.get("succeeded")),
            "non_mesh_direct_denial_probe_passed": bool(direct_denial.get("blocked_as_expected")),
            "authorization_policy_expected_principal": enforcement.get("authorization_policy_expected_principal"),
            "errors": metadata.get("errors") or enforcement.get("errors") or [],
            "limitations": metadata.get("limitations") or [],
        }

    def write_file_into_pod(self, context: ConditionContext, remote_path: str, content: str) -> None:
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
            context.client_namespace,
            self.args.client_pod,
            "--",
            "python",
            "-c",
            code,
            encoded,
            remote_path,
        ])

    def inject_runtime_metadata(self, context: ConditionContext) -> None:
        run_command([
            sys.executable,
            str(self.repo_root / "scripts" / "inject_k8s_runtime_metadata.py"),
            "--config",
            str(context.effective_config_path),
            "--namespace",
            context.service_namespace,
            "--client-namespace",
            context.client_namespace,
            "--client-pod",
            self.args.client_pod,
        ])

    def resource_metric_prime_status_path(self, context: ConditionContext) -> Path:
        return context.condition_dir / "resource_metric_prime_status.json"

    def expected_resource_metric_containers(self, context: ConditionContext) -> dict[str, dict[str, list[str]]]:
        expectations: dict[str, dict[str, list[str]]] = {}
        for pod in self.service_pods(context):
            name = pod_name(pod)
            containers = sorted(
                {
                    str(container.get("name") or "")
                    for container in metric_container_specs(pod)
                    if str(container.get("name") or "").strip()
                }
            )
            if containers:
                expectations.setdefault(context.service_namespace, {})[name] = containers

        client = self.client_pod(context)
        client_name = pod_name(client)
        client_containers = sorted(
            {
                str(container.get("name") or "")
                for container in metric_container_specs(client)
                if str(container.get("name") or "").strip()
            }
        )
        if client_containers:
            expectations.setdefault(context.client_namespace, {})[client_name] = client_containers
        return expectations

    def top_container_metrics_for_namespace(self, namespace: str) -> tuple[dict[str, list[str]], str | None]:
        result = run_command(
            [
                "kubectl",
                "top",
                "pod",
                "--containers",
                "--no-headers",
                "-n",
                namespace,
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            return {}, detail or f"kubectl top exited with {result.returncode}"

        observed: dict[str, set[str]] = {}
        for line in (result.stdout or "").splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            pod, container = parts[:2]
            observed.setdefault(pod, set()).add(container)
        return {pod: sorted(containers) for pod, containers in observed.items()}, None

    def missing_resource_metric_containers(
        self,
        expected: dict[str, dict[str, list[str]]],
        observed: dict[str, dict[str, list[str]]],
    ) -> dict[str, dict[str, list[str]]]:
        missing: dict[str, dict[str, list[str]]] = {}
        for namespace, expected_pods in expected.items():
            observed_pods = observed.get(namespace) or {}
            for pod, expected_containers in expected_pods.items():
                observed_containers = set(observed_pods.get(pod) or [])
                missing_containers = sorted(set(expected_containers) - observed_containers)
                if missing_containers:
                    missing.setdefault(namespace, {})[pod] = missing_containers
        return missing

    def format_missing_resource_metrics(self, missing: dict[str, dict[str, list[str]]]) -> str:
        parts: list[str] = []
        for namespace, pods in sorted(missing.items()):
            for pod, containers in sorted(pods.items()):
                parts.append(f"{namespace}/{pod} containers={','.join(containers)}")
        return "; ".join(parts)

    def wait_for_resource_metrics_ready(self, context: ConditionContext) -> dict[str, Any] | None:
        if self.args.disable_resource_sampling:
            return None

        expected = self.expected_resource_metric_containers(context)
        status_path = self.resource_metric_prime_status_path(context)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        timeout_seconds = float(self.args.resource_metric_prime_timeout_seconds)
        interval_seconds = float(self.args.resource_metric_prime_interval_seconds)
        started = time.monotonic()
        started_at = datetime.now(timezone.utc).isoformat()
        deadline = started + timeout_seconds
        attempts = 0
        log(
            f"Priming resource metrics for {context.condition_name}; waiting for kubectl top "
            "to report benchmark service and client containers."
        )

        while True:
            attempts += 1
            observed: dict[str, dict[str, list[str]]] = {}
            errors: dict[str, str] = {}
            for namespace in sorted(expected):
                namespace_observed, error = self.top_container_metrics_for_namespace(namespace)
                observed[namespace] = namespace_observed
                if error:
                    errors[namespace] = error

            missing = self.missing_resource_metric_containers(expected, observed)
            elapsed = time.monotonic() - started
            status: dict[str, Any] = {
                "condition": context.condition_name,
                "started_at": started_at,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "ready": not errors and not missing,
                "attempts": attempts,
                "elapsed_seconds": round(elapsed, 3),
                "timeout_seconds": timeout_seconds,
                "interval_seconds": interval_seconds,
                "expected": expected,
                "observed": observed,
                "missing": missing,
                "errors": errors,
            }
            status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
            if status["ready"]:
                log(
                    f"Resource metrics are ready for {context.condition_name} "
                    f"after {attempts} check(s)."
                )
                return status

            now = time.monotonic()
            if now >= deadline:
                details: list[str] = []
                if missing:
                    details.append("missing " + self.format_missing_resource_metrics(missing))
                if errors:
                    details.append(
                        "kubectl top errors "
                        + "; ".join(f"{namespace}: {error}" for namespace, error in sorted(errors.items()))
                    )
                raise PipelineError(
                    f"Timed out waiting for resource metrics for {context.condition_name}: "
                    + ("; ".join(details) if details else "no benchmark pod metrics appeared")
                )

            time.sleep(min(interval_seconds, max(0.0, deadline - now)))

    def start_resource_sampler(self, context: ConditionContext) -> subprocess.Popen | None:
        if self.args.disable_resource_sampling:
            return None
        stdout_path = context.condition_dir / "resource_sampler_stdout.txt"
        stderr_path = context.condition_dir / "resource_sampler_stderr.txt"
        status_path = context.condition_dir / "resource_sampler_status.json"
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        command = [
            sys.executable,
            str(self.repo_root / "scripts" / "sample_k8s_resources.py"),
            "--all-namespaces",
            "--interval-seconds",
            str(self.args.resource_sample_interval_seconds),
            "--samples",
            str(self.args.resource_sample_max_samples),
            "--output",
            str(context.resource_samples_path),
        ]
        process = subprocess.Popen(
            command,
            cwd=str(self.repo_root),
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
        process._rq21_stdout_handle = stdout_handle  # type: ignore[attr-defined]
        process._rq21_stderr_handle = stderr_handle  # type: ignore[attr-defined]
        status_path.write_text(
            json.dumps(
                {
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "command": command,
                    "output_csv": str(context.resource_samples_path),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return process

    def stop_resource_sampler(self, context: ConditionContext, process: subprocess.Popen | None) -> None:
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for attr in ("_rq21_stdout_handle", "_rq21_stderr_handle"):
            handle = getattr(process, attr, None)
            if handle is not None:
                handle.close()
        status_path = context.condition_dir / "resource_sampler_status.json"
        status = {}
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
        status.update({
            "stopped_at": datetime.now(timezone.utc).isoformat(),
            "returncode": process.returncode,
            "samples_file_exists": context.resource_samples_path.exists(),
        })
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    def copy_results_with_fallback(self, context: ConditionContext, source_path: str, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if destination_path.exists():
            shutil.rmtree(destination_path)
        result = run_command(
            [
                "kubectl",
                "cp",
                f"{context.client_namespace}/{self.args.client_pod}:{source_path}",
                str(destination_path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return

        warn(f"kubectl cp failed for {source_path}; attempting Python tar-stream fallback.")
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
                source_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        extracted_path = destination_path.parent / Path(source_path).name
        if extracted_path.exists() and extracted_path != destination_path:
            if extracted_path.is_dir():
                shutil.rmtree(extracted_path)
            else:
                extracted_path.unlink()
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            archive.extractall(path=destination_path.parent)
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
        if return_code != 0:
            raise PipelineError(
                f"kubectl tar-stream fallback failed for {source_path}: {stderr.strip() or return_code}"
            )
        if extracted_path.exists() and extracted_path != destination_path:
            shutil.move(str(extracted_path), str(destination_path))

    def run_condition_benchmark(self, context: ConditionContext, pass_index: int) -> None:
        log(f"Running benchmark for {context.condition_name}.")
        self.inject_runtime_metadata(context)
        remote_config = f"/tmp/rq21_paired/{context.condition_name}_config.yaml"
        remote_output = f"/tmp/rq21_paired/{context.condition_name}_pass{pass_index:02d}_{utc_run_stamp()}"
        self.write_file_into_pod(
            context,
            remote_config,
            context.effective_config_path.read_text(encoding="utf-8"),
        )
        run_command([
            "kubectl",
            "exec",
            "-n",
            context.client_namespace,
            self.args.client_pod,
            "--",
            "rm",
            "-rf",
            remote_output,
        ], check=False)

        self.wait_for_resource_metrics_ready(context)
        sampler = self.start_resource_sampler(context)
        try:
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
        finally:
            self.stop_resource_sampler(context, sampler)

        run_command([
            "kubectl",
            "exec",
            "-n",
            context.client_namespace,
            self.args.client_pod,
            "--",
            "test",
            "-d",
            remote_output,
        ])
        self.copy_results_with_fallback(context, remote_output, context.benchmark_dir)
        (context.condition_dir / "benchmark_remote_output_path.txt").write_text(
            remote_output + "\n",
            encoding="utf-8",
        )
        run_command([
            "kubectl",
            "exec",
            "-n",
            context.client_namespace,
            self.args.client_pod,
            "--",
            "rm",
            "-rf",
            remote_output,
        ], check=False)

    def gather_diagnostics(self, context: ConditionContext) -> None:
        context.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        commands = {
            "service_pods_wide.txt": ["get", "pods", "-n", context.service_namespace, "-o", "wide"],
            "client_pods_wide.txt": ["get", "pods", "-n", context.client_namespace, "-o", "wide"],
            "service_deployments.txt": ["get", "deployments", "-n", context.service_namespace, "-o", "wide"],
            "service_events.txt": ["get", "events", "-n", context.service_namespace, "--sort-by=.lastTimestamp"],
            "client_events.txt": ["get", "events", "-n", context.client_namespace, "--sort-by=.lastTimestamp"],
            "peer_authentication.txt": [
                "get",
                "peerauthentication.security.istio.io",
                "-n",
                context.service_namespace,
                "-o",
                "yaml",
            ],
            "authorization_policy.txt": [
                "get",
                "authorizationpolicy.security.istio.io",
                "-n",
                context.service_namespace,
                "-o",
                "yaml",
            ],
            "service_logs_inference.txt": [
                "logs",
                "-n",
                context.service_namespace,
                "-l",
                f"condition={context.condition_name},workload-role=service",
                "-c",
                "inference",
                "--tail=200",
                "--prefix=true",
            ],
            "service_logs_istio_proxy.txt": [
                "logs",
                "-n",
                context.service_namespace,
                "-l",
                f"condition={context.condition_name},workload-role=service",
                "-c",
                "istio-proxy",
                "--tail=200",
                "--prefix=true",
            ],
            "client_logs.txt": [
                "logs",
                "-n",
                context.client_namespace,
                self.args.client_pod,
                "-c",
                "client",
                "--tail=200",
            ],
        }
        for file_name, kubectl_args in commands.items():
            result = run_command(["kubectl", *kubectl_args], capture_output=True, check=False)
            (context.diagnostics_dir / file_name).write_text(
                (result.stdout or "") + (result.stderr or ""),
                encoding="utf-8",
            )

    def run_condition_once(self, key: str, pass_index: int, execution_index: int) -> None:
        context = self.condition_context(key, pass_index, execution_index)
        self.current_context = context
        context.condition_dir.mkdir(parents=True, exist_ok=True)
        context.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        static_summary = self.generate_manifests(context)

        try:
            self.apply_manifests(context)
            self.wait_for_ready(context)
            if key == "plain":
                validation_artifact = self.validate_plain_runtime(context)
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
            self.run_condition_benchmark(context, pass_index)
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
                "operational_overhead": operational_overhead,
                "security_preflight_artifact": str(security_preflight_artifact) if security_preflight_artifact else None,
                "security_validation": security_validation,
                "security_validation_passed": security_validation_passed,
                "service_namespace": context.service_namespace,
                "client_namespace": context.client_namespace,
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

    def read_condition_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        fieldnames: list[str] | None = None
        for record in self.completed_conditions:
            raw_path = Path(record["benchmark_dir"]) / "raw_iterations.csv"
            if not raw_path.exists():
                raise PipelineError(f"Missing raw benchmark artifact: {raw_path}")
            with raw_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if fieldnames is None:
                    fieldnames = reader.fieldnames or []
                elif reader.fieldnames != fieldnames:
                    raise PipelineError(
                        f"raw_iterations.csv header mismatch for {record['condition']}: "
                        f"{reader.fieldnames} != {fieldnames}"
                    )
                for row in reader:
                    row["paired_pass"] = str(record["pass"])
                    row["condition_key"] = str(record["condition_key"])
                    row["execution_index"] = str(record["execution_index"])
                    rows.append(row)
        return rows

    def summarize_latency(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        by_key: dict[str, list[dict[str, Any]]] = {"plain": [], "mtls": []}
        for row in rows:
            by_key.setdefault(str(row.get("condition_key")), []).append(row)

        summaries: dict[str, Any] = {}
        for key, key_rows in by_key.items():
            latencies = [value for value in (maybe_float(row.get("end_to_end_ms")) for row in key_rows) if value is not None]
            non_compute = [
                value
                for value in (maybe_float(row.get("non_compute_overhead_ms")) for row in key_rows)
                if value is not None
            ]
            total_compute = [
                value
                for value in (maybe_float(row.get("total_compute_ms")) for row in key_rows)
                if value is not None
            ]
            hop_forward_means = {}
            for hop in range(1, 6):
                values = [
                    value
                    for value in (maybe_float(row.get(f"hop_{hop}_forward_ms")) for row in key_rows)
                    if value is not None
                ]
                if values:
                    hop_forward_means[f"hop_{hop}_forward_ms_mean"] = mean_or_none(values)
            activation_means = {}
            for metric in (
                "total_activation_bytes",
                "hop_1_activation_bytes",
                "hop_2_activation_bytes",
            ):
                values = [
                    value
                    for value in (maybe_float(row.get(metric)) for row in key_rows)
                    if value is not None
                ]
                activation_means[f"{metric}_mean"] = mean_or_none(values)
            summaries[key] = {
                "condition": key_rows[0].get("condition") if key_rows else self.condition_names.get(key),
                "n": len(latencies),
                "mean_ms": mean_or_none(latencies),
                "median_ms": percentile(latencies, 50) if latencies else None,
                "p95_ms": percentile(latencies, 95) if latencies else None,
                "p99_ms": percentile(latencies, 99) if latencies else None,
                "non_compute_overhead_ms_mean": mean_or_none(non_compute),
                "total_compute_ms_mean": mean_or_none(total_compute),
                **hop_forward_means,
                **activation_means,
            }

        plain = summaries.get("plain") or {}
        mtls = summaries.get("mtls") or {}
        plain_mean = plain.get("mean_ms")
        mtls_mean = mtls.get("mean_ms")
        plain_p95 = plain.get("p95_ms")
        mtls_p95 = mtls.get("p95_ms")
        comparison = {
            "mean_latency_overhead_ms": (
                mtls_mean - plain_mean
                if isinstance(plain_mean, (int, float)) and isinstance(mtls_mean, (int, float))
                else None
            ),
            "mean_latency_overhead_pct": (
                ((mtls_mean - plain_mean) / plain_mean) * 100.0
                if isinstance(plain_mean, (int, float))
                and isinstance(mtls_mean, (int, float))
                and plain_mean > 0
                else None
            ),
            "p95_latency_overhead_ms": (
                mtls_p95 - plain_p95
                if isinstance(plain_p95, (int, float)) and isinstance(mtls_p95, (int, float))
                else None
            ),
        }
        for metric in (
            "total_activation_bytes_mean",
            "hop_1_activation_bytes_mean",
            "hop_2_activation_bytes_mean",
        ):
            plain_value = plain.get(metric)
            mtls_value = mtls.get(metric)
            comparison[f"{metric}_delta"] = (
                mtls_value - plain_value
                if isinstance(plain_value, (int, float)) and isinstance(mtls_value, (int, float))
                else None
            )
        return {"by_condition": summaries, "comparison": comparison}

    def summarize_resource_samples(self) -> dict[str, Any]:
        summaries: dict[str, Any] = {}
        for key in ("plain", "mtls"):
            records = [
                record
                for record in self.completed_conditions
                if str(record.get("condition_key")) == key
            ]
            if not records:
                summaries[key] = {
                    "available": False,
                    "reason": "no completed condition runs were recorded",
                }
                continue

            aggregated: dict[str, list[float]] = {
                category: [] for category in RESOURCE_METRIC_CATEGORIES
            }
            failures: list[dict[str, Any]] = []
            passes_covered: set[int] = set()
            service_app_sample_row_count = 0
            sidecar_sample_row_count = 0
            client_sample_row_count = 0

            for record in records:
                path = Path(record["resource_samples"])
                if not path.exists():
                    failures.append({
                        "pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "resource_samples": str(path),
                        "reason": "resource sample CSV was not created; metrics-server may be unavailable",
                    })
                    continue

                per_timestamp: dict[str, dict[str, float]] = {}
                observed_namespaces: set[str] = set()
                service_namespace_rows = 0
                service_app_rows = 0
                sidecar_rows = 0
                observed_sidecar_rows = 0
                client_namespace_rows = 0
                with path.open("r", encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        namespace = str(row.get("namespace") or "")
                        if namespace:
                            observed_namespaces.add(namespace)
                        if namespace not in {record["service_namespace"], record["client_namespace"]}:
                            continue
                        container_name = str(row.get("container_name") or "")
                        if namespace == record["service_namespace"] and container_name == "istio-proxy":
                            observed_sidecar_rows += 1
                        timestamp_value = str(row.get("timestamp") or "unknown")
                        bucket = per_timestamp.setdefault(timestamp_value, empty_resource_metric_sample())
                        cpu = parse_cpu_mcores(str(row.get("cpu_usage") or ""))
                        memory = parse_memory_mib(str(row.get("memory_usage") or ""))
                        if cpu is None or memory is None:
                            continue

                        if namespace == record["client_namespace"]:
                            client_namespace_rows += 1
                            client_sample_row_count += 1
                            bucket["client_cpu_mcores"] += cpu
                            bucket["client_memory_mib"] += memory
                        elif container_name == "istio-proxy":
                            service_namespace_rows += 1
                            sidecar_rows += 1
                            sidecar_sample_row_count += 1
                            bucket["sidecar_cpu_mcores"] += cpu
                            bucket["sidecar_memory_mib"] += memory
                        else:
                            service_namespace_rows += 1
                            service_app_rows += 1
                            service_app_sample_row_count += 1
                            bucket["service_app_cpu_mcores"] += cpu
                            bucket["service_app_memory_mib"] += memory

                if not per_timestamp:
                    failures.append({
                        "pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "resource_samples": str(path),
                        "reason": "resource sample CSV had no rows for the condition namespaces",
                        "observed_namespaces": sorted(observed_namespaces),
                    })
                    continue
                if service_namespace_rows == 0:
                    failures.append({
                        "pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "resource_samples": str(path),
                        "reason": "resource sample CSV had no service-namespace rows for the benchmarked condition",
                        "observed_namespaces": sorted(observed_namespaces),
                        "client_namespace_rows": client_namespace_rows,
                    })
                    continue
                if key == "plain" and observed_sidecar_rows > 0:
                    failures.append({
                        "pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "resource_samples": str(path),
                        "reason": "plain resource sample CSV contained istio-proxy rows",
                        "observed_namespaces": sorted(observed_namespaces),
                        "service_app_rows": service_app_rows,
                        "observed_sidecar_rows": observed_sidecar_rows,
                        "sidecar_rows": sidecar_rows,
                        "client_namespace_rows": client_namespace_rows,
                    })
                    continue
                if key == "mtls" and sidecar_rows == 0:
                    failures.append({
                        "pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "resource_samples": str(path),
                        "reason": "mTLS resource sample CSV had zero istio-proxy rows",
                        "observed_namespaces": sorted(observed_namespaces),
                        "service_app_rows": service_app_rows,
                        "client_namespace_rows": client_namespace_rows,
                    })
                    continue

                passes_covered.add(int(record["pass"]))
                for sample in per_timestamp.values():
                    sample["total_pod_cpu_mcores"] = (
                        sample["service_app_cpu_mcores"] + sample["sidecar_cpu_mcores"]
                    )
                    sample["total_pod_memory_mib"] = (
                        sample["service_app_memory_mib"] + sample["sidecar_memory_mib"]
                    )
                    for category in RESOURCE_METRIC_CATEGORIES:
                        aggregated[category].append(sample[category])

            sample_count = len(aggregated["service_app_cpu_mcores"])
            if failures:
                summaries[key] = {
                    "available": False,
                    "reason": "one or more required resource sample artifacts were incomplete",
                    "sample_count": sample_count,
                    "passes_covered": sorted(passes_covered),
                    "service_app_sample_row_count": service_app_sample_row_count,
                    "sidecar_sample_row_count": sidecar_sample_row_count,
                    "client_sample_row_count": client_sample_row_count,
                    "sidecar_metrics_available": sidecar_sample_row_count > 0,
                    "failures": failures,
                }
                continue
            if sample_count == 0:
                summaries[key] = {
                    "available": False,
                    "reason": "resource sample aggregation produced no usable steady-state samples",
                }
                continue

            summaries[key] = {
                "available": True,
                "sample_count": sample_count,
                "passes_covered": sorted(passes_covered),
                "service_app_sample_row_count": service_app_sample_row_count,
                "sidecar_sample_row_count": sidecar_sample_row_count,
                "client_sample_row_count": client_sample_row_count,
                "sidecar_metrics_available": sidecar_sample_row_count > 0,
                **{
                    f"{category}_mean": mean_or_none(values)
                    for category, values in aggregated.items()
                },
            }

        plain = summaries.get("plain") or {}
        mtls = summaries.get("mtls") or {}
        comparison = {}
        for metric in (
            "service_app_cpu_mcores_mean",
            "service_app_memory_mib_mean",
            "sidecar_cpu_mcores_mean",
            "sidecar_memory_mib_mean",
            "total_pod_cpu_mcores_mean",
            "total_pod_memory_mib_mean",
            "client_cpu_mcores_mean",
            "client_memory_mib_mean",
        ):
            plain_value = plain.get(metric)
            mtls_value = mtls.get(metric)
            if isinstance(plain_value, (int, float)) and isinstance(mtls_value, (int, float)):
                comparison[f"{metric}_overhead"] = mtls_value - plain_value
            elif metric.startswith("sidecar_") and isinstance(mtls_value, (int, float)):
                comparison[f"{metric}_overhead"] = mtls_value
        return {"by_condition": summaries, "comparison": comparison}

    def summarize_operational_overhead(self) -> dict[str, Any]:
        summaries: dict[str, Any] = {}
        for key in ("plain", "mtls"):
            records = [
                record
                for record in self.completed_conditions
                if str(record.get("condition_key")) == key and isinstance(record.get("operational_overhead"), dict)
            ]
            if not records:
                summaries[key] = {
                    "available": False,
                    "reason": "no operational-overhead records were captured",
                }
                continue

            operational_records = [record["operational_overhead"] for record in records]
            summary_metrics = [payload.get("summary") or {} for payload in operational_records]
            deployment_complexity = (operational_records[0].get("deployment_complexity") or {}) if operational_records else {}
            operational_complexity = (operational_records[0].get("operational_complexity") or {}) if operational_records else {}

            def metric_mean(metric: str) -> float | None:
                return mean_or_none(
                    [
                        float(summary[metric])
                        for summary in summary_metrics
                        if isinstance(summary.get(metric), (int, float))
                    ]
                )

            colocation_records = [
                payload.get("control_plane_colocation") or {}
                for payload in operational_records
                if isinstance(payload.get("control_plane_colocation"), dict)
            ]
            shared_node_names = sorted(
                {
                    str(node)
                    for item in colocation_records
                    for node in (item.get("shared_node_names") or [])
                    if str(node).strip()
                }
            )
            control_plane_pod_names = sorted(
                {
                    str(name)
                    for item in colocation_records
                    for name in (item.get("control_plane_pod_names") or [])
                    if str(name).strip()
                }
            )
            control_plane_colocation = {
                "shares_benchmark_node": any(
                    bool(item.get("shares_benchmark_node"))
                    for item in colocation_records
                ),
                "shared_node_names": shared_node_names,
                "control_plane_pod_names": control_plane_pod_names,
            }

            summaries[key] = {
                "available": True,
                "passes_covered": sorted({int(record["pass"]) for record in records}),
                "service_pod_count_total": sum(int((payload.get("summary") or {}).get("service_pod_count") or 0) for payload in operational_records),
                "service_scheduling_delay_seconds_mean": metric_mean("service_scheduling_delay_seconds_mean"),
                "service_schedule_to_ready_seconds_mean": metric_mean("service_schedule_to_ready_seconds_mean"),
                "service_app_started_delay_seconds_mean": metric_mean("service_app_started_delay_seconds_mean"),
                "service_sidecar_started_delay_seconds_mean": metric_mean("service_sidecar_started_delay_seconds_mean"),
                "service_failed_scheduling_event_count": sum(
                    int((payload.get("summary") or {}).get("service_failed_scheduling_event_count") or 0)
                    for payload in operational_records
                ),
                "service_app_requested_cpu_mcores_total": metric_mean("service_app_requested_cpu_mcores_total"),
                "service_sidecar_requested_cpu_mcores_total": metric_mean("service_sidecar_requested_cpu_mcores_total"),
                "service_total_requested_cpu_mcores_total": metric_mean("service_total_requested_cpu_mcores_total"),
                "service_app_requested_memory_mib_total": metric_mean("service_app_requested_memory_mib_total"),
                "service_sidecar_requested_memory_mib_total": metric_mean("service_sidecar_requested_memory_mib_total"),
                "service_total_requested_memory_mib_total": metric_mean("service_total_requested_memory_mib_total"),
                "client_requested_cpu_mcores_total": metric_mean("client_requested_cpu_mcores_total"),
                "client_requested_memory_mib_total": metric_mean("client_requested_memory_mib_total"),
                "benchmark_requested_cpu_mcores_total": metric_mean("benchmark_requested_cpu_mcores_total"),
                "benchmark_requested_memory_mib_total": metric_mean("benchmark_requested_memory_mib_total"),
                "node_request_headroom_cpu_mcores": metric_mean("node_request_headroom_cpu_mcores"),
                "node_request_headroom_memory_mib": metric_mean("node_request_headroom_memory_mib"),
                "deployment_complexity": deployment_complexity,
                "operational_complexity": operational_complexity,
                "control_plane_colocation": control_plane_colocation,
            }

        plain = summaries.get("plain") or {}
        mtls = summaries.get("mtls") or {}

        def overhead(metric: str) -> float | None:
            plain_value = plain.get(metric)
            mtls_value = mtls.get(metric)
            if isinstance(plain_value, (int, float)) and isinstance(mtls_value, (int, float)):
                return float(mtls_value - plain_value)
            return None

        plain_complexity = plain.get("deployment_complexity") or {}
        mtls_complexity = mtls.get("deployment_complexity") or {}
        comparison = {
            "service_scheduling_delay_seconds_overhead": overhead("service_scheduling_delay_seconds_mean"),
            "service_schedule_to_ready_seconds_overhead": overhead("service_schedule_to_ready_seconds_mean"),
            "service_app_started_delay_seconds_overhead": overhead("service_app_started_delay_seconds_mean"),
            "service_sidecar_started_delay_seconds_mean": mtls.get("service_sidecar_started_delay_seconds_mean"),
            "failed_scheduling_event_count_overhead": overhead("service_failed_scheduling_event_count"),
            "service_app_requested_cpu_mcores_overhead": overhead("service_app_requested_cpu_mcores_total"),
            "service_sidecar_requested_cpu_mcores_overhead": overhead("service_sidecar_requested_cpu_mcores_total"),
            "service_total_requested_cpu_mcores_overhead": overhead("service_total_requested_cpu_mcores_total"),
            "service_app_requested_memory_mib_overhead": overhead("service_app_requested_memory_mib_total"),
            "service_sidecar_requested_memory_mib_overhead": overhead("service_sidecar_requested_memory_mib_total"),
            "service_total_requested_memory_mib_overhead": overhead("service_total_requested_memory_mib_total"),
            "benchmark_requested_cpu_mcores_overhead": overhead("benchmark_requested_cpu_mcores_total"),
            "benchmark_requested_memory_mib_overhead": overhead("benchmark_requested_memory_mib_total"),
            "node_request_headroom_cpu_mcores_delta": overhead("node_request_headroom_cpu_mcores"),
            "node_request_headroom_memory_mib_delta": overhead("node_request_headroom_memory_mib"),
            "mtls_control_plane_colocation": mtls.get("control_plane_colocation") or {},
            "deployment_complexity_delta": {
                "additional_aks_enablement_step_count": int(mtls_complexity.get("aks_enablement_step_count") or 0)
                - int(plain_complexity.get("aks_enablement_step_count") or 0),
                "additional_kubernetes_object_count": int(mtls_complexity.get("kubernetes_object_count") or 0)
                - int(plain_complexity.get("kubernetes_object_count") or 0),
                "additional_always_on_control_plane_pod_count": int(mtls_complexity.get("always_on_control_plane_pod_count") or 0)
                - int(plain_complexity.get("always_on_control_plane_pod_count") or 0),
                "additional_injected_container_count": int(mtls_complexity.get("total_injected_container_count") or 0)
                - int(plain_complexity.get("total_injected_container_count") or 0),
            },
        }
        return {"by_condition": summaries, "comparison": comparison}

    def resource_summary_blockers(self, resources: dict[str, Any]) -> list[str]:
        blockers: list[str] = []
        by_condition = resources.get("by_condition") or {}
        for key in ("plain", "mtls"):
            payload = by_condition.get(key) or {}
            if payload.get("available"):
                continue
            reason = str(payload.get("reason") or "resource metrics unavailable")
            blockers.append(f"{key}: {reason}")
            for failure in payload.get("failures") or []:
                blockers.append(
                    f"{key} pass {failure.get('pass')} exec {failure.get('execution_index')}: {failure.get('reason')}"
                )
        return blockers

    def summarize_security_validation(self) -> dict[str, Any]:
        mtls_records = [
            record
            for record in self.completed_conditions
            if str(record.get("condition_key")) == "mtls"
        ]
        failures: list[dict[str, Any]] = []
        artifacts: list[dict[str, Any]] = []
        for record in mtls_records:
            security = record.get("security_validation") or {}
            artifacts.append({
                "pass": record.get("pass"),
                "execution_index": record.get("execution_index"),
                "artifact_path": record.get("security_preflight_artifact"),
                "metadata_path": security.get("metadata_path"),
                "passed": bool(record.get("security_validation_passed")),
                "full_chain_positive_probe_passed": security.get("full_chain_positive_probe_passed"),
                "non_mesh_direct_denial_probe_passed": security.get("non_mesh_direct_denial_probe_passed"),
            })
            if not record.get("security_validation_passed"):
                failures.append({
                    "pass": record.get("pass"),
                    "execution_index": record.get("execution_index"),
                    "reason": security.get("reason") or "mTLS security preflight did not pass",
                    "errors": security.get("errors") or [],
                })
        return {
            "passed": bool(mtls_records) and not failures,
            "mtls_condition_count": len(mtls_records),
            "artifacts": artifacts,
            "failures": failures,
        }

    def summarize_iteration_rows(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        metric_fields = (
            "end_to_end_ms",
            "total_compute_ms",
            "non_compute_overhead_ms",
            "hop_1_forward_ms",
            "hop_2_forward_ms",
            "total_activation_bytes",
            "hop_1_activation_bytes",
            "hop_2_activation_bytes",
        )
        return {
            metric: numeric_summary(
                [
                    value
                    for value in (maybe_float(row.get(metric)) for row in rows)
                    if value is not None
                ]
            )
            for metric in metric_fields
        }

    def build_aggregated_results(
        self,
        summary: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        overall_by_condition: dict[str, Any] = {}
        per_pass_by_condition: dict[str, dict[str, Any]] = {}
        paired_pass_deltas: list[dict[str, Any]] = []

        for key in ("plain", "mtls"):
            condition_rows = [
                row for row in rows if str(row.get("condition_key") or "") == key
            ]
            overall_by_condition[key] = {
                "condition": (
                    condition_rows[0].get("condition")
                    if condition_rows
                    else self.condition_names.get(key)
                ),
                "latency": self.summarize_iteration_rows(condition_rows),
                "resources": (summary.get("resources") or {}).get("by_condition", {}).get(key, {}),
                "operational": (summary.get("operational") or {}).get("by_condition", {}).get(key, {}),
            }

            for pass_value in sorted(
                {
                    int(row["paired_pass"])
                    for row in condition_rows
                    if str(row.get("paired_pass") or "").isdigit()
                }
            ):
                pass_rows = [
                    row
                    for row in condition_rows
                    if str(row.get("paired_pass") or "") == str(pass_value)
                ]
                per_pass_by_condition.setdefault(str(pass_value), {})[key] = {
                    "condition": overall_by_condition[key]["condition"],
                    "latency": self.summarize_iteration_rows(pass_rows),
                }

        for pass_value in sorted(int(value) for value in per_pass_by_condition):
            payload = per_pass_by_condition[str(pass_value)]
            plain_latency = (payload.get("plain") or {}).get("latency") or {}
            mtls_latency = (payload.get("mtls") or {}).get("latency") or {}
            plain_end = (plain_latency.get("end_to_end_ms") or {}).get("mean")
            mtls_end = (mtls_latency.get("end_to_end_ms") or {}).get("mean")
            plain_p95 = (plain_latency.get("end_to_end_ms") or {}).get("p95")
            mtls_p95 = (mtls_latency.get("end_to_end_ms") or {}).get("p95")
            plain_non_compute = (plain_latency.get("non_compute_overhead_ms") or {}).get("mean")
            mtls_non_compute = (mtls_latency.get("non_compute_overhead_ms") or {}).get("mean")
            plain_compute = (plain_latency.get("total_compute_ms") or {}).get("mean")
            mtls_compute = (mtls_latency.get("total_compute_ms") or {}).get("mean")

            paired_pass_deltas.append({
                "pass": pass_value,
                "plain_mean_ms": plain_end,
                "mtls_mean_ms": mtls_end,
                "mean_latency_overhead_ms": (
                    mtls_end - plain_end
                    if isinstance(plain_end, (int, float)) and isinstance(mtls_end, (int, float))
                    else None
                ),
                "mean_latency_overhead_pct": (
                    ((mtls_end - plain_end) / plain_end) * 100.0
                    if isinstance(plain_end, (int, float))
                    and isinstance(mtls_end, (int, float))
                    and plain_end > 0
                    else None
                ),
                "p95_latency_overhead_ms": (
                    mtls_p95 - plain_p95
                    if isinstance(plain_p95, (int, float)) and isinstance(mtls_p95, (int, float))
                    else None
                ),
                "non_compute_overhead_delta_ms": (
                    mtls_non_compute - plain_non_compute
                    if isinstance(plain_non_compute, (int, float))
                    and isinstance(mtls_non_compute, (int, float))
                    else None
                ),
                "total_compute_delta_ms": (
                    mtls_compute - plain_compute
                    if isinstance(plain_compute, (int, float)) and isinstance(mtls_compute, (int, float))
                    else None
                ),
            })

        latency_deltas = [
            float(row["mean_latency_overhead_ms"])
            for row in paired_pass_deltas
            if isinstance(row.get("mean_latency_overhead_ms"), (int, float))
        ]
        latency_pct_deltas = [
            float(row["mean_latency_overhead_pct"])
            for row in paired_pass_deltas
            if isinstance(row.get("mean_latency_overhead_pct"), (int, float))
        ]
        comparison = {
            "latency": (summary.get("latency") or {}).get("comparison", {}),
            "resources": (summary.get("resources") or {}).get("comparison", {}),
            "operational": (summary.get("operational") or {}).get("comparison", {}),
            "paired_pass_delta_ms": numeric_summary(latency_deltas),
            "paired_pass_delta_pct": numeric_summary(latency_pct_deltas),
        }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_artifacts": {
                "paired_summary_json": str(self.merged_dir / "paired_summary.json"),
                "raw_iterations_csv": str(self.merged_dir / "raw_iterations.csv"),
            },
            "run": {
                "smoke": bool(summary.get("smoke")),
                "image_ref": summary.get("image_ref"),
                "mesh_revision": summary.get("mesh_revision"),
                "execution_plan": summary.get("execution_plan"),
                "requirements": summary.get("requirements"),
                "security_validation_passed": summary.get("security_validation_passed"),
                "security_validation": summary.get("security_validation"),
                "completed_condition_executions": len(summary.get("conditions") or []),
                "total_iteration_rows": len(rows),
            },
            "overall_by_condition": overall_by_condition,
            "per_pass_by_condition": per_pass_by_condition,
            "paired_pass_deltas": paired_pass_deltas,
            "comparison": comparison,
        }

    def write_aggregated_results_csv(self, aggregated: dict[str, Any]) -> None:
        out_path = self.merged_dir / "aggregated_results.csv"
        fieldnames = [
            "row_type",
            "condition_key",
            "condition",
            "paired_pass",
            "n",
            "mean_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
            "stdev_ms",
            "total_compute_ms_mean",
            "non_compute_overhead_ms_mean",
            "total_activation_bytes_mean",
            "hop_1_activation_bytes_mean",
            "hop_2_activation_bytes_mean",
            "mean_latency_overhead_ms",
            "mean_latency_overhead_pct",
            "p95_latency_overhead_ms",
            "non_compute_overhead_delta_ms",
            "total_compute_delta_ms",
            "security_validation_passed",
            "resource_metrics_available",
            "resource_sample_count",
            "sidecar_sample_row_count",
            "sidecar_metrics_available",
            "service_app_cpu_mcores_mean",
            "sidecar_cpu_mcores_mean",
            "total_pod_cpu_mcores_mean",
            "service_app_memory_mib_mean",
            "sidecar_memory_mib_mean",
            "total_pod_memory_mib_mean",
            "service_schedule_to_ready_seconds_mean",
            "service_sidecar_started_delay_seconds_mean",
            "deployment_kubernetes_object_count",
            "deployment_control_plane_pod_count",
            "deployment_injected_container_count",
        ]

        rows: list[dict[str, Any]] = []
        run = aggregated.get("run") or {}
        for key, payload in (aggregated.get("overall_by_condition") or {}).items():
            latency = payload.get("latency") or {}
            end_to_end = latency.get("end_to_end_ms") or {}
            compute = latency.get("total_compute_ms") or {}
            non_compute = latency.get("non_compute_overhead_ms") or {}
            activation_total = latency.get("total_activation_bytes") or {}
            activation_hop1 = latency.get("hop_1_activation_bytes") or {}
            activation_hop2 = latency.get("hop_2_activation_bytes") or {}
            resources = payload.get("resources") or {}
            operational = payload.get("operational") or {}
            deployment = operational.get("deployment_complexity") or {}
            rows.append({
                "row_type": "condition_overall",
                "condition_key": key,
                "condition": payload.get("condition"),
                "n": end_to_end.get("n"),
                "mean_ms": end_to_end.get("mean"),
                "median_ms": end_to_end.get("median"),
                "p95_ms": end_to_end.get("p95"),
                "p99_ms": end_to_end.get("p99"),
                "stdev_ms": end_to_end.get("stdev"),
                "total_compute_ms_mean": compute.get("mean"),
                "non_compute_overhead_ms_mean": non_compute.get("mean"),
                "total_activation_bytes_mean": activation_total.get("mean"),
                "hop_1_activation_bytes_mean": activation_hop1.get("mean"),
                "hop_2_activation_bytes_mean": activation_hop2.get("mean"),
                "security_validation_passed": run.get("security_validation_passed") if key == "mtls" else None,
                "resource_metrics_available": resources.get("available"),
                "resource_sample_count": resources.get("sample_count"),
                "sidecar_sample_row_count": resources.get("sidecar_sample_row_count"),
                "sidecar_metrics_available": resources.get("sidecar_metrics_available"),
                "service_app_cpu_mcores_mean": resources.get("service_app_cpu_mcores_mean"),
                "sidecar_cpu_mcores_mean": resources.get("sidecar_cpu_mcores_mean"),
                "total_pod_cpu_mcores_mean": resources.get("total_pod_cpu_mcores_mean"),
                "service_app_memory_mib_mean": resources.get("service_app_memory_mib_mean"),
                "sidecar_memory_mib_mean": resources.get("sidecar_memory_mib_mean"),
                "total_pod_memory_mib_mean": resources.get("total_pod_memory_mib_mean"),
                "service_schedule_to_ready_seconds_mean": operational.get("service_schedule_to_ready_seconds_mean"),
                "service_sidecar_started_delay_seconds_mean": operational.get("service_sidecar_started_delay_seconds_mean"),
                "deployment_kubernetes_object_count": deployment.get("kubernetes_object_count"),
                "deployment_control_plane_pod_count": deployment.get("always_on_control_plane_pod_count"),
                "deployment_injected_container_count": deployment.get("total_injected_container_count"),
            })

        for pass_value, by_condition in (aggregated.get("per_pass_by_condition") or {}).items():
            for key, payload in by_condition.items():
                latency = payload.get("latency") or {}
                end_to_end = latency.get("end_to_end_ms") or {}
                compute = latency.get("total_compute_ms") or {}
                non_compute = latency.get("non_compute_overhead_ms") or {}
                activation_total = latency.get("total_activation_bytes") or {}
                activation_hop1 = latency.get("hop_1_activation_bytes") or {}
                activation_hop2 = latency.get("hop_2_activation_bytes") or {}
                rows.append({
                    "row_type": "condition_pass",
                    "condition_key": key,
                    "condition": payload.get("condition"),
                    "paired_pass": pass_value,
                    "n": end_to_end.get("n"),
                    "mean_ms": end_to_end.get("mean"),
                    "median_ms": end_to_end.get("median"),
                    "p95_ms": end_to_end.get("p95"),
                    "p99_ms": end_to_end.get("p99"),
                    "stdev_ms": end_to_end.get("stdev"),
                    "total_compute_ms_mean": compute.get("mean"),
                    "non_compute_overhead_ms_mean": non_compute.get("mean"),
                    "total_activation_bytes_mean": activation_total.get("mean"),
                    "hop_1_activation_bytes_mean": activation_hop1.get("mean"),
                    "hop_2_activation_bytes_mean": activation_hop2.get("mean"),
                    "security_validation_passed": run.get("security_validation_passed") if key == "mtls" else None,
                })

        for payload in aggregated.get("paired_pass_deltas") or []:
            rows.append({
                "row_type": "paired_pass_delta",
                "paired_pass": payload.get("pass"),
                "mean_latency_overhead_ms": payload.get("mean_latency_overhead_ms"),
                "mean_latency_overhead_pct": payload.get("mean_latency_overhead_pct"),
                "p95_latency_overhead_ms": payload.get("p95_latency_overhead_ms"),
                "non_compute_overhead_delta_ms": payload.get("non_compute_overhead_delta_ms"),
                "total_compute_delta_ms": payload.get("total_compute_delta_ms"),
            })

        comparison = aggregated.get("comparison") or {}
        latency = comparison.get("latency") or {}
        resources = comparison.get("resources") or {}
        operational = comparison.get("operational") or {}
        rows.append({
            "row_type": "comparison_overall",
            "mean_latency_overhead_ms": latency.get("mean_latency_overhead_ms"),
            "mean_latency_overhead_pct": latency.get("mean_latency_overhead_pct"),
            "p95_latency_overhead_ms": latency.get("p95_latency_overhead_ms"),
            "total_activation_bytes_mean": latency.get("total_activation_bytes_mean_delta"),
            "hop_1_activation_bytes_mean": latency.get("hop_1_activation_bytes_mean_delta"),
            "hop_2_activation_bytes_mean": latency.get("hop_2_activation_bytes_mean_delta"),
            "security_validation_passed": run.get("security_validation_passed"),
            "sidecar_cpu_mcores_mean": resources.get("sidecar_cpu_mcores_mean_overhead"),
            "total_pod_cpu_mcores_mean": resources.get("total_pod_cpu_mcores_mean_overhead"),
            "sidecar_memory_mib_mean": resources.get("sidecar_memory_mib_mean_overhead"),
            "total_pod_memory_mib_mean": resources.get("total_pod_memory_mib_mean_overhead"),
            "service_schedule_to_ready_seconds_mean": operational.get("service_schedule_to_ready_seconds_overhead"),
            "service_sidecar_started_delay_seconds_mean": operational.get("service_sidecar_started_delay_seconds_mean"),
        })

        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field) for field in fieldnames})

    def write_aggregated_results_markdown(self, aggregated: dict[str, Any]) -> None:
        out_path = self.merged_dir / "aggregated_results.md"
        run = aggregated.get("run") or {}
        comparison = aggregated.get("comparison") or {}
        latency = comparison.get("latency") or {}
        resources = comparison.get("resources") or {}
        operational = comparison.get("operational") or {}
        lines = [
            "# RQ2.1 Aggregated Results",
            "",
            f"- Image: `{run.get('image_ref')}`",
            f"- Mesh revision: `{run.get('mesh_revision')}`",
            f"- Completed executions: `{run.get('completed_condition_executions')}`",
            f"- Iteration rows: `{run.get('total_iteration_rows')}`",
            f"- Resource metrics complete: `{((run.get('requirements') or {}).get('resource_metrics_complete'))}`",
            f"- mTLS security validation passed: `{run.get('security_validation_passed')}`",
            "",
            "## Overall Latency",
            "",
            "| Condition | n | Mean ms | Median ms | p95 ms | p99 ms | Non-compute mean ms |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for key in ("plain", "mtls"):
            payload = (aggregated.get("overall_by_condition") or {}).get(key) or {}
            latency_payload = payload.get("latency") or {}
            end_to_end = latency_payload.get("end_to_end_ms") or {}
            non_compute = latency_payload.get("non_compute_overhead_ms") or {}
            lines.append(
                f"| {key} | {end_to_end.get('n')} | {end_to_end.get('mean')} | "
                f"{end_to_end.get('median')} | {end_to_end.get('p95')} | "
                f"{end_to_end.get('p99')} | {non_compute.get('mean')} |"
            )
        lines.extend([
            "",
            "## Activation Sanity",
            "",
            "| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |",
            "| --- | ---: | ---: | ---: |",
        ])
        for key in ("plain", "mtls"):
            payload = (aggregated.get("overall_by_condition") or {}).get(key) or {}
            latency_payload = payload.get("latency") or {}
            total_activation = latency_payload.get("total_activation_bytes") or {}
            hop_1_activation = latency_payload.get("hop_1_activation_bytes") or {}
            hop_2_activation = latency_payload.get("hop_2_activation_bytes") or {}
            lines.append(
                f"| {key} | {total_activation.get('mean')} | "
                f"{hop_1_activation.get('mean')} | {hop_2_activation.get('mean')} |"
            )
        lines.extend([
            "",
            "## Paired Pass Deltas",
            "",
            "| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for payload in aggregated.get("paired_pass_deltas") or []:
            lines.append(
                f"| {payload.get('pass')} | {payload.get('plain_mean_ms')} | "
                f"{payload.get('mtls_mean_ms')} | {payload.get('mean_latency_overhead_ms')} | "
                f"{payload.get('mean_latency_overhead_pct')} | "
                f"{payload.get('non_compute_overhead_delta_ms')} |"
            )
        lines.extend([
            "",
            "## Overall Comparison",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Mean latency overhead ms | {latency.get('mean_latency_overhead_ms')} |",
            f"| Mean latency overhead % | {latency.get('mean_latency_overhead_pct')} |",
            f"| p95 latency overhead ms | {latency.get('p95_latency_overhead_ms')} |",
            f"| Sidecar CPU mean mCPU | {resources.get('sidecar_cpu_mcores_mean_overhead')} |",
            f"| Total pod CPU overhead mean mCPU | {resources.get('total_pod_cpu_mcores_mean_overhead')} |",
            f"| Sidecar memory mean MiB | {resources.get('sidecar_memory_mib_mean_overhead')} |",
            f"| Total pod memory overhead mean MiB | {resources.get('total_pod_memory_mib_mean_overhead')} |",
            f"| Schedule-to-ready overhead s | {operational.get('service_schedule_to_ready_seconds_overhead')} |",
            "",
            "See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.",
        ])
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_aggregated_results(
        self,
        summary: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        aggregated = self.build_aggregated_results(summary, rows)
        (self.merged_dir / "aggregated_results.json").write_text(
            json.dumps(aggregated, indent=2),
            encoding="utf-8",
        )
        self.write_aggregated_results_csv(aggregated)
        self.write_aggregated_results_markdown(aggregated)
        return aggregated

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
        security_validation = self.summarize_security_validation()
        resource_requirement_blockers = self.resource_summary_blockers(resources)
        requirement_blockers = list(resource_requirement_blockers)
        if self.args.disable_resource_sampling:
            requirement_blockers.insert(
                0,
                "resource sampling was disabled; RQ2.1 requires CPU and memory overhead metrics",
            )
            resource_requirement_blockers.insert(
                0,
                "resource sampling was disabled; RQ2.1 requires CPU and memory overhead metrics",
            )
        if not security_validation.get("passed"):
            requirement_blockers.append("mTLS security validation was not completed successfully during the paired run")
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "smoke": bool(self.args.smoke),
            "image_ref": self.effective_image_ref,
            "mesh_revision": self.mesh_revision,
            "execution_plan": self.execution_plan,
            "conditions": self.completed_conditions,
            "latency": latency,
            "resources": resources,
            "operational": operational,
            "security_validation_passed": bool(security_validation.get("passed")),
            "security_validation": security_validation,
            "requirements": {
                "resource_metrics_complete": not resource_requirement_blockers,
                "security_validation_complete": bool(security_validation.get("passed")),
                "blocking_issues": requirement_blockers,
            },
            "notes": [
                "Plain and mTLS are measured on the same AKS cluster, image digest, nodepool, resources, and split topology.",
                "mTLS condition keeps the benchmark client outside the mesh and protects the downstream service with STRICT PeerAuthentication plus AuthorizationPolicy.",
                "The paired runner captures scheduling delay, schedule-to-ready delay, and deployment-complexity snapshots before each benchmark pass.",
                "Resource metrics are aggregated across all completed passes for each condition.",
                "RQ2.1 resource metrics are blocking: missing service-namespace samples leave the paired artifact set incomplete.",
            ],
        }
        summary_path = self.merged_dir / "paired_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        self.write_summary_csv(summary)
        self.write_summary_markdown(summary)
        self.write_aggregated_results(summary, rows)

        if (
            (resource_requirement_blockers and not self.args.disable_resource_sampling)
            or not security_validation.get("passed")
        ):
            raise PipelineError(
                "RQ2.1 paired benchmark artifact set is incomplete:\n- "
                + "\n- ".join(requirement_blockers)
            )

        for key, path in self.effective_config_paths.items():
            shutil.copy2(path, self.merged_dir / f"{key}_effective_config.yaml")

    def write_summary_csv(self, summary: dict[str, Any]) -> None:
        out_path = self.merged_dir / "paired_summary.csv"
        latency = summary["latency"]["by_condition"]
        resources = summary["resources"]["by_condition"]
        operational = summary["operational"]["by_condition"]
        fieldnames = [
            "condition_key",
            "condition",
            "n",
            "mean_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
            "non_compute_overhead_ms_mean",
            "total_compute_ms_mean",
            "total_activation_bytes_mean",
            "hop_1_activation_bytes_mean",
            "hop_2_activation_bytes_mean",
            "security_validation_passed",
            "resource_metrics_available",
            "resource_metrics_reason",
            "resource_sample_count",
            "sidecar_sample_row_count",
            "sidecar_metrics_available",
            "resource_passes_covered",
            "operational_passes_covered",
            "service_app_cpu_mcores_mean",
            "sidecar_cpu_mcores_mean",
            "total_pod_cpu_mcores_mean",
            "service_app_memory_mib_mean",
            "sidecar_memory_mib_mean",
            "total_pod_memory_mib_mean",
            "client_cpu_mcores_mean",
            "client_memory_mib_mean",
            "service_scheduling_delay_seconds_mean",
            "service_schedule_to_ready_seconds_mean",
            "service_app_started_delay_seconds_mean",
            "service_sidecar_started_delay_seconds_mean",
            "service_failed_scheduling_event_count",
            "service_app_requested_cpu_mcores_total",
            "service_sidecar_requested_cpu_mcores_total",
            "service_total_requested_cpu_mcores_total",
            "service_app_requested_memory_mib_total",
            "service_sidecar_requested_memory_mib_total",
            "service_total_requested_memory_mib_total",
            "benchmark_requested_cpu_mcores_total",
            "benchmark_requested_memory_mib_total",
            "node_request_headroom_cpu_mcores",
            "node_request_headroom_memory_mib",
            "deployment_kubernetes_object_count",
            "deployment_control_plane_pod_count",
            "deployment_injected_container_count",
            "control_plane_shares_benchmark_node",
            "control_plane_shared_node_names",
            "control_plane_shared_pod_names",
        ]
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for key in ("plain", "mtls"):
                resource_row = resources.get(key) or {}
                operational_row = operational.get(key) or {}
                row = {"condition_key": key}
                row.update(latency.get(key) or {})
                row.update(resource_row)
                row.update(operational_row)
                row["resource_metrics_available"] = resource_row.get("available")
                row["resource_metrics_reason"] = resource_row.get("reason")
                row["resource_sample_count"] = resource_row.get("sample_count")
                row["sidecar_sample_row_count"] = resource_row.get("sidecar_sample_row_count")
                row["sidecar_metrics_available"] = resource_row.get("sidecar_metrics_available")
                row["resource_passes_covered"] = json.dumps(resource_row.get("passes_covered") or [])
                row["operational_passes_covered"] = json.dumps(operational_row.get("passes_covered") or [])
                row["security_validation_passed"] = summary.get("security_validation_passed") if key == "mtls" else None
                deployment_complexity = operational_row.get("deployment_complexity") or {}
                row["deployment_kubernetes_object_count"] = deployment_complexity.get("kubernetes_object_count")
                row["deployment_control_plane_pod_count"] = deployment_complexity.get("always_on_control_plane_pod_count")
                row["deployment_injected_container_count"] = deployment_complexity.get("total_injected_container_count")
                control_plane = operational_row.get("control_plane_colocation") or {}
                row["control_plane_shares_benchmark_node"] = control_plane.get("shares_benchmark_node")
                row["control_plane_shared_node_names"] = json.dumps(control_plane.get("shared_node_names") or [])
                row["control_plane_shared_pod_names"] = json.dumps(control_plane.get("control_plane_pod_names") or [])
                writer.writerow({field: row.get(field) for field in fieldnames})

    def write_summary_markdown(self, summary: dict[str, Any]) -> None:
        comparison = summary["latency"]["comparison"]
        latency_by_condition = summary["latency"]["by_condition"]
        resource_by_condition = summary["resources"]["by_condition"]
        resources = summary["resources"]["comparison"]
        operational = summary["operational"]["comparison"]
        deployment_delta = operational.get("deployment_complexity_delta") or {}
        mtls_resources = resource_by_condition.get("mtls") or {}
        mtls_control_plane = operational.get("mtls_control_plane_colocation") or {}
        lines = [
            "# RQ2.1 Paired Benchmark Summary",
            "",
            f"- Smoke mode: `{summary['smoke']}`",
            f"- Image: `{summary['image_ref']}`",
            f"- Mesh revision: `{summary['mesh_revision']}`",
            f"- Execution order: `{summary['execution_plan']['passes']}`",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| RQ2.1 resource metrics complete | {summary['requirements']['resource_metrics_complete']} |",
            f"| mTLS security validation passed | {summary.get('security_validation_passed')} |",
            f"| Mean latency overhead (ms) | {comparison.get('mean_latency_overhead_ms')} |",
            f"| Mean latency overhead (%) | {comparison.get('mean_latency_overhead_pct')} |",
            f"| p95 latency overhead (ms) | {comparison.get('p95_latency_overhead_ms')} |",
            f"| mTLS sidecar sample rows | {mtls_resources.get('sidecar_sample_row_count')} |",
            f"| mTLS sidecar metrics available | {mtls_resources.get('sidecar_metrics_available')} |",
            f"| Sidecar CPU cost (mCPU mean) | {resources.get('sidecar_cpu_mcores_mean_overhead')} |",
            f"| Sidecar memory cost (MiB mean) | {resources.get('sidecar_memory_mib_mean_overhead')} |",
            f"| Total pod CPU overhead (mCPU mean) | {resources.get('total_pod_cpu_mcores_mean_overhead')} |",
            f"| Total pod memory overhead (MiB mean) | {resources.get('total_pod_memory_mib_mean_overhead')} |",
            f"| Service sidecar requested CPU overhead (mCPU) | {operational.get('service_sidecar_requested_cpu_mcores_overhead')} |",
            f"| Service sidecar requested memory overhead (MiB) | {operational.get('service_sidecar_requested_memory_mib_overhead')} |",
            f"| Scheduling delay overhead (s mean) | {operational.get('service_scheduling_delay_seconds_overhead')} |",
            f"| Schedule-to-ready overhead (s mean) | {operational.get('service_schedule_to_ready_seconds_overhead')} |",
            f"| mTLS sidecar start delay (s mean) | {operational.get('service_sidecar_started_delay_seconds_mean')} |",
            f"| Additional Kubernetes objects | {deployment_delta.get('additional_kubernetes_object_count')} |",
            f"| Additional control-plane pods | {deployment_delta.get('additional_always_on_control_plane_pod_count')} |",
            f"| Additional injected containers | {deployment_delta.get('additional_injected_container_count')} |",
            "",
        ]
        lines.extend([
            "## Activation Sanity",
            "",
            "| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |",
            "| --- | ---: | ---: | ---: |",
        ])
        for key in ("plain", "mtls"):
            payload = latency_by_condition.get(key) or {}
            lines.append(
                f"| {key} | {payload.get('total_activation_bytes_mean')} | "
                f"{payload.get('hop_1_activation_bytes_mean')} | "
                f"{payload.get('hop_2_activation_bytes_mean')} |"
            )
        lines.append("")
        if mtls_control_plane.get("shares_benchmark_node"):
            lines.extend([
                "## Limitations",
                "",
                "- Mesh control-plane pods shared benchmark node(s) "
                + ", ".join(mtls_control_plane.get("shared_node_names") or [])
                + ". Control-plane pods on shared nodes: "
                + ", ".join(mtls_control_plane.get("control_plane_pod_names") or []),
                "",
            ])
        blockers = summary.get("requirements", {}).get("blocking_issues") or []
        if blockers:
            lines.extend([
                "## Blocking Issues",
                "",
                *[f"- {issue}" for issue in blockers],
                "",
            ])
        lines.extend([
            "See `paired_summary.json`, `aggregated_results.md`, and `raw_iterations.csv` for thesis inspection.",
        ])
        (self.merged_dir / "paired_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_run_metadata(self, *, completed: bool) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "completed": completed,
            "smoke": bool(self.args.smoke),
            "artifact_dir": str(self.artifact_dir),
            "plain_config": str(self.source_paths["plain"]),
            "mtls_config": str(self.source_paths["mtls"]),
            "effective_configs": {key: str(path) for key, path in self.effective_config_paths.items()},
            "image_ref": self.effective_image_ref,
            "mesh_revision": self.mesh_revision,
            "nodepool": self.args.nodepool,
            "provision_requested": bool(self.args.provision),
            "infrastructure_provisioned": self.infrastructure_provisioned,
            "destroy_infrastructure_on_success": bool(self.args.destroy_infrastructure_on_success),
            "destroy_infrastructure_on_failure": bool(self.args.destroy_infrastructure_on_failure),
            "infrastructure_destroyed": self.infrastructure_destroyed,
            "resource_group": self.args.resource_group,
            "cluster_name": self.args.cluster_name,
            "acr_name": self.acr_name,
            "execution_plan": self.execution_plan,
            "completed_conditions": self.completed_conditions,
            "terraform_infra_dir": str(INFRA_DIR),
        }
        self.run_metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def run(self) -> None:
        self.validate_configs()
        log(
            "RQ2.1 paired benchmark scope: chain_2svc_plain vs chain_2svc_mtls only; "
            "RQ2.2 and chain_5svc are intentionally not run."
        )
        self.prepare_artifact_dirs()
        self.verify_required_files()
        self.verify_host_prerequisites()
        self.prepare_infrastructure()
        self.write_effective_configs()

        if self.args.generate_only:
            for key in ("plain", "mtls"):
                context = self.condition_context(key, 0, 0)
                self.generate_manifests(context)
            self.write_run_metadata(completed=True)
            log(f"Generate-only paired artifacts: {self.artifact_dir}")
            return

        self.verify_cluster_reachable()
        execution_index = 0
        for pass_record in self.execution_plan["passes"]:
            pass_index = int(pass_record["pass"])
            for key in pass_record["order"]:
                execution_index += 1
                log(
                    f"Starting paired pass {pass_index}, execution {execution_index}: "
                    f"{self.condition_names[key]}"
                )
                self.run_condition_once(key, pass_index, execution_index)

        self.merge_artifacts()
        self.write_run_metadata(completed=True)
        if self.args.destroy_infrastructure_on_success:
            self.destroy_infrastructure("successful paired benchmark")
            self.write_run_metadata(completed=True)
        log(f"RQ2.1 paired benchmark artifacts: {self.artifact_dir}")

    def handle_failure(self, exc: Exception) -> None:
        if self.current_context and self.resources_deployed and self.args.cleanup_on_failure:
            try:
                self.cleanup_namespaces(self.current_context)
            except Exception as cleanup_exc:
                warn(f"Failed to clean up namespaces after failure: {cleanup_exc}")
        elif self.current_context and self.resources_deployed:
            warn(
                f"Preserving namespaces {self.current_context.service_namespace} and "
                f"{self.current_context.client_namespace} for inspection."
            )
        if self.args.destroy_infrastructure_on_failure:
            try:
                self.destroy_infrastructure("failed paired benchmark")
            except Exception as destroy_exc:
                warn(f"Failed to destroy infrastructure after paired benchmark failure: {destroy_exc}")
        try:
            self.write_run_metadata(completed=False)
        except Exception:
            pass
        warn(f"RQ2.1 paired benchmark failed. Artifacts directory: {self.artifact_dir}")
        print(f"[{timestamp()}] ERROR: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    runner = RQ21PairedBenchmarkRunner(args)
    try:
        runner.run()
    except Exception as exc:
        runner.handle_failure(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
