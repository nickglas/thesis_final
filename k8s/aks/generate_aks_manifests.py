"""Generate Kubernetes manifests for AKS-backed RQ1.x experiments.

Produces Deployment + ClusterIP Service YAML for remote service segments plus a
benchmark client pod manifest. When a config YAML is provided, the conditions,
image, namespace, and resource settings are all taken from that config so the
rendered manifests stay aligned with the benchmark artifacts.
"""

from __future__ import annotations

import argparse
import os
import sys

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
AKS_DIR = SCRIPT_DIR
OUTPUT_DIR = os.path.join(AKS_DIR, "generated")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.config import (
    format_k8s_service_name,
    load_config,
    sanitize_k8s_name_component,
)

DEFAULT_CONDITIONS = [
    {"name": "monolithic_k8s_1svc", "type": "chain", "split_points": []},
    {"name": "chain_2svc", "type": "chain", "split_points": ["layer2"]},
    {"name": "chain_3svc", "type": "chain", "split_points": ["layer1", "layer3"]},
    {"name": "chain_4svc", "type": "chain", "split_points": ["layer1", "layer2", "layer3"]},
    {"name": "chain_5svc", "type": "chain", "split_points": ["layer1", "layer2", "layer3", "layer4"]},
]

DEFAULTS = {
    "service_name_template": "{condition}-svc-{index}",
    "namespace": "rq15",
    "nodepool": "rq15pool",
    "grpc_port": 50051,
    "max_message_bytes": 16 * 1024 * 1024,
    "image": "thesis-inference:latest",
    "cpu_request": "1",
    "cpu_limit": "1",
    "memory_request": "1Gi",
    "memory_limit": "1Gi",
    "client_cpu_request": "100m",
    "client_cpu_limit": "500m",
    "client_memory_request": "1Gi",
    "client_memory_limit": "1Gi",
    "pytorch_intra_op_threads": 1,
    "pytorch_inter_op_threads": 1,
    "omp_num_threads": 1,
    "mkl_num_threads": 1,
    "openblas_num_threads": 1,
    "image_pull_policy": "Always",
    "experiment_label": "rq15",
    "placement_strategy": "none",
    "placement_require_same_node": False,
    "placement_fail_if_not_colocated": False,
    "placement_node_selector": {},
}


def _svc_name(condition: str, index: int, cfg: dict) -> str:
    return format_k8s_service_name(cfg["service_name_template"], condition, index)


def _condition_specs_from_experiment(experiment) -> list[dict]:
    specs = []
    for cond in experiment.conditions:
        if cond.type == "chain":
            specs.append({
                "name": cond.name,
                "type": cond.type,
                "split_points": list(cond.chain_split_points or []),
            })
            continue
        if cond.type == "split":
            if not cond.split_after:
                raise ValueError(f"Split condition '{cond.name}' is missing split_after")
            specs.append({
                "name": cond.name,
                "type": cond.type,
                "split_after": cond.split_after,
                "split_points": [],
            })
            continue
        if cond.type == "monolithic":
            specs.append({
                "name": cond.name,
                "type": cond.type,
                "split_points": [],
            })
            continue
        raise ValueError(f"Unsupported condition type '{cond.type}' for {cond.name}")
    return specs


def _config_overrides(config_path: str) -> tuple[dict, list[dict]]:
    experiment = load_config(config_path)
    if experiment.kubernetes is None:
        raise ValueError(f"Config has no kubernetes section: {config_path}")

    k8s = experiment.kubernetes
    threading = experiment.cpu_stabilisation.threading
    placement = k8s.placement
    return {
        "service_name_template": k8s.service_name_template,
        "namespace": k8s.namespace,
        "nodepool": placement.node_pool or DEFAULTS["nodepool"],
        "grpc_port": k8s.grpc_port,
        "max_message_bytes": k8s.max_message_bytes,
        "image": k8s.image,
        "image_pull_policy": k8s.image_pull_policy,
        "cpu_request": k8s.resources.cpu_request,
        "cpu_limit": k8s.resources.cpu_limit,
        "memory_request": k8s.resources.memory_request,
        "memory_limit": k8s.resources.memory_limit,
        "client_cpu_request": k8s.client_resources.cpu_request,
        "client_cpu_limit": k8s.client_resources.cpu_limit,
        "client_memory_request": k8s.client_resources.memory_request,
        "client_memory_limit": k8s.client_resources.memory_limit,
        "pytorch_intra_op_threads": threading.pytorch_intra_op,
        "pytorch_inter_op_threads": threading.pytorch_inter_op,
        "omp_num_threads": threading.omp_num_threads,
        "mkl_num_threads": threading.mkl_num_threads,
        "openblas_num_threads": threading.openblas_num_threads,
        "experiment_label": sanitize_k8s_name_component(k8s.namespace),
        "placement_strategy": placement.strategy,
        "placement_require_same_node": placement.require_same_node,
        "placement_fail_if_not_colocated": placement.fail_if_not_colocated,
        "placement_node_selector": dict(placement.node_selector),
    }, _condition_specs_from_experiment(experiment)


def _yaml_text(document: dict) -> str:
    return yaml.safe_dump(document, sort_keys=False).rstrip() + "\n"


def _client_manifest_file_name(condition_name: str) -> str:
    return f"99_benchmark_client_{sanitize_k8s_name_component(condition_name)}.yaml"


def _base_node_selector(cfg: dict) -> dict[str, str]:
    selector: dict[str, str] = {}
    nodepool = str(cfg.get("nodepool") or "").strip()
    if nodepool:
        selector["agentpool"] = nodepool
    explicit_selector = cfg.get("placement_node_selector") or {}
    selector.update({str(key): str(value) for key, value in explicit_selector.items()})
    return selector


def _service_affinity(condition_spec: dict) -> dict | None:
    split_points = condition_spec["split_points"]
    n_segments = len(split_points) + 1
    if condition_spec["type"] != "chain" or n_segments <= 1:
        return None
    return {
        "podAffinity": {
            "requiredDuringSchedulingIgnoredDuringExecution": [
                {
                    "labelSelector": {
                        "matchLabels": {
                            "experiment-condition": condition_spec["name"],
                        }
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        }
    }


def _client_affinity(condition_spec: dict | None, cfg: dict) -> dict | None:
    if condition_spec is None or condition_spec["type"] != "split":
        return None

    strategy = str(cfg.get("placement_strategy") or "none")
    if strategy not in {"strict_same_node", "prefer_same_node"}:
        return None

    affinity_term = {
        "labelSelector": {
            "matchLabels": {
                "condition": condition_spec["name"],
                "segment-index": "1",
                "workload-role": "service",
            }
        },
        "topologyKey": "kubernetes.io/hostname",
    }
    if strategy == "strict_same_node":
        return {
            "podAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": [affinity_term]
            }
        }
    return {
        "podAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 100,
                    "podAffinityTerm": affinity_term,
                }
            ]
        }
    }


def _command_and_args(condition_spec: dict, index: int, cfg: dict) -> tuple[list[str] | None, list[str]]:
    if condition_spec["type"] == "split":
        return ["python", "-m", "src.services.service_b_runner"], [
            "--split_after", condition_spec["split_after"],
            "--host", "0.0.0.0",
            "--port", str(cfg["grpc_port"]),
            "--max_message_bytes", str(cfg["max_message_bytes"]),
        ]

    split_points = condition_spec["split_points"]
    n_segments = len(split_points) + 1
    args = [
        "--segment_index", str(index - 1),
        "--host", "0.0.0.0",
        "--port", str(cfg["grpc_port"]),
        "--max_message_bytes", str(cfg["max_message_bytes"]),
    ]
    if split_points:
        args += ["--split_points"] + split_points
    if index < n_segments:
        next_name = _svc_name(condition_spec["name"], index + 1, cfg)
        next_addr = f"{next_name}.{cfg['namespace']}.svc.cluster.local:{cfg['grpc_port']}"
        args += ["--next_address", next_addr]
    return None, args


def _generate_service_yaml(condition: str, index: int, cfg: dict) -> str:
    name = _svc_name(condition, index, cfg)
    ns = cfg["namespace"]
    port = cfg["grpc_port"]
    exp = cfg["experiment_label"]
    document = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": {
                "app": "thesis-inference",
                "condition": condition,
                "segment-index": str(index),
                "experiment": exp,
                "workload-role": "service",
            },
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {
                "app": "thesis-inference",
                "condition": condition,
                "segment-index": str(index),
            },
            "ports": [
                {
                    "name": "grpc",
                    "port": port,
                    "targetPort": port,
                    "protocol": "TCP",
                }
            ],
        },
    }
    return _yaml_text(document)


def _generate_deployment_yaml(condition_spec: dict, index: int, cfg: dict) -> str:
    condition = condition_spec["name"]
    name = _svc_name(condition, index, cfg)
    ns = cfg["namespace"]
    image = cfg["image"]
    port = cfg["grpc_port"]
    pull_policy = cfg["image_pull_policy"]
    exp = cfg["experiment_label"]

    command, args = _command_and_args(condition_spec, index, cfg)
    container = {
        "name": "inference",
        "image": image,
        "imagePullPolicy": pull_policy,
        "ports": [{"containerPort": port, "name": "grpc"}],
        "args": args,
        "env": [
            {"name": "PYTORCH_INTRA_OP_THREADS", "value": str(cfg["pytorch_intra_op_threads"])} ,
            {"name": "PYTORCH_INTER_OP_THREADS", "value": str(cfg["pytorch_inter_op_threads"])} ,
            {"name": "OMP_NUM_THREADS", "value": str(cfg["omp_num_threads"])} ,
            {"name": "MKL_NUM_THREADS", "value": str(cfg["mkl_num_threads"])} ,
            {"name": "OPENBLAS_NUM_THREADS", "value": str(cfg["openblas_num_threads"])} ,
        ],
        "resources": {
            "requests": {
                "cpu": str(cfg["cpu_request"]),
                "memory": str(cfg["memory_request"]),
            },
            "limits": {
                "cpu": str(cfg["cpu_limit"]),
                "memory": str(cfg["memory_limit"]),
            },
        },
        "readinessProbe": {
            "tcpSocket": {"port": port},
            "initialDelaySeconds": 5,
            "periodSeconds": 5,
            "failureThreshold": 6,
        },
    }
    if command is not None:
        container["command"] = command

    pod_spec = {"containers": [container]}
    node_selector = _base_node_selector(cfg)
    if node_selector:
        pod_spec["nodeSelector"] = node_selector
    affinity = _service_affinity(condition_spec)
    if affinity:
        pod_spec["affinity"] = affinity

    document = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": {
                "app": "thesis-inference",
                "condition": condition,
                "segment-index": str(index),
                "experiment": exp,
                "workload-role": "service",
            },
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "thesis-inference",
                    "condition": condition,
                    "segment-index": str(index),
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "thesis-inference",
                        "condition": condition,
                        "segment-index": str(index),
                        "experiment": exp,
                        "experiment-condition": condition,
                        "workload-role": "service",
                    }
                },
                "spec": pod_spec,
            },
        },
    }
    return _yaml_text(document)


def _generate_client_pod_yaml(cfg: dict, condition_spec: dict | None = None) -> str:
    labels = {
        "app": "thesis-inference",
        "role": "client",
        "workload-role": "client",
        "experiment": cfg["experiment_label"],
    }
    if condition_spec is not None:
        labels["condition"] = condition_spec["name"]
        labels["experiment-condition"] = condition_spec["name"]

    container = {
        "name": "client",
        "image": str(cfg["image"]),
        "imagePullPolicy": str(cfg["image_pull_policy"]),
        "command": ["sleep", "infinity"],
        "env": [
            {"name": "PYTORCH_INTRA_OP_THREADS", "value": str(cfg["pytorch_intra_op_threads"])} ,
            {"name": "PYTORCH_INTER_OP_THREADS", "value": str(cfg["pytorch_inter_op_threads"])} ,
            {"name": "OMP_NUM_THREADS", "value": str(cfg["omp_num_threads"])} ,
            {"name": "MKL_NUM_THREADS", "value": str(cfg["mkl_num_threads"])} ,
            {"name": "OPENBLAS_NUM_THREADS", "value": str(cfg["openblas_num_threads"])} ,
            {"name": "MY_POD_NAME", "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}}},
            {"name": "MY_NODE_NAME", "valueFrom": {"fieldRef": {"fieldPath": "spec.nodeName"}}},
            {"name": "MY_POD_IP", "valueFrom": {"fieldRef": {"fieldPath": "status.podIP"}}},
        ],
        "resources": {
            "requests": {
                "cpu": str(cfg["client_cpu_request"]),
                "memory": str(cfg["client_memory_request"]),
            },
            "limits": {
                "cpu": str(cfg["client_cpu_limit"]),
                "memory": str(cfg["client_memory_limit"]),
            },
        },
    }

    pod_spec = {
        "restartPolicy": "Never",
        "containers": [container],
    }
    node_selector = _base_node_selector(cfg)
    if node_selector:
        pod_spec["nodeSelector"] = node_selector
    affinity = _client_affinity(condition_spec, cfg)
    if affinity:
        pod_spec["affinity"] = affinity

    document = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "benchmark-client",
            "namespace": cfg["namespace"],
            "labels": labels,
        },
        "spec": pod_spec,
    }
    header = [
        "# Generated benchmark client pod.",
        "# Regenerate from the experiment config before applying.",
    ]
    if condition_spec is not None:
        header.append(f"# Condition-specific placement manifest for {condition_spec['name']}.")
    return "\n".join(header) + "\n" + _yaml_text(document)


def _generate_namespace_yaml(namespace: str) -> str:
    document = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": namespace,
            "labels": {
                "experiment": sanitize_k8s_name_component(namespace),
            },
        },
    }
    return _yaml_text(document)


def generate_condition(condition_spec: dict, cfg: dict) -> str:
    if condition_spec["type"] == "monolithic":
        return (
            f"# {condition_spec['name']} runs entirely inside the benchmark client pod.\n"
            "# No remote service manifests are required for this condition.\n"
        )

    condition = condition_spec["name"]
    split_points = condition_spec["split_points"]
    n_segments = 1 if condition_spec["type"] == "split" else len(split_points) + 1
    docs = []
    for idx in range(1, n_segments + 1):
        docs.append(_generate_service_yaml(condition, idx, cfg))
        docs.append(_generate_deployment_yaml(condition_spec, idx, cfg))
    return "---\n".join(docs)


def write_all(cfg: dict, condition_specs: list[dict]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ns_path = os.path.join(OUTPUT_DIR, "00_namespace.yaml")
    with open(ns_path, "w", encoding="utf-8") as handle:
        handle.write(_generate_namespace_yaml(cfg["namespace"]))
    print(f"Generated: {ns_path}")

    for condition_spec in condition_specs:
        condition = condition_spec["name"]
        if condition_spec["type"] == "monolithic":
            descriptor = "client-only"
        elif condition_spec["type"] == "split":
            descriptor = "1 service"
        else:
            descriptor = f"{len(condition_spec['split_points']) + 1} services"
        out_path = os.path.join(OUTPUT_DIR, f"{condition}.yaml")
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(generate_condition(condition_spec, cfg))
        print(f"Generated: {out_path} ({descriptor})")

    client_path = os.path.join(OUTPUT_DIR, "99_benchmark_client.yaml")
    with open(client_path, "w", encoding="utf-8") as handle:
        handle.write(_generate_client_pod_yaml(cfg))
    print(f"Generated: {client_path}")

    if str(cfg.get("placement_strategy") or "none") != "none":
        for condition_spec in condition_specs:
            client_condition_path = os.path.join(
                OUTPUT_DIR,
                _client_manifest_file_name(condition_spec["name"]),
            )
            with open(client_condition_path, "w", encoding="utf-8") as handle:
                handle.write(_generate_client_pod_yaml(cfg, condition_spec))
            print(f"Generated: {client_condition_path} (condition-specific client)")

    print(f"\nAll manifests written to {OUTPUT_DIR}\nApply with: kubectl apply -f {OUTPUT_DIR}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AKS manifests for config-driven RQ1.x conditions")
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Experiment config YAML. When provided, conditions, image, service resources, "
            "client resources, namespace, and thread settings are taken from the config."
        ),
    )
    parser.add_argument(
        "--acr-image",
        default=None,
        help=(
            "Full ACR image reference. Use a mutable tag for smoke tests or a pinned "
            "digest for the thesis run. Example: myacr.azurecr.io/thesis-inference@sha256:<digest>"
        ),
    )
    parser.add_argument("--namespace", default=None, help="Kubernetes namespace override")
    parser.add_argument("--nodepool", default=None, help="AKS node pool agentpool label override")
    parser.add_argument("--cpu", default=None, help="Set both service CPU request and limit")
    parser.add_argument("--cpu-request", default=None, dest="cpu_request", help="Service CPU request override")
    parser.add_argument("--cpu-limit", default=None, dest="cpu_limit", help="Service CPU limit override")
    parser.add_argument("--memory", default=None, help="Set both service memory request and limit")
    parser.add_argument("--memory-request", default=None, dest="memory_request", help="Service memory request override")
    parser.add_argument("--memory-limit", default=None, dest="memory_limit", help="Service memory limit override")
    parser.add_argument("--client-cpu-request", default=None, dest="client_cpu_request", help="Client CPU request override")
    parser.add_argument("--client-cpu-limit", default=None, dest="client_cpu_limit", help="Client CPU limit override")
    parser.add_argument("--client-memory-request", default=None, dest="client_memory_request", help="Client memory request override")
    parser.add_argument("--client-memory-limit", default=None, dest="client_memory_limit", help="Client memory limit override")
    parser.add_argument("--grpc-port", type=int, default=None, help="gRPC port override")
    args = parser.parse_args()

    if not args.config and not args.acr_image:
        parser.error("one of --config or --acr-image is required")

    cfg = dict(DEFAULTS)
    condition_specs = list(DEFAULT_CONDITIONS)
    if args.config:
        try:
            cfg_overrides, condition_specs = _config_overrides(args.config)
            cfg.update(cfg_overrides)
        except ValueError as exc:
            parser.error(str(exc))

    cfg.update(
        {
            "image": args.acr_image or cfg["image"],
            "namespace": args.namespace or cfg["namespace"],
            "nodepool": args.nodepool or cfg["nodepool"],
            "grpc_port": args.grpc_port or cfg["grpc_port"],
            "cpu_request": args.cpu_request or args.cpu or cfg["cpu_request"],
            "cpu_limit": args.cpu_limit or args.cpu_request or args.cpu or cfg["cpu_limit"],
            "memory_request": args.memory_request or args.memory or cfg["memory_request"],
            "memory_limit": args.memory_limit or args.memory_request or args.memory or cfg["memory_limit"],
            "client_cpu_request": args.client_cpu_request or cfg["client_cpu_request"],
            "client_cpu_limit": args.client_cpu_limit or args.client_cpu_request or cfg["client_cpu_limit"],
            "client_memory_request": args.client_memory_request or cfg["client_memory_request"],
            "client_memory_limit": args.client_memory_limit or args.client_memory_request or cfg["client_memory_limit"],
            "experiment_label": sanitize_k8s_name_component(args.namespace or cfg["namespace"]),
        }
    )

    print("Generating AKS manifests:")
    if args.config:
        print(f"  config    : {args.config}")
    print(f"  namespace : {cfg['namespace']}")
    print(f"  nodepool  : {cfg['nodepool']}")
    print(f"  image     : {cfg['image']}")
    print(f"  cpu_req   : {cfg['cpu_request']}")
    print(f"  cpu_limit : {cfg['cpu_limit']}")
    print(f"  mem_req   : {cfg['memory_request']}")
    print(f"  mem_limit : {cfg['memory_limit']}")
    print(f"  client_cpu_req   : {cfg['client_cpu_request']}")
    print(f"  client_cpu_limit : {cfg['client_cpu_limit']}")
    print(f"  client_mem_req   : {cfg['client_memory_request']}")
    print(f"  client_mem_limit : {cfg['client_memory_limit']}")
    print(f"  placement strategy: {cfg['placement_strategy']}")
    print(f"  conditions: {len(condition_specs)}")
    print()

    write_all(cfg, condition_specs)


if __name__ == "__main__":
    main()
