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


def _container_snapshot(pod: dict) -> dict:
    containers = pod.get("spec", {}).get("containers", [])
    container = containers[0] if containers else {}
    statuses = pod.get("status", {}).get("containerStatuses", [])
    status = statuses[0] if statuses else {}
    resources = container.get("resources", {})
    return {
        "image": container.get("image", "unknown"),
        "image_id": status.get("imageID", "unknown"),
        "image_pull_policy": container.get("imagePullPolicy", "unknown"),
        "resources": {
            "requests": resources.get("requests", {}) or {},
            "limits": resources.get("limits", {}) or {},
        },
    }


def _pod_snapshot(pod: dict) -> dict:
    snapshot = _container_snapshot(pod)
    snapshot.update({
        "pod_name": pod.get("metadata", {}).get("name", "unknown"),
        "node_name": pod.get("spec", {}).get("nodeName", "unknown"),
        "pod_ip": pod.get("status", {}).get("podIP", "unknown"),
        "qos_class": pod.get("status", {}).get("qosClass", "unknown"),
    })
    return snapshot


def _build_runtime_metadata(config_path: str, namespace: str, client_pod: str) -> dict:
    config = load_config(config_path)
    current_context = _kubectl_text(["config", "current-context"])
    try:
        cluster_info = _kubectl_text(["cluster-info"]).splitlines()[0]
    except Exception:
        cluster_info = "unknown"

    client_json = _kubectl_json(["get", "pod", client_pod, "-n", namespace, "-o", "json"])
    payload = {
        "captured_at": datetime.now().isoformat(),
        "namespace": namespace,
        "cluster_context": current_context,
        "cluster_info": cluster_info,
        "cluster_deployment": _build_cluster_deployment_metadata(
            namespace,
            current_context,
            cluster_info,
        ),
        "client": _pod_snapshot(client_json),
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
            "-n", namespace,
            "-l", f"condition={cond.name}",
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
                    f"{record['service_name']}.{namespace}.svc.cluster.local:"
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
    parser.add_argument("--namespace", default=None, help="Benchmark namespace (defaults to config value)")
    parser.add_argument("--client-pod", default="benchmark-client", help="Benchmark client pod name")
    parser.add_argument("--destination", default=DEFAULT_IN_POD_PATH, help="In-pod file path")
    parser.add_argument("--print-only", action="store_true", help="Print the collected JSON instead of injecting it")
    args = parser.parse_args()

    config = load_config(args.config)
    namespace = args.namespace or config.kubernetes.namespace
    payload = _build_runtime_metadata(args.config, namespace, args.client_pod)

    if args.print_only:
        print(json.dumps(payload, indent=2))
        return

    _inject_into_pod(namespace, args.client_pod, args.destination, payload)
    print(
        f"Injected runtime metadata for context {payload['cluster_context']} "
        f"into {args.client_pod}:{args.destination}"
    )


if __name__ == "__main__":
    main()