"""Fail-closed preflight for thesis-facing RQ1.5 full measurements.

The smoke deployment intentionally relaxes scheduling reservations to fit a quota-
constrained D4s_v3 node. The thesis-facing run should not proceed unless the live
cluster can support the same fully controlled request/limit profile used by the
RQ1.4 rolling benchmark methodology.
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.benchmark.config import load_config


def _kubectl_json(args: list[str]) -> dict:
    output = subprocess.check_output(["kubectl", *args], text=True)
    return json.loads(output)


def _kubectl_text(args: list[str]) -> str:
    return subprocess.check_output(["kubectl", *args], text=True).strip()


def parse_cpu_to_millicores(value: str) -> int:
    value = str(value).strip()
    if value.endswith("m"):
        return int(value[:-1])
    return int(float(value) * 1000)


def parse_memory_to_mib(value: str) -> int:
    value = str(value).strip()
    units = {
        "Ki": 1 / 1024,
        "Mi": 1,
        "Gi": 1024,
        "Ti": 1024 * 1024,
        "K": 1 / 1000,
        "M": 1000 / 1024,
        "G": 1000 * 1000 / 1024,
    }
    match = re.fullmatch(r"([0-9.]+)([A-Za-z]+)?", value)
    if not match:
        raise ValueError(f"Unsupported memory quantity: {value}")
    number = float(match.group(1))
    unit = match.group(2) or "Mi"
    if unit not in units:
        raise ValueError(f"Unsupported memory unit: {unit}")
    return int(number * units[unit])


def _service_count(condition) -> int:
    return len(condition.chain_split_points or []) + 1


def _validate_full_controlled_profile(config) -> list[str]:
    errors = []
    res = config.kubernetes.resources
    client = config.kubernetes.client_resources

    if res.cpu_request != res.cpu_limit:
        errors.append(
            f"service cpu_request ({res.cpu_request}) != cpu_limit ({res.cpu_limit}); exact RQ1.4 parity requires Guaranteed QoS"
        )
    if res.memory_request != res.memory_limit:
        errors.append(
            f"service memory_request ({res.memory_request}) != memory_limit ({res.memory_limit}); exact RQ1.4 parity requires Guaranteed QoS"
        )
    if not re.fullmatch(r"[0-9]+", res.cpu_request):
        errors.append(
            f"service cpu_request ({res.cpu_request}) is not an integer core value; exact RQ1.4 parity requires integer CPU"
        )
    if client.cpu_request != client.cpu_limit:
        errors.append(
            f"client cpu_request ({client.cpu_request}) != cpu_limit ({client.cpu_limit}); keep the client fully controlled for the thesis run"
        )
    if client.memory_request != client.memory_limit:
        errors.append(
            f"client memory_request ({client.memory_request}) != memory_limit ({client.memory_limit}); keep the client fully controlled for the thesis run"
        )
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Fail-closed preflight for thesis-facing RQ1.5 full measurements"
    )
    parser.add_argument("--config", default="configs/rq1/1.5/rq1_5_full.yaml")
    parser.add_argument(
        "--mode",
        choices=["rolling", "simultaneous"],
        default="rolling",
        help="Capacity model: rolling matches the established RQ1.4 fully controlled methodology",
    )
    parser.add_argument("--namespace", default=None)
    parser.add_argument("--nodepool", default="rq15pool")
    args = parser.parse_args()

    config = load_config(args.config)
    namespace = args.namespace or config.kubernetes.namespace
    errors = _validate_full_controlled_profile(config)

    current_context = _kubectl_text(["config", "current-context"])
    if current_context == "docker-desktop":
        errors.append("kubectl current-context is docker-desktop; thesis-facing AKS measurements must run against the AKS cluster")

    nodes = _kubectl_json([
        "get", "nodes",
        "-l", f"agentpool={args.nodepool}",
        "-o", "json",
    ]).get("items", [])
    ready_nodes = []
    for node in nodes:
        conditions = node.get("status", {}).get("conditions", [])
        if any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions):
            ready_nodes.append(node)
    if not ready_nodes:
        errors.append(f"No Ready nodes found in agentpool={args.nodepool}")
        allocatable_cpu_mcpu = 0
        allocatable_mem_mib = 0
    else:
        allocatable_cpu_mcpu = max(
            parse_cpu_to_millicores(node["status"]["allocatable"]["cpu"])
            for node in ready_nodes
        )
        allocatable_mem_mib = max(
            parse_memory_to_mib(node["status"]["allocatable"]["memory"])
            for node in ready_nodes
        )

    current_requested_cpu_mcpu = 0
    current_requested_mem_mib = 0
    for pod in _kubectl_json(["get", "pods", "-A", "-o", "json"]).get("items", []):
        pod_namespace = pod.get("metadata", {}).get("namespace", "")
        if pod_namespace == namespace:
            continue
        phase = pod.get("status", {}).get("phase")
        if phase in {"Succeeded", "Failed"}:
            continue
        for container in pod.get("spec", {}).get("containers", []):
            requests = container.get("resources", {}).get("requests", {})
            cpu_value = requests.get("cpu")
            mem_value = requests.get("memory")
            if cpu_value is not None:
                current_requested_cpu_mcpu += parse_cpu_to_millicores(cpu_value)
            if mem_value is not None:
                current_requested_mem_mib += parse_memory_to_mib(mem_value)

    service_count_values = [_service_count(cond) for cond in config.conditions]
    service_cpu_mcpu = parse_cpu_to_millicores(config.kubernetes.resources.cpu_request)
    service_mem_mib = parse_memory_to_mib(config.kubernetes.resources.memory_request)
    client_cpu_mcpu = parse_cpu_to_millicores(config.kubernetes.client_resources.cpu_request)
    client_mem_mib = parse_memory_to_mib(config.kubernetes.client_resources.memory_request)

    if args.mode == "rolling":
        benchmark_cpu_mcpu = client_cpu_mcpu + max(service_count_values, default=0) * service_cpu_mcpu
        benchmark_mem_mib = client_mem_mib + max(service_count_values, default=0) * service_mem_mib
    else:
        benchmark_cpu_mcpu = client_cpu_mcpu + sum(count * service_cpu_mcpu for count in service_count_values)
        benchmark_mem_mib = client_mem_mib + sum(count * service_mem_mib for count in service_count_values)

    required_cpu_mcpu = current_requested_cpu_mcpu + benchmark_cpu_mcpu
    required_mem_mib = current_requested_mem_mib + benchmark_mem_mib

    if required_cpu_mcpu > allocatable_cpu_mcpu:
        errors.append(
            "CPU capacity preflight failed: "
            f"allocatable={allocatable_cpu_mcpu / 1000.0:.3f} cores, "
            f"current non-{namespace} requested={current_requested_cpu_mcpu / 1000.0:.3f} cores, "
            f"benchmark requested={benchmark_cpu_mcpu / 1000.0:.3f} cores, "
            f"mode={args.mode}."
        )
    if required_mem_mib > allocatable_mem_mib:
        errors.append(
            "Memory capacity preflight failed: "
            f"allocatable={allocatable_mem_mib} MiB, "
            f"current non-{namespace} requested={current_requested_mem_mib} MiB, "
            f"benchmark requested={benchmark_mem_mib} MiB, "
            f"mode={args.mode}."
        )

    print(f"Context: {current_context}")
    print(f"Namespace: {namespace}")
    print(f"Nodepool: {args.nodepool}")
    print(f"Mode: {args.mode}")
    print(f"Ready nodes in pool: {len(ready_nodes)}")
    print(f"Largest-node allocatable CPU: {allocatable_cpu_mcpu / 1000.0:.3f} cores")
    print(f"Largest-node allocatable memory: {allocatable_mem_mib} MiB")
    print(f"Current non-{namespace} requested CPU: {current_requested_cpu_mcpu / 1000.0:.3f} cores")
    print(f"Current non-{namespace} requested memory: {current_requested_mem_mib} MiB")
    print(f"Benchmark requested CPU: {benchmark_cpu_mcpu / 1000.0:.3f} cores")
    print(f"Benchmark requested memory: {benchmark_mem_mib} MiB")

    if errors:
        print("\nPreflight FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(
            "\nRecommendation: use a thesis-facing cluster/profile that can sustain the rolling full-family deployment with Guaranteed QoS. "
            "In practice that means an AKS node with at least ~6 allocatable CPU cores and ~6 GiB allocatable memory after system reservations. "
            "A D8-class node is the practical starting point; the current D4s_v3 smoke cluster is not.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nPreflight PASSED: cluster capacity and QoS profile are sufficient for the thesis-facing RQ1.5 run.")


if __name__ == "__main__":
    main()