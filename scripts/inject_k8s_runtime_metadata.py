"""Collect live Kubernetes deployment metadata on the host and inject it into the benchmark client pod.

This solves the provenance gap for in-cluster benchmark runs where the client pod
cannot reliably discover service pod identities or the host-side kube context.
The runner reads the injected file from /tmp/k8s_runtime_metadata.json and writes
the resolved deployment profile into deployment_metadata.json.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.benchmark.config import load_config, format_k8s_service_name


DEFAULT_IN_POD_PATH = "/tmp/k8s_runtime_metadata.json"


def _kubectl_json(args: list[str]) -> dict:
    output = subprocess.check_output(["kubectl", *args], text=True)
    return json.loads(output)


def _kubectl_text(args: list[str]) -> str:
    return subprocess.check_output(["kubectl", *args], text=True).strip()


def _kubectl_json_or_none(args: list[str]) -> dict | None:
    try:
        return _kubectl_json(args)
    except Exception:
        return None


def _load_raw_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload if isinstance(payload, dict) else {}


def _raw_k8s_config(config_path: str) -> dict:
    raw = _load_raw_config(config_path)
    k8s = raw.get("kubernetes") or {}
    return k8s if isinstance(k8s, dict) else {}


def _raw_mesh_config(raw_k8s: dict) -> dict:
    mesh = raw_k8s.get("mesh") or {}
    return mesh if isinstance(mesh, dict) else {}


def _az_json_or_none(args: list[str]) -> dict | list | None:
    if shutil.which("az") is None:
        return None
    try:
        output = subprocess.check_output(["az", *args, "--output", "json"], text=True)
        return json.loads(output)
    except Exception:
        return None


def _normalize_cni_name(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized == "azure":
        return "azure-cni"
    return normalized


def _select_aks_cluster(current_context: str, cluster_info: str) -> dict:
    clusters = _az_json_or_none(["aks", "list"])
    if not isinstance(clusters, list):
        return {}

    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        name = str(cluster.get("name", ""))
        fqdn = str(cluster.get("fqdn", ""))
        if name and name == current_context:
            return cluster
        if fqdn and fqdn in cluster_info:
            return cluster

    if len(clusters) == 1 and isinstance(clusters[0], dict):
        return clusters[0]
    return {}


def _summarize_values(values: set[str]) -> str | None:
    cleaned = sorted({value for value in values if value and value != "unknown"})
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned)


def _build_cluster_deployment_metadata(namespace: str, current_context: str, cluster_info: str) -> dict:
    deployment = {
        "type": "kubernetes",
        "namespace": namespace,
    }

    version_payload = _kubectl_json_or_none(["version", "-o", "json"])
    if isinstance(version_payload, dict):
        deployment["cluster_version"] = (
            version_payload.get("serverVersion", {}) or {}
        ).get("gitVersion")

    nodes_payload = _kubectl_json_or_none(["get", "nodes", "-o", "json"])
    if isinstance(nodes_payload, dict):
        nodes = nodes_payload.get("items") or []
        if nodes:
            deployment["node_count"] = len(nodes)
        instance_types = set()
        regions = set()
        for node in nodes:
            labels = ((node.get("metadata") or {}).get("labels") or {})
            instance_types.add(
                str(
                    labels.get("node.kubernetes.io/instance-type")
                    or labels.get("beta.kubernetes.io/instance-type")
                    or ""
                )
            )
            regions.add(
                str(
                    labels.get("topology.kubernetes.io/region")
                    or labels.get("failure-domain.beta.kubernetes.io/region")
                    or ""
                )
            )
        deployment["node_instance_type"] = _summarize_values(instance_types)
        deployment["azure_region"] = _summarize_values(regions)

    aks_cluster = _select_aks_cluster(current_context, cluster_info)
    if aks_cluster:
        deployment["cluster_type"] = "aks"
        deployment["cluster_version"] = aks_cluster.get("kubernetesVersion") or deployment.get("cluster_version")
        deployment["azure_region"] = aks_cluster.get("location") or deployment.get("azure_region")
        deployment["cni"] = _normalize_cni_name(
            ((aks_cluster.get("networkProfile") or {}).get("networkPlugin"))
        )
        pool_profiles = aks_cluster.get("agentPoolProfiles") or []
        total_nodes = 0
        vm_sizes = set()
        for pool in pool_profiles:
            if not isinstance(pool, dict):
                continue
            count = pool.get("count")
            if isinstance(count, int):
                total_nodes += count
            vm_sizes.add(str(pool.get("vmSize") or ""))
        if total_nodes > 0:
            deployment["node_count"] = total_nodes
        deployment["node_instance_type"] = _summarize_values(vm_sizes) or deployment.get("node_instance_type")
    elif ".azmk8s.io" in cluster_info:
        deployment["cluster_type"] = "aks"

    return {
        key: value
        for key, value in deployment.items()
        if value not in (None, "")
    }


def _container_records(pod: dict) -> list[dict]:
    app_containers = [
        ("app", container)
        for container in pod.get("spec", {}).get("containers", [])
        if isinstance(container, dict)
    ]
    init_containers = [
        ("init", container)
        for container in pod.get("spec", {}).get("initContainers", [])
        if isinstance(container, dict)
    ]
    containers = init_containers + app_containers
    status_payload = pod.get("status", {})
    statuses = (
        (status_payload.get("containerStatuses") or [])
        + (status_payload.get("initContainerStatuses") or [])
    )
    status_by_name = {
        str(status.get("name")): status
        for status in statuses
        if isinstance(status, dict)
    }
    records = []
    for container_type, container in containers:
        status = status_by_name.get(str(container.get("name")), {})
        resources = container.get("resources", {}) or {}
        records.append({
            "name": container.get("name", "unknown"),
            "container_type": container_type,
            "native_sidecar": container_type == "init" and container.get("name") == "istio-proxy",
            "image": container.get("image", "unknown"),
            "image_id": status.get("imageID", "unknown"),
            "image_pull_policy": container.get("imagePullPolicy", "unknown"),
            "ready": bool(status.get("ready", False)),
            "restart_count": status.get("restartCount", 0),
            "resources": {
                "requests": resources.get("requests", {}) or {},
                "limits": resources.get("limits", {}) or {},
            },
        })
    return records


def _container_snapshot(pod: dict) -> dict:
    records = _container_records(pod)
    app_records = [record for record in records if record.get("container_type") == "app"]
    container = app_records[0] if app_records else (records[0] if records else {})
    sidecars = [record for record in records if record.get("name") == "istio-proxy"]
    resources = container.get("resources", {})
    return {
        "image": container.get("image", "unknown"),
        "image_id": container.get("image_id", "unknown"),
        "image_pull_policy": container.get("image_pull_policy", "unknown"),
        "resources": {
            "requests": resources.get("requests", {}) or {},
            "limits": resources.get("limits", {}) or {},
        },
        "containers": records,
        "sidecar_present": bool(sidecars),
        "sidecars": sidecars,
        "sidecar_image_ids": [
            record.get("image_id", "unknown")
            for record in sidecars
            if record.get("image_id") not in (None, "")
        ],
    }


def _pod_snapshot(pod: dict) -> dict:
    metadata = pod.get("metadata", {}) or {}
    spec = pod.get("spec", {}) or {}
    snapshot = _container_snapshot(pod)
    snapshot.update({
        "pod_name": metadata.get("name", "unknown"),
        "node_name": spec.get("nodeName", "unknown"),
        "pod_ip": pod.get("status", {}).get("podIP", "unknown"),
        "qos_class": pod.get("status", {}).get("qosClass", "unknown"),
        "service_account_name": spec.get("serviceAccountName", "unknown"),
        "labels": metadata.get("labels", {}) or {},
        "annotations": metadata.get("annotations", {}) or {},
    })
    return snapshot


def _placement_policy(config) -> dict:
    placement = config.kubernetes.placement
    policy = {
        "strategy": placement.strategy,
        "require_same_node": bool(placement.require_same_node),
        "fail_if_not_colocated": bool(placement.fail_if_not_colocated),
        "node_selector": dict(placement.node_selector),
        "node_pool": placement.node_pool,
    }
    return {
        key: value
        for key, value in policy.items()
        if value not in (None, "") and not (isinstance(value, dict) and not value)
    }


def _namespace_snapshot(namespace: str) -> dict:
    payload = _kubectl_json_or_none(["get", "namespace", namespace, "-o", "json"])
    if not isinstance(payload, dict):
        return {"name": namespace, "labels": {}, "annotations": {}}
    metadata = payload.get("metadata") or {}
    return {
        "name": namespace,
        "labels": metadata.get("labels", {}) or {},
        "annotations": metadata.get("annotations", {}) or {},
    }


def _peer_authentication_resources(namespace: str) -> list[dict]:
    payload = _kubectl_json_or_none([
        "get",
        "peerauthentication.security.istio.io",
        "-n",
        namespace,
        "-o",
        "json",
    ])
    if not isinstance(payload, dict):
        return []
    records = []
    for item in payload.get("items") or []:
        metadata = item.get("metadata") or {}
        records.append({
            "name": metadata.get("name", "unknown"),
            "namespace": metadata.get("namespace", namespace),
            "labels": metadata.get("labels", {}) or {},
            "spec": item.get("spec", {}) or {},
        })
    return records


def _mesh_control_plane_pods() -> list[dict]:
    payload = _kubectl_json_or_none(["get", "pods", "-A", "-o", "json"])
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
        })
    return records


def _mesh_metadata(raw_k8s: dict, service_namespace: str, client_namespace: str) -> dict:
    mesh = _raw_mesh_config(raw_k8s)
    enabled = bool(mesh.get("enabled", False))
    return {
        "enabled": enabled,
        "implementation": mesh.get("implementation"),
        "revision": mesh.get("revision"),
        "service_namespace": service_namespace,
        "client_namespace": client_namespace,
        "service_accounts": mesh.get("service_accounts") or {},
        "proxy_resources": mesh.get("proxy_resources") or {},
        "peer_authentication": {
            "declared": (mesh.get("peer_authentication") or {}),
            "observed": _peer_authentication_resources(service_namespace) if enabled else [],
        },
        "control_plane_pods": _mesh_control_plane_pods() if enabled else [],
    }


def _build_runtime_metadata(
    config_path: str,
    namespace: str,
    client_pod: str,
    client_namespace: str | None = None,
) -> dict:
    config = load_config(config_path)
    raw_k8s = _raw_k8s_config(config_path)
    service_namespace = namespace
    resolved_client_namespace = client_namespace or str(
        raw_k8s.get("client_namespace") or service_namespace
    )
    current_context = _kubectl_text(["config", "current-context"])
    try:
        cluster_info = _kubectl_text(["cluster-info"]).splitlines()[0]
    except Exception:
        cluster_info = "unknown"

    client_json = _kubectl_json([
        "get",
        "pod",
        client_pod,
        "-n",
        resolved_client_namespace,
        "-o",
        "json",
    ])
    payload = {
        "captured_at": datetime.now().isoformat(),
        "namespace": service_namespace,
        "namespaces": {
            "service": _namespace_snapshot(service_namespace),
            "client": _namespace_snapshot(resolved_client_namespace),
        },
        "cluster_context": current_context,
        "cluster_info": cluster_info,
        "cluster_deployment": _build_cluster_deployment_metadata(
            service_namespace,
            current_context,
            cluster_info,
        ),
        "placement_policy": _placement_policy(config),
        "client": _pod_snapshot(client_json),
        "mesh": _mesh_metadata(raw_k8s, service_namespace, resolved_client_namespace),
        "conditions": {},
    }

    for cond in config.conditions:
        svc_name_map = {
            str(index): format_k8s_service_name(
                config.kubernetes.service_name_template,
                cond.name,
                index,
            )
            for index in range(1, len(cond.chain_split_points or []) + 2)
        }

        pod_list = _kubectl_json([
            "get", "pods",
            "-n", service_namespace,
            "-l", f"condition={cond.name},workload-role=service",
            "-o", "json",
        ])
        records = []
        for item in pod_list.get("items", []):
            labels = item.get("metadata", {}).get("labels", {})
            seg_idx = str(labels.get("segment-index", "unknown"))
            record = _pod_snapshot(item)
            record["segment_index"] = seg_idx
            record["service_name"] = svc_name_map.get(seg_idx, "unknown")
            if record["service_name"] != "unknown":
                record["address"] = (
                    f"{record['service_name']}.{service_namespace}.svc.cluster.local:"
                    f"{config.kubernetes.grpc_port}"
                )
            records.append(record)
        payload["conditions"][cond.name] = records

    return payload


def _inject_into_pod(namespace: str, client_pod: str, destination: str, payload: dict):
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    subprocess.run(
        [
            "kubectl", "exec", "-n", namespace, client_pod, "--",
            "python", "-c",
            (
                "import base64, pathlib, sys; "
                "pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(sys.argv[2]))"
            ),
            destination,
            encoded,
        ],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Inject live Kubernetes deployment metadata into the benchmark client pod"
    )
    parser.add_argument("--config", required=True, help="Path to experiment config YAML")
    parser.add_argument("--namespace", default=None, help="Inference service namespace (defaults to config value)")
    parser.add_argument(
        "--client-namespace",
        default=None,
        help="Benchmark client namespace (defaults to kubernetes.client_namespace or --namespace)",
    )
    parser.add_argument("--client-pod", default="benchmark-client", help="Benchmark client pod name")
    parser.add_argument("--destination", default=DEFAULT_IN_POD_PATH, help="In-pod file path")
    parser.add_argument("--print-only", action="store_true", help="Print the collected JSON instead of injecting it")
    args = parser.parse_args()

    config = load_config(args.config)
    namespace = args.namespace or config.kubernetes.namespace
    raw_k8s = _raw_k8s_config(args.config)
    client_namespace = args.client_namespace or str(raw_k8s.get("client_namespace") or namespace)
    payload = _build_runtime_metadata(args.config, namespace, args.client_pod, client_namespace)

    if args.print_only:
        print(json.dumps(payload, indent=2))
        return

    _inject_into_pod(client_namespace, args.client_pod, args.destination, payload)
    print(
        f"Injected runtime metadata for context {payload['cluster_context']} "
        f"into {client_namespace}/{args.client_pod}:{args.destination}"
    )


if __name__ == "__main__":
    main()
