"""Stage 0 preflight for the approved RQ2.2 AMD SEV-SNP AKS path.

This script is intentionally narrow. It validates only the thesis-facing
West Europe `Standard_D8as_v5` versus `Standard_DC8as_v5` plan recorded in
building_plans/rq2/RQ2_2_Experimental_Design.md. It does not run the
benchmark.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "rq2" / "2.2" / "rq2_2_confidential_amd_sev_snp.yaml"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "results_exports"

APPROVED_REGION = "westeurope"
APPROVED_BACKEND = "amd_sev_snp"
APPROVED_STANDARD_SIZE = "Standard_D8as_v5"
APPROVED_CONFIDENTIAL_SIZE = "Standard_DC8as_v5"
APPROVED_STANDARD_FAMILY = "standardDASv5Family"
APPROVED_CONFIDENTIAL_FAMILY = "standardDCASv5Family"
APPROVED_STANDARD_QUOTA_LIMIT = 16
APPROVED_CONFIDENTIAL_QUOTA_LIMIT = 16
ROLLING_PEAK_REGIONAL_VCPUS = 18

WINDOWS_COMMAND_CANDIDATES = {
    "az": [r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"],
}


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_command_path(command_name: str) -> str | None:
    resolved = shutil.which(command_name)
    if resolved:
        return resolved
    if os.name == "nt":
        for candidate in WINDOWS_COMMAND_CANDIDATES.get(command_name, []):
            if Path(candidate).exists():
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


def run_command(args: list[str]) -> CommandResult:
    completed = subprocess.run(
        prepare_command_args(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = (completed.stdout or b"").decode("utf-8", errors="replace")
    stderr = (completed.stderr or b"").decode("utf-8", errors="replace")
    return CommandResult(args=list(args), returncode=int(completed.returncode), stdout=stdout, stderr=stderr)


def command_record(result: CommandResult) -> dict[str, Any]:
    return {
        "args": result.args,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def command_stdout_json(result: CommandResult) -> Any:
    if not (result.stdout or "").strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def run_json_command(args: list[str], commands: list[dict[str, Any]]) -> Any:
    result = run_command(args)
    commands.append(command_record(result))
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Command failed: {' '.join(args)}")
    return command_stdout_json(result)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"YAML did not parse as a mapping: {path}")
    return payload


def make_artifact_dir(output_dir: str | None) -> Path:
    if output_dir:
        path = Path(output_dir).resolve()
    else:
        path = DEFAULT_OUTPUT_ROOT / f"rq2_2_preflight_{utc_stamp()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def usage_record_by_value(usages: list[dict[str, Any]], value: str) -> dict[str, Any] | None:
    target = value.lower()
    for item in usages or []:
        name = item.get("name") or {}
        if str(name.get("value") or "").lower() == target:
            return item
    return None


def usage_summary(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {"found": False}
    current = int(record.get("currentValue") or 0)
    limit = int(record.get("limit") or 0)
    name = record.get("name") or {}
    return {
        "found": True,
        "name": name.get("localizedValue") or name.get("value"),
        "value": name.get("value"),
        "current": current,
        "limit": limit,
        "available": max(0, limit - current),
    }


def capability_value(sku: dict[str, Any], capability_name: str) -> str | None:
    for capability in sku.get("capabilities") or []:
        if capability.get("name") == capability_name:
            return str(capability.get("value") or "")
    return None


def zone_sort_key(zone: str) -> tuple[int, str]:
    return (int(zone), zone) if zone.isdigit() else (9999, zone)


def sorted_zones(zones: set[str] | list[str]) -> list[str]:
    return sorted({str(zone) for zone in zones}, key=zone_sort_key)


def reported_zones(sku: dict[str, Any]) -> list[str]:
    zones: set[str] = set()
    for item in sku.get("locationInfo") or []:
        zones.update(str(zone) for zone in item.get("zones") or [])
        for zone_detail in item.get("zoneDetails") or []:
            zones.update(str(zone) for zone in zone_detail.get("name") or [])
    return sorted_zones(zones)


def restricted_zones(sku: dict[str, Any]) -> list[str]:
    zones: set[str] = set()
    for restriction in sku.get("restrictions") or []:
        if str(restriction.get("type") or "").lower() != "zone":
            continue
        restriction_info = restriction.get("restrictionInfo") or {}
        zones.update(str(zone) for zone in restriction_info.get("zones") or [])
    return sorted_zones(zones)


def effective_zones(sku: dict[str, Any]) -> list[str]:
    reported = set(reported_zones(sku))
    restricted = set(restricted_zones(sku))
    if not reported:
        return []
    return sorted_zones(reported - restricted)


def broad_vm_family(size: str) -> str:
    token = size.replace("Standard_", "", 1)
    match = re.match(r"^D(C)?\d+([a-z]+)_v(\d+)$", token, flags=re.IGNORECASE)
    if not match:
        return token.lower()
    suffix = match.group(2).lower()
    generation = match.group(3)
    return f"d{suffix}_v{generation}"


def sku_summary(size: str, sku_payload: list[dict[str, Any]]) -> dict[str, Any]:
    sku = next((item for item in sku_payload or [] if item.get("name") == size), None)
    if not sku:
        return {"found": False, "size": size}
    return {
        "found": True,
        "size": size,
        "family": sku.get("family"),
        "broad_family": broad_vm_family(size),
        "locations": sku.get("locations") or [],
        "location_info": sku.get("locationInfo") or [],
        "restrictions": sku.get("restrictions") or [],
        "vcpus": capability_value(sku, "vCPUs"),
        "memory_gb": capability_value(sku, "MemoryGB"),
        "hyperv_generations": capability_value(sku, "HyperVGenerations"),
        "confidential_computing_type": capability_value(sku, "ConfidentialComputingType"),
        "accelerated_networking": capability_value(sku, "AcceleratedNetworkingEnabled"),
        "ephemeral_os_disk": capability_value(sku, "EphemeralOSDiskSupported"),
        "disk_controller_types": capability_value(sku, "DiskControllerTypes"),
        "zone_availability": {
            "reported_zones": reported_zones(sku),
            "restricted_zones": restricted_zones(sku),
            "effective_zones": effective_zones(sku),
        },
    }


def display_value(value: Any) -> str:
    if value is None or value == "":
        return "<unset>"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "<unset>"
    return str(value)


def zone_phrase(zones: list[str]) -> str:
    if not zones:
        return "<unknown zones>"
    prefix = "zone" if len(zones) == 1 else "zones"
    return f"{prefix} {', '.join(zones)}"


def hardware_near_assessment(
    standard: dict[str, Any],
    confidential: dict[str, Any],
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    basis = {
        "vcpus_match": standard.get("vcpus") == confidential.get("vcpus"),
        "memory_gb_match": standard.get("memory_gb") == confidential.get("memory_gb"),
        "hyperv_generations_match": standard.get("hyperv_generations") == confidential.get("hyperv_generations"),
        "broad_family_match": standard.get("broad_family") == confidential.get("broad_family"),
        "standard": {
            "vcpus": standard.get("vcpus"),
            "memory_gb": standard.get("memory_gb"),
            "hyperv_generations": standard.get("hyperv_generations"),
            "broad_family": standard.get("broad_family"),
        },
        "confidential": {
            "vcpus": confidential.get("vcpus"),
            "memory_gb": confidential.get("memory_gb"),
            "hyperv_generations": confidential.get("hyperv_generations"),
            "broad_family": confidential.get("broad_family"),
        },
    }
    is_hardware_near = all(
        bool(basis[key])
        for key in ("vcpus_match", "memory_gb_match", "hyperv_generations_match", "broad_family_match")
    )
    overhead_framing = "hardware_near" if is_hardware_near else "not_hardware_near"
    differences: list[dict[str, Any]] = []
    if not is_hardware_near:
        return overhead_framing, basis, differences

    capability_checks = [
        ("accelerated_networking", "AcceleratedNetworkingEnabled", "accelerated networking differs"),
        ("ephemeral_os_disk", "EphemeralOSDiskSupported", "ephemeral OS disk support differs"),
        ("disk_controller_types", "DiskControllerTypes", "DiskControllerTypes differs"),
        ("confidential_computing_type", "ConfidentialComputingType", "ConfidentialComputingType differs"),
    ]
    for key, capability, description in capability_checks:
        standard_value = standard.get(key)
        confidential_value = confidential.get(key)
        if standard_value == confidential_value:
            continue
        differences.append({
            "kind": "capability",
            "capability": capability,
            "standard_value": standard_value,
            "confidential_value": confidential_value,
            "message": (
                "Hardware-near selected pair capability differs: "
                f"{description} ({APPROVED_STANDARD_SIZE}={display_value(standard_value)}, "
                f"{APPROVED_CONFIDENTIAL_SIZE}={display_value(confidential_value)})."
            ),
        })

    standard_zones = ((standard.get("zone_availability") or {}).get("effective_zones") or [])
    confidential_zones = ((confidential.get("zone_availability") or {}).get("effective_zones") or [])
    if standard_zones != confidential_zones:
        if len(confidential_zones) == 1:
            zone_message = (
                "Hardware-near selected pair zone availability differs: "
                f"confidential SKU {APPROVED_CONFIDENTIAL_SIZE} is only available in {zone_phrase(confidential_zones)}; "
                f"standard SKU {APPROVED_STANDARD_SIZE} is available in {zone_phrase(standard_zones)}."
            )
        elif len(standard_zones) == 1:
            zone_message = (
                "Hardware-near selected pair zone availability differs: "
                f"standard SKU {APPROVED_STANDARD_SIZE} is only available in {zone_phrase(standard_zones)}; "
                f"confidential SKU {APPROVED_CONFIDENTIAL_SIZE} is available in {zone_phrase(confidential_zones)}."
            )
        else:
            zone_message = (
                "Hardware-near selected pair zone availability differs: "
                f"standard SKU {APPROVED_STANDARD_SIZE} is available in {zone_phrase(standard_zones)}; "
                f"confidential SKU {APPROVED_CONFIDENTIAL_SIZE} is available in {zone_phrase(confidential_zones)}."
            )
        differences.append({
            "kind": "zone_availability",
            "capability": "zones/locationInfo",
            "standard_value": standard_zones,
            "confidential_value": confidential_zones,
            "standard_location_info": standard.get("location_info") or [],
            "confidential_location_info": confidential.get("location_info") or [],
            "message": zone_message,
        })

    return overhead_framing, basis, differences


def blocking_sku_restrictions(summary: dict[str, Any]) -> list[dict[str, Any]]:
    restrictions = summary.get("restrictions") or []
    return [
        restriction
        for restriction in restrictions
        if str(restriction.get("type") or "").lower() != "zone"
    ]


def sku_restriction_warnings(summary: dict[str, Any], region: str) -> list[str]:
    warnings: list[str] = []
    for restriction in summary.get("restrictions") or []:
        if str(restriction.get("type") or "").lower() != "zone":
            continue
        restriction_info = restriction.get("restrictionInfo") or {}
        zones = restriction_info.get("zones") or []
        if zones:
            warnings.append(
                f"{summary.get('size')} has subscription zone restrictions in {region}: "
                f"unavailable zones={', '.join(str(zone) for zone in zones)}"
            )
    return warnings


def config_hard_gate(raw_config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cc = raw_config.get("confidential_compute") or {}
    if not isinstance(cc, dict):
        errors.append("confidential_compute must be a mapping")
        cc = {}

    checks = {
        "region": str(cc.get("region") or ""),
        "backend": str(cc.get("backend") or ""),
        "standard_size": str(cc.get("standard_size") or ""),
        "confidential_size": str(cc.get("confidential_size") or ""),
        "target_service_index": str(cc.get("target_service_index") or ""),
        "standard_quota_family": str((cc.get("standard_quota") or {}).get("family") or ""),
        "confidential_quota_family": str((cc.get("confidential_quota") or {}).get("family") or ""),
        "standard_quota_required_limit": int((cc.get("standard_quota") or {}).get("required_limit") or 0),
        "confidential_quota_required_limit": int((cc.get("confidential_quota") or {}).get("required_limit") or 0),
    }
    expected = {
        "region": APPROVED_REGION,
        "backend": APPROVED_BACKEND,
        "standard_size": APPROVED_STANDARD_SIZE,
        "confidential_size": APPROVED_CONFIDENTIAL_SIZE,
        "target_service_index": "2",
        "standard_quota_family": APPROVED_STANDARD_FAMILY,
        "confidential_quota_family": APPROVED_CONFIDENTIAL_FAMILY,
        "standard_quota_required_limit": APPROVED_STANDARD_QUOTA_LIMIT,
        "confidential_quota_required_limit": APPROVED_CONFIDENTIAL_QUOTA_LIMIT,
    }
    for key, expected_value in expected.items():
        if checks.get(key) != expected_value:
            errors.append(f"RQ2.2 approved-plan gate failed for {key}: expected={expected_value} observed={checks.get(key)}")

    conditions = raw_config.get("conditions") or []
    names = [str(condition.get("name") or "") for condition in conditions if isinstance(condition, dict)]
    expected_conditions = [
        "chain_2svc_mtls_standard",
        "chain_2svc_mtls_confidential_service2",
    ]
    if names != expected_conditions:
        errors.append(f"RQ2.2 conditions must be exactly {expected_conditions}, observed={names}")
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        if condition.get("type") != "chain" or condition.get("chain_split_points") != ["layer2"]:
            errors.append(f"RQ2.2 condition must be chain_2svc split after layer2: {condition.get('name')}")

    return checks, errors


def rq21_security_semantics(raw_config: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    k8s = raw_config.get("kubernetes") or {}
    mesh = k8s.get("mesh") or {}
    authz = mesh.get("authorization_policy") or {}
    peer = mesh.get("peer_authentication") or {}
    if not mesh.get("enabled"):
        errors.append("kubernetes.mesh.enabled must be true")
    if str(mesh.get("implementation") or "") != "managed AKS Istio add-on":
        errors.append("kubernetes.mesh.implementation must be managed AKS Istio add-on")
    if k8s.get("client_namespace") == k8s.get("namespace"):
        errors.append("benchmark client must remain outside the mesh namespace")
    if not peer.get("enabled"):
        errors.append("PeerAuthentication must be enabled")
    if not authz.get("enabled"):
        errors.append("AuthorizationPolicy must be enabled")
    if str(authz.get("source_segment_index") or "") != "1" or str(authz.get("downstream_segment_index") or "") != "2":
        errors.append("AuthorizationPolicy must allow only service1 to service2")
    accounts = mesh.get("service_accounts") or {}
    if "1" not in accounts or "2" not in accounts:
        errors.append("service accounts for service1 and service2 are required")
    return not errors, errors


def manifest_docs(manifest_dir: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in sorted(manifest_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            for document in yaml.safe_load_all(handle):
                if isinstance(document, dict):
                    docs.append(document)
    return docs


def deployment_for(docs: list[dict[str, Any]], condition: str, segment_index: str) -> dict[str, Any] | None:
    for doc in docs:
        if doc.get("kind") != "Deployment":
            continue
        labels = (doc.get("metadata") or {}).get("labels") or {}
        if labels.get("condition") == condition and labels.get("segment-index") == segment_index:
            return doc
    return None


def validate_generated_manifests(manifest_dir: Path) -> tuple[bool, list[str]]:
    docs = manifest_docs(manifest_dir)
    errors: list[str] = []
    expected = {
        ("chain_2svc_mtls_standard", "1"): ("r22s1std", "false"),
        ("chain_2svc_mtls_standard", "2"): ("r22s2std", "false"),
        ("chain_2svc_mtls_confidential_service2", "1"): ("r22s1std", "false"),
        ("chain_2svc_mtls_confidential_service2", "2"): ("r22s2cvm", "true"),
    }
    for (condition, segment), (nodepool, confidential) in expected.items():
        deployment = deployment_for(docs, condition, segment)
        if not deployment:
            errors.append(f"Missing deployment for {condition} segment {segment}")
            continue
        labels = (deployment.get("metadata") or {}).get("labels") or {}
        selector = (((deployment.get("spec") or {}).get("template") or {}).get("spec") or {}).get("nodeSelector") or {}
        affinity = (((deployment.get("spec") or {}).get("template") or {}).get("spec") or {}).get("affinity")
        if selector.get("agentpool") != nodepool:
            errors.append(f"{condition} segment {segment} must select nodepool {nodepool}, observed={selector}")
        if labels.get("confidential-compute") != confidential:
            errors.append(f"{condition} segment {segment} has wrong confidential-compute label: {labels}")
        if affinity:
            errors.append(f"{condition} segment {segment} must not include same-node service affinity")
    if not any(doc.get("kind") == "AuthorizationPolicy" for doc in docs):
        errors.append("AuthorizationPolicy for service2 missing")
    if not any(doc.get("kind") == "PeerAuthentication" for doc in docs):
        errors.append("PeerAuthentication resources missing")
    return not errors, errors


def run_generate_only_validation(config_path: Path, artifact_dir: Path, commands: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "passed": False,
        "manifest_dir": None,
        "errors": [],
    }
    manifest_dir = artifact_dir / "generate_only_manifests"
    result = run_command([
        sys.executable,
        str(REPO_ROOT / "k8s" / "aks" / "generate_aks_manifests.py"),
        "--config",
        str(config_path),
        "--output-dir",
        str(manifest_dir),
    ])
    commands.append(command_record(result))
    payload["manifest_dir"] = str(manifest_dir)
    if result.returncode != 0:
        payload["errors"].append(result.stderr.strip() or result.stdout.strip() or "manifest generation failed")
        return payload
    passed, errors = validate_generated_manifests(manifest_dir)
    payload["passed"] = passed
    payload["errors"] = errors
    return payload


def nodepool_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    power_state = payload.get("powerState")
    if isinstance(power_state, dict):
        power_state = power_state.get("code")
    return {
        "name": payload.get("name"),
        "vm_size": payload.get("vmSize"),
        "provisioning_state": payload.get("provisioningState"),
        "power_state": power_state,
        "mode": payload.get("mode"),
        "count": payload.get("count"),
        "availability_zones": payload.get("availabilityZones"),
        "node_labels": payload.get("nodeLabels"),
    }


def delete_aks_nodepool(resource_group: str, cluster_name: str, nodepool_name: str) -> CommandResult:
    return run_command([
        "az",
        "aks",
        "nodepool",
        "delete",
        "--resource-group",
        resource_group,
        "--cluster-name",
        cluster_name,
        "--name",
        nodepool_name,
    ])


def validate_aks_nodepool(
    resource_group: str | None,
    cluster_name: str | None,
    commands: list[dict[str, Any]],
    keep: bool = False,
) -> dict[str, Any]:
    payload = {
        "status": "not_validated",
        "final_status": "not_validated",
        "nodepool_name": None,
        "requested_vm_size": APPROVED_CONFIDENTIAL_SIZE,
        "observed_vm_size": None,
        "region": APPROVED_REGION,
        "create_command": None,
        "show_command": None,
        "delete_command": None,
        "create_response_summary": {},
        "show_response_summary": {},
        "created": False,
        "deleted": False,
        "errors": [],
    }

    def set_status(status: str) -> None:
        payload["status"] = status
        payload["final_status"] = status

    if not resource_group or not cluster_name:
        payload["errors"].append("--resource-group and --cluster-name are required for --validate-aks-nodepool")
        set_status("failed")
        return payload

    nodepool_name = ("r22v" + datetime.now(timezone.utc).strftime("%H%M%S"))[:12].lower()
    payload["nodepool_name"] = nodepool_name
    add_result = run_command([
        "az",
        "aks",
        "nodepool",
        "add",
        "--resource-group",
        resource_group,
        "--cluster-name",
        cluster_name,
        "--name",
        nodepool_name,
        "--node-count",
        "1",
        "--node-vm-size",
        APPROVED_CONFIDENTIAL_SIZE,
        "--mode",
        "User",
        "--labels",
        "rq=2.2",
        "rq22-role=service2-confidential",
        "confidential-compute=amd-sev-snp",
        "purpose=rq22preflight",
        "--output",
        "json",
    ])
    add_record = command_record(add_result)
    commands.append(add_record)
    payload["create_command"] = add_record
    add_summary = nodepool_summary(command_stdout_json(add_result))
    payload["create_response_summary"] = add_summary
    if add_result.returncode != 0:
        payload["errors"].append(add_result.stderr.strip() or add_result.stdout.strip() or "AKS node-pool create failed")
        if not keep:
            delete_result = delete_aks_nodepool(resource_group, cluster_name, nodepool_name)
            delete_record = command_record(delete_result)
            commands.append(delete_record)
            payload["delete_command"] = delete_record
            if delete_result.returncode == 0:
                payload["deleted"] = True
        set_status("failed")
        return payload
    payload["created"] = True

    show_result = run_command([
        "az",
        "aks",
        "nodepool",
        "show",
        "--resource-group",
        resource_group,
        "--cluster-name",
        cluster_name,
        "--name",
        nodepool_name,
        "--output",
        "json",
    ])
    show_record = command_record(show_result)
    commands.append(show_record)
    payload["show_command"] = show_record
    show_summary = nodepool_summary(command_stdout_json(show_result))
    payload["show_response_summary"] = show_summary
    payload["observed_vm_size"] = show_summary.get("vm_size")
    if show_result.returncode != 0:
        payload["errors"].append(show_result.stderr.strip() or show_result.stdout.strip() or "AKS node-pool show failed")
    elif payload["observed_vm_size"] != APPROVED_CONFIDENTIAL_SIZE:
        payload["errors"].append(
            f"AKS node-pool VM size mismatch: requested={APPROVED_CONFIDENTIAL_SIZE} observed={payload['observed_vm_size']}"
        )

    if not keep:
        delete_result = delete_aks_nodepool(resource_group, cluster_name, nodepool_name)
        delete_record = command_record(delete_result)
        commands.append(delete_record)
        payload["delete_command"] = delete_record
        if delete_result.returncode == 0:
            payload["deleted"] = True
        else:
            payload["errors"].append(delete_result.stderr.strip() or delete_result.stdout.strip() or "AKS node-pool delete failed")

    set_status("failed" if payload["errors"] else "passed")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RQ2.2 Stage 0 preflight for the approved AMD SEV-SNP AKS path")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-aks-nodepool", action="store_true")
    parser.add_argument("--resource-group", default=None)
    parser.add_argument("--cluster-name", default=None)
    parser.add_argument("--keep-test-nodepool", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_dir = make_artifact_dir(args.output_dir)
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    selected_region = APPROVED_REGION
    standard_sku: dict[str, Any] = {"found": False, "size": APPROVED_STANDARD_SIZE}
    confidential_sku: dict[str, Any] = {"found": False, "size": APPROVED_CONFIDENTIAL_SIZE}
    quota = {
        "total_regional_vcpus": {"found": False},
        "standard_family": {"found": False},
        "confidential_family": {"found": False},
        "rolling_peak_required_vcpus": ROLLING_PEAK_REGIONAL_VCPUS,
    }
    aks_status = {"status": "not_validated", "final_status": "not_validated", "errors": []}
    manifest_validation = {"passed": False, "errors": []}
    mtls_authz = {"preserved": False, "errors": []}
    config_checks: dict[str, Any] = {}
    overhead_framing = "not_evaluated"
    hardware_near_basis: dict[str, Any] = {}
    selected_pair_capability_differences: list[dict[str, Any]] = []

    try:
        config_path = Path(args.config).resolve()
        raw_config = load_yaml(config_path)
        config_checks, gate_errors = config_hard_gate(raw_config)
        errors.extend(gate_errors)

        preserved, semantic_errors = rq21_security_semantics(raw_config)
        mtls_authz = {"preserved": preserved, "errors": semantic_errors}
        errors.extend(semantic_errors)

        if not errors:
            usages = run_json_command(["az", "vm", "list-usage", "-l", selected_region, "--output", "json"], commands) or []
            quota["total_regional_vcpus"] = usage_summary(usage_record_by_value(usages, "cores"))
            quota["standard_family"] = usage_summary(usage_record_by_value(usages, APPROVED_STANDARD_FAMILY))
            quota["confidential_family"] = usage_summary(usage_record_by_value(usages, APPROVED_CONFIDENTIAL_FAMILY))

            if not quota["standard_family"].get("found"):
                errors.append(f"Quota record missing: {APPROVED_STANDARD_FAMILY}")
            elif int(quota["standard_family"].get("limit") or 0) < APPROVED_STANDARD_QUOTA_LIMIT:
                errors.append(
                    f"Standard DASv5 quota is below approved RQ2.2 limit: "
                    f"limit={quota['standard_family'].get('limit')} required={APPROVED_STANDARD_QUOTA_LIMIT}"
                )

            if not quota["confidential_family"].get("found"):
                errors.append(f"Quota record missing: {APPROVED_CONFIDENTIAL_FAMILY}")
            elif int(quota["confidential_family"].get("limit") or 0) < APPROVED_CONFIDENTIAL_QUOTA_LIMIT:
                errors.append(
                    f"Standard DCASv5 quota is below approved RQ2.2 limit: "
                    f"limit={quota['confidential_family'].get('limit')} required={APPROVED_CONFIDENTIAL_QUOTA_LIMIT}"
                )

            total_available = int(quota["total_regional_vcpus"].get("available") or 0)
            if total_available < ROLLING_PEAK_REGIONAL_VCPUS:
                errors.append(
                    f"Total regional vCPU availability is below RQ2.2 rolling peak: "
                    f"available={total_available} required={ROLLING_PEAK_REGIONAL_VCPUS}"
                )

            standard_payload = run_json_command([
                "az", "vm", "list-skus", "-l", selected_region, "--size", APPROVED_STANDARD_SIZE, "--output", "json"
            ], commands) or []
            confidential_payload = run_json_command([
                "az", "vm", "list-skus", "-l", selected_region, "--size", APPROVED_CONFIDENTIAL_SIZE, "--output", "json"
            ], commands) or []
            standard_sku = sku_summary(APPROVED_STANDARD_SIZE, standard_payload)
            confidential_sku = sku_summary(APPROVED_CONFIDENTIAL_SIZE, confidential_payload)
            if not standard_sku.get("found"):
                errors.append(f"Approved standard SKU not found in {selected_region}: {APPROVED_STANDARD_SIZE}")
            if not confidential_sku.get("found"):
                errors.append(f"Approved confidential SKU not found in {selected_region}: {APPROVED_CONFIDENTIAL_SIZE}")
            warnings.extend(sku_restriction_warnings(standard_sku, selected_region))
            warnings.extend(sku_restriction_warnings(confidential_sku, selected_region))
            standard_blockers = blocking_sku_restrictions(standard_sku)
            confidential_blockers = blocking_sku_restrictions(confidential_sku)
            if standard_blockers:
                errors.append(f"Approved standard SKU has blocking restrictions in {selected_region}: {standard_blockers}")
            if confidential_blockers:
                errors.append(f"Approved confidential SKU has blocking restrictions in {selected_region}: {confidential_blockers}")
            if standard_sku.get("found") and confidential_sku.get("found"):
                overhead_framing, hardware_near_basis, selected_pair_capability_differences = hardware_near_assessment(
                    standard_sku,
                    confidential_sku,
                )
                if overhead_framing != "hardware_near":
                    errors.append(f"Approved AMD pair is not hardware-near by Stage 0 basis: {hardware_near_basis}")
                warnings.extend(
                    difference["message"]
                    for difference in selected_pair_capability_differences
                    if difference.get("message")
                )

        if not errors:
            manifest_validation = run_generate_only_validation(config_path, artifact_dir, commands)
            if not manifest_validation.get("passed"):
                errors.extend(manifest_validation.get("errors") or ["generate-only manifest validation failed"])

        if args.validate_aks_nodepool and not errors:
            aks_status = validate_aks_nodepool(
                args.resource_group,
                args.cluster_name,
                commands,
                keep=args.keep_test_nodepool,
            )
            errors.extend(aks_status.get("errors") or [])
        elif args.dry_run:
            warnings.append("Dry-run does not validate live AKS confidential node-pool support")
        else:
            warnings.append("Live AKS confidential node-pool support was not requested")

    except Exception as exc:  # noqa: BLE001 - preserve failure context in artifact.
        errors.append(str(exc))

    benchmark_ready = (
        not errors
        and bool(manifest_validation.get("passed"))
        and bool(mtls_authz.get("preserved"))
        and aks_status.get("status") == "passed"
    )

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark_ready": benchmark_ready,
        "approved_plan": {
            "region": APPROVED_REGION,
            "backend": APPROVED_BACKEND,
            "standard_size": APPROVED_STANDARD_SIZE,
            "confidential_size": APPROVED_CONFIDENTIAL_SIZE,
            "standard_quota_family": APPROVED_STANDARD_FAMILY,
            "confidential_quota_family": APPROVED_CONFIDENTIAL_FAMILY,
            "standard_quota_limit": APPROVED_STANDARD_QUOTA_LIMIT,
            "confidential_quota_limit": APPROVED_CONFIDENTIAL_QUOTA_LIMIT,
            "rolling_peak_required_vcpus": ROLLING_PEAK_REGIONAL_VCPUS,
        },
        "config_checks": config_checks,
        "selected_region": selected_region,
        "selected_backend": APPROVED_BACKEND,
        "selected_standard_size": APPROVED_STANDARD_SIZE,
        "selected_confidential_size": APPROVED_CONFIDENTIAL_SIZE,
        "selected_node_pools": {
            "service1_standard": "r22s1std",
            "service2_standard": "r22s2std",
            "service2_confidential": "r22s2cvm",
        },
        "quota": quota,
        "sku_availability": {
            "standard": standard_sku,
            "confidential": confidential_sku,
        },
        "aks_nodepool_feasibility": aks_status,
        "rq21_mtls_authz_semantics": mtls_authz,
        "generate_only_manifests": manifest_validation,
        "overhead_framing": overhead_framing,
        "hardware_near_basis": hardware_near_basis,
        "selected_pair_capability_differences": selected_pair_capability_differences,
        "warnings": warnings,
        "errors": errors,
        "commands_attempted": commands,
    }
    out_path = artifact_dir / "rq22_preflight.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote RQ2.2 preflight artifact: {out_path}")
    for warning in warnings:
        print(warning, file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
