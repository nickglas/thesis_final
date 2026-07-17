from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

from src.benchmark.config import format_k8s_service_name, load_config
from src.benchmark.deployment_metadata import build_environment_deployment_section
from src.benchmark.logging import ArtifactLogger
from src.benchmark.runner import BenchmarkRunner
from src.models.validation import validate_equivalence


RUNTIME_METADATA_PATH = "/tmp/k8s_runtime_metadata.json"


class RemoteServiceBenchmarkRunner(BenchmarkRunner):
    """BenchmarkRunner variant for AKS split conditions with external Service B."""

    def _start_service_b(self, split_after: str):
        logger = logging.getLogger("rq1_1_aks")
        logger.info(
            "Using externally deployed Service B for %s at %s:%s",
            split_after,
            self.config.grpc_host,
            self.config.grpc_port,
        )
        return None

    def _stop_service_b(self, proc) -> None:
        return None


def _is_running_in_kubernetes() -> bool:
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True
    return os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace")


def _assert_in_cluster_execution(config, config_path: str, logger: logging.Logger) -> None:
    if _is_running_in_kubernetes():
        return

    namespace = config.kubernetes.namespace
    logger.error(
        "RQ1.1 AKS benchmarking must run from inside the Kubernetes cluster."
    )
    logger.error(
        "Run instead: kubectl exec -it -n %s benchmark-client -- python -m src.benchmark.k8s_split_experiment --config %s --condition <name>",
        namespace,
        config_path,
    )
    sys.exit(1)


def _read_runtime_metadata(path: str = RUNTIME_METADATA_PATH) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _resolve_condition(config, condition_name: str):
    selected = [cond for cond in config.conditions if cond.name == condition_name]
    if not selected:
        available = ", ".join(cond.name for cond in config.conditions)
        raise ValueError(
            f"Condition '{condition_name}' was not found in config. Available conditions: {available}"
        )
    config.conditions = selected
    return selected[0]


def _service_host_and_address(config, condition) -> tuple[str, str, str]:
    service_name = format_k8s_service_name(
        config.kubernetes.service_name_template,
        condition.name,
        1,
    )
    service_host = f"{service_name}.{config.kubernetes.namespace}.svc.cluster.local"
    service_address = f"{service_host}:{config.kubernetes.grpc_port}"
    return service_name, service_host, service_address


def _declared_kubernetes_config(config) -> dict[str, Any]:
    k8s = config.kubernetes
    return {
        "image": k8s.image,
        "image_pull_policy": k8s.image_pull_policy,
        "service_resources": {
            "requests": {
                "cpu": k8s.resources.cpu_request,
                "memory": k8s.resources.memory_request,
            },
            "limits": {
                "cpu": k8s.resources.cpu_limit,
                "memory": k8s.resources.memory_limit,
            },
        },
        "client_resources": {
            "requests": {
                "cpu": k8s.client_resources.cpu_request,
                "memory": k8s.client_resources.memory_request,
            },
            "limits": {
                "cpu": k8s.client_resources.cpu_limit,
                "memory": k8s.client_resources.memory_limit,
            },
        },
    }


def _placement_policy(config) -> dict[str, Any]:
    placement = config.kubernetes.placement
    policy = {
        "strategy": placement.strategy,
        "require_same_node": bool(placement.require_same_node),
        "fail_if_not_colocated": bool(placement.fail_if_not_colocated),
        "node_selector": dict(placement.node_selector),
        "node_pool": placement.node_pool,
        "tolerations": list(placement.tolerations),
        "require_control_plane_isolation": bool(placement.require_control_plane_isolation),
    }
    return {
        key: value
        for key, value in policy.items()
        if value not in (None, "") and not (isinstance(value, (dict, list)) and not value)
    }


def _placement_validation(config, condition, runtime_meta: dict[str, Any], services: list[dict[str, Any]]) -> dict[str, Any]:
    policy = runtime_meta.get("placement_policy") or _placement_policy(config)
    client = runtime_meta.get("client") or {}
    checked = condition.type == "split" and str(policy.get("strategy") or "none") != "none"
    required = condition.type == "split" and bool(policy.get("require_same_node"))
    service_pods = []
    service_nodes = set()
    for service in services:
        if not isinstance(service, dict):
            continue
        record = {
            "service_name": service.get("service_name") or "unknown",
            "pod_name": service.get("pod_name") or "unknown",
            "node_name": service.get("node_name") or "unknown",
            "segment_index": service.get("segment_index") or "unknown",
        }
        service_pods.append(record)
        node_name = str(record["node_name"])
        if node_name and node_name != "unknown":
            service_nodes.add(node_name)

    client_node = str(client.get("node_name") or "unknown")
    if condition.type != "split":
        status = "not_applicable"
        colocated = None
    elif len(service_pods) != 1 or client_node == "unknown" or len(service_nodes) != 1:
        status = "unknown"
        colocated = None
    else:
        colocated = client_node in service_nodes
        status = "pass" if colocated else "fail"

    return {
        "strategy": policy.get("strategy") or "none",
        "checked": checked,
        "required": required,
        "fail_if_not_colocated": bool(policy.get("fail_if_not_colocated")),
        "status": status,
        "colocated": colocated,
        "client_pod": client.get("pod_name") or "unknown",
        "client_node": client_node,
        "service_nodes": sorted(service_nodes),
        "service_pods": service_pods,
    }


def _fallback_service_record(config, condition) -> dict[str, Any]:
    service_name, _, service_address = _service_host_and_address(config, condition)
    k8s = config.kubernetes
    return {
        "service_name": service_name,
        "address": service_address,
        "segment_index": "1",
        "pod_name": "unknown",
        "node_name": "unknown",
        "pod_ip": "unknown",
        "image": k8s.image,
        "image_id": "unknown",
        "image_pull_policy": k8s.image_pull_policy,
        "qos_class": "unknown",
        "resources": {
            "requests": {
                "cpu": k8s.resources.cpu_request,
                "memory": k8s.resources.memory_request,
            },
            "limits": {
                "cpu": k8s.resources.cpu_limit,
                "memory": k8s.resources.memory_limit,
            },
        },
    }


def _build_condition_deployment_metadata(config, condition, runtime_meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    services = list((runtime_meta.get("conditions") or {}).get(condition.name, []))
    if condition.type == "split" and not services:
        services = [_fallback_service_record(config, condition)]
    placement_policy = runtime_meta.get("placement_policy") or _placement_policy(config)
    placement_validation = _placement_validation(config, condition, runtime_meta, services)

    payload = {
        "namespace": config.kubernetes.namespace,
        "condition": condition.name,
        "num_services": 0 if condition.type == "monolithic" else len(services),
        "split_after": condition.split_after,
        "services": services,
        "declared_kubernetes_config": _declared_kubernetes_config(config),
        "placement_policy": placement_policy,
        "placement_validation": placement_validation,
        "cluster_context": runtime_meta.get("cluster_context") or "unknown",
        "cluster_info": runtime_meta.get("cluster_info") or "unknown",
        "cluster_deployment": runtime_meta.get("cluster_deployment") or {},
        "client": runtime_meta.get("client") or {},
        "collected_at": runtime_meta.get("captured_at") or datetime.now().isoformat(),
    }
    return {condition.name: payload}


def _validate_local_parity(config, condition, logger: logging.Logger) -> dict[str, dict[str, Any]]:
    if condition.type != "split":
        logger.info("Selected condition is monolithic; no split parity validation is required.")
        return {}

    logger.info("Running local split parity validation for %s", condition.split_after)
    parity_results = validate_equivalence(
        split_points=[condition.split_after],
        atol=config.parity_atol,
        num_inputs=config.parity_num_inputs,
        seed=config.seed,
    )

    info = parity_results[condition.split_after]
    status = "PASS" if info["match"] else "FAIL"
    logger.info(
        "  %s: %s (max_abs_diff=%.2e)",
        condition.split_after,
        status,
        info["max_abs_diff"],
    )
    if not info["match"]:
        raise RuntimeError(
            f"Local parity validation failed for {condition.name} ({condition.split_after})"
        )
    return parity_results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="In-cluster AKS entrypoint for RQ1.1 coarse split benchmarking"
    )
    parser.add_argument("--config", required=True, help="Path to experiment config YAML")
    parser.add_argument("--condition", required=True, help="Single RQ1.1 condition to execute")
    parser.add_argument("--output-dir", default=None, help="Override output directory")
    parser.add_argument(
        "--grpc-host",
        default=None,
        help="Override the Service B DNS host for split conditions",
    )
    parser.add_argument(
        "--grpc-port",
        type=int,
        default=None,
        help="Override the Service B gRPC port for split conditions",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("rq1_1_aks")

    config = load_config(args.config)
    if config.kubernetes is None:
        logger.error("Config file must include a 'kubernetes' section for AKS experiments.")
        return 1

    try:
        condition = _resolve_condition(config, args.condition)
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    _assert_in_cluster_execution(config, args.config, logger)

    if condition.type == "split":
        service_name, service_host, service_address = _service_host_and_address(config, condition)
        config.grpc_host = args.grpc_host or service_host
        config.grpc_port = args.grpc_port or config.kubernetes.grpc_port
        logger.info(
            "Using remote Service B target %s for %s (%s)",
            service_address,
            condition.name,
            service_name,
        )
    else:
        logger.info("Running monolithic client-only condition %s", condition.name)

    parity_results = _validate_local_parity(config, condition, logger)

    runner = RemoteServiceBenchmarkRunner(config, args.config, args.output_dir)
    runner.parity_local_results = parity_results
    runner.run()

    runtime_meta = _read_runtime_metadata()
    if not runtime_meta:
        logger.warning(
            "Runtime metadata file %s was not present; deployment metadata will be best-effort only.",
            RUNTIME_METADATA_PATH,
        )
    deployment_metadata = _build_condition_deployment_metadata(config, condition, runtime_meta)

    artifact_logger = ArtifactLogger(runner.output_dir)
    artifact_logger.save_json("deployment_metadata.json", deployment_metadata)
    deployment_section = build_environment_deployment_section(deployment_metadata)
    if deployment_section:
        artifact_logger.update_environment({"deployment": deployment_section})

    logger.info("Benchmark artifacts directory: %s", os.path.abspath(runner.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
