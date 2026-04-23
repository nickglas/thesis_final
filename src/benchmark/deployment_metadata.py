from __future__ import annotations

import re
from typing import Any


_SHA256_PATTERN = re.compile(r"(sha256:[0-9a-fA-F]{32,})")
_AKS_REGION_PATTERN = re.compile(r"\.hcp\.([a-z0-9-]+)\.azmk8s\.io", re.IGNORECASE)


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_container_image_digest(*image_refs: Any) -> str | None:
    for image_ref in image_refs:
        if not isinstance(image_ref, str):
            continue
        match = _SHA256_PATTERN.search(image_ref)
        if match:
            return match.group(1)
    return None


def _parse_acr_registry(image_ref: Any) -> str | None:
    if not isinstance(image_ref, str) or "/" not in image_ref:
        return None
    registry = image_ref.split("/", 1)[0].strip()
    if "." not in registry:
        return None
    return registry


def _infer_cluster_type(sample_meta: dict[str, Any], cluster_deployment: dict[str, Any]) -> str:
    explicit = str(cluster_deployment.get("cluster_type") or "").strip()
    if explicit:
        return explicit

    cluster_context = str(sample_meta.get("cluster_context") or "").lower()
    cluster_info = str(sample_meta.get("cluster_info") or "").lower()
    if ".azmk8s.io" in cluster_info or cluster_context.startswith("aks"):
        return "aks"
    if "kind" in cluster_context:
        return "kind"
    return "kubernetes"


def _infer_azure_region(sample_meta: dict[str, Any], cluster_deployment: dict[str, Any]) -> str | None:
    explicit = _first_non_empty(cluster_deployment.get("azure_region"))
    if explicit is not None:
        return explicit

    cluster_info = str(sample_meta.get("cluster_info") or "")
    match = _AKS_REGION_PATTERN.search(cluster_info)
    if match:
        return match.group(1)
    return None


def _collect_pod_placement(
    deployment_metadata: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], bool]:
    placement: dict[str, str] = {}
    colocated = True
    required_conditions = 0

    for condition_meta in deployment_metadata.values():
        if not isinstance(condition_meta, dict):
            continue

        client = condition_meta.get("client") or {}
        client_name = client.get("pod_name")
        client_node = client.get("node_name")
        if client_name and client_node and client_name != "unknown" and client_node != "unknown":
            placement[str(client_name)] = str(client_node)

        service_nodes = set()
        services = condition_meta.get("services") or []
        for service in services:
            if not isinstance(service, dict):
                continue
            service_name = service.get("service_name")
            node_name = service.get("node_name")
            if service_name and node_name and node_name != "unknown":
                placement[str(service_name)] = str(node_name)
                service_nodes.add(str(node_name))

        validation = condition_meta.get("placement_validation") or {}
        if bool(validation.get("required")):
            required_conditions += 1
            if str(validation.get("status")) != "pass":
                colocated = False

    return placement, colocated if required_conditions else False


def _collect_condition_placement_validation(
    deployment_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    conditions: dict[str, dict[str, Any]] = {}
    checked_conditions: list[str] = []
    required_conditions: list[str] = []
    all_required_conditions_passed = True

    for condition_name, condition_meta in deployment_metadata.items():
        if not isinstance(condition_meta, dict):
            continue

        validation = condition_meta.get("placement_validation") or {}
        if not isinstance(validation, dict) or not validation:
            continue

        summary = {
            "checked": bool(validation.get("checked")),
            "required": bool(validation.get("required")),
            "status": validation.get("status") or "unknown",
            "colocated": validation.get("colocated"),
            "client_node": validation.get("client_node") or "unknown",
            "service_nodes": list(validation.get("service_nodes") or []),
        }
        conditions[str(condition_name)] = summary
        if summary["checked"]:
            checked_conditions.append(str(condition_name))
        if summary["required"]:
            required_conditions.append(str(condition_name))
            if summary["status"] != "pass":
                all_required_conditions_passed = False

    payload = {
        "conditions": conditions,
        "checked_conditions": checked_conditions,
        "required_conditions": required_conditions,
    }
    if required_conditions:
        payload["all_required_conditions_passed"] = all_required_conditions_passed
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {})
    }


def build_environment_deployment_section(
    deployment_metadata: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Aggregate per-condition deployment metadata into environment.json schema."""
    if not isinstance(deployment_metadata, dict) or not deployment_metadata:
        return {}

    sample_meta = next(
        (
            condition_meta
            for condition_meta in deployment_metadata.values()
            if isinstance(condition_meta, dict)
        ),
        None,
    )
    if not isinstance(sample_meta, dict):
        return {}

    cluster_deployment = sample_meta.get("cluster_deployment") or {}
    placement, pod_colocation_enforced = _collect_pod_placement(deployment_metadata)
    placement_policy = sample_meta.get("placement_policy") or {}
    placement_validation = _collect_condition_placement_validation(deployment_metadata)
    cluster_type = _infer_cluster_type(sample_meta, cluster_deployment)

    node_count = _coerce_int(cluster_deployment.get("node_count"))
    if node_count is None and placement:
        node_count = len(set(placement.values()))

    digest = None
    registry = None
    for condition_meta in deployment_metadata.values():
        if not isinstance(condition_meta, dict):
            continue

        client = condition_meta.get("client") or {}
        digest = digest or _parse_container_image_digest(
            client.get("image"),
            client.get("image_id"),
        )
        registry = registry or _parse_acr_registry(client.get("image"))

        for service in condition_meta.get("services") or []:
            if not isinstance(service, dict):
                continue
            digest = digest or _parse_container_image_digest(
                service.get("image"),
                service.get("image_id"),
            )
            registry = registry or _parse_acr_registry(service.get("image"))

    deployment = {
        "type": "kubernetes",
        "cluster_type": cluster_type,
        "cluster_version": _first_non_empty(cluster_deployment.get("cluster_version")),
        "node_count": node_count,
        "node_instance_type": _first_non_empty(cluster_deployment.get("node_instance_type")),
        "azure_region": _infer_azure_region(sample_meta, cluster_deployment),
        "cni": _first_non_empty(cluster_deployment.get("cni")),
        "namespace": _first_non_empty(cluster_deployment.get("namespace"), sample_meta.get("namespace")),
        "pod_colocation_enforced": pod_colocation_enforced,
        "placement_policy": placement_policy,
        "placement_validation": placement_validation,
        "pod_placement": placement,
        "container_image_digest": digest,
        "acr_registry": registry,
    }

    if cluster_type == "aks":
        if deployment.get("cluster_version") in (None, ""):
            deployment["cluster_version"] = "unknown"
        if deployment.get("node_count") in (None, ""):
            deployment["node_count"] = len(set(placement.values())) if placement else 0
        if deployment.get("node_instance_type") in (None, ""):
            deployment["node_instance_type"] = "unknown"
        if deployment.get("azure_region") in (None, ""):
            deployment["azure_region"] = "unknown"
        if deployment.get("cni") in (None, ""):
            deployment["cni"] = "unknown"

    return {
        key: value
        for key, value in deployment.items()
        if value not in (None, "") and not (isinstance(value, dict) and not value)
    }