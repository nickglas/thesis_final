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
    "client_namespace": None,
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
    "security_condition": "plain",
    "mesh_enabled": False,
    "mesh_implementation": None,
    "mesh_revision": None,
    "mesh_namespace": None,
    "mesh_service_accounts": {},
    "mesh_proxy_resources": {},
    "mesh_peer_authentication_enabled": False,
    "mesh_peer_authentication_namespace_mode": "PERMISSIVE",
    "mesh_peer_authentication_strict_workloads": [],
    "mesh_authorization_policy_enabled": False,
    "mesh_authorization_policy_name": "downstream-service1-only",
    "mesh_authorization_policy_downstream_segment_index": "2",
    "mesh_authorization_policy_source_segment_index": "1",
    "metadata_capture_mesh": False,
    "metadata_record_control_plane_placement": False,
    "resource_sampling_enabled": False,
    "rq2_manifest_labels": False,
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


def _load_raw_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Config did not parse as a YAML object: {config_path}")
    return payload


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_service_accounts(raw: dict) -> dict[str, str]:
    accounts: dict[str, str] = {}
    for key, value in (raw or {}).items():
        index = str(key).strip()
        account_name = str(value).strip()
        if index and account_name:
            accounts[index] = account_name
    return accounts


def _normalize_proxy_resources(raw: dict) -> dict[str, str]:
    resources: dict[str, str] = {}
    for key in ("cpu_request", "cpu_limit", "memory_request", "memory_limit"):
        value = (raw or {}).get(key)
        if value not in (None, ""):
            resources[key] = str(value)
    return resources


def _normalize_strict_workloads(raw: list | None) -> list[dict]:
    workloads = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        segment_index = item.get("segment_index")
        if segment_index in (None, ""):
            continue
        workloads.append({
            "name": str(item.get("name") or f"segment-{segment_index}-strict"),
            "segment_index": str(segment_index),
            "mode": str(item.get("mode") or "STRICT"),
        })
    return workloads


def _mesh_overrides(raw_k8s: dict, namespace: str) -> dict:
    mesh_raw = raw_k8s.get("mesh") or {}
    if not isinstance(mesh_raw, dict):
        raise ValueError("kubernetes.mesh must be a mapping when provided")

    peer_raw = mesh_raw.get("peer_authentication") or {}
    if not isinstance(peer_raw, dict):
        raise ValueError("kubernetes.mesh.peer_authentication must be a mapping when provided")

    authz_raw = mesh_raw.get("authorization_policy") or {}
    if not isinstance(authz_raw, dict):
        raise ValueError("kubernetes.mesh.authorization_policy must be a mapping when provided")

    metadata_raw = raw_k8s.get("metadata") or {}
    if not isinstance(metadata_raw, dict):
        raise ValueError("kubernetes.metadata must be a mapping when provided")

    sampling_raw = raw_k8s.get("resource_sampling") or {}
    if not isinstance(sampling_raw, dict):
        raise ValueError("kubernetes.resource_sampling must be a mapping when provided")

    mesh_enabled = _as_bool(mesh_raw.get("enabled"), False)
    mesh_namespace = str(mesh_raw.get("namespace") or namespace)
    mesh_revision = mesh_raw.get("revision")
    mesh_revision = str(mesh_revision).strip() if mesh_revision not in (None, "") else None
    implementation = mesh_raw.get("implementation")
    implementation = str(implementation).strip() if implementation not in (None, "") else None

    if mesh_enabled:
        if not mesh_revision:
            raise ValueError("kubernetes.mesh.revision is required when kubernetes.mesh.enabled is true")
        if mesh_namespace != namespace:
            raise ValueError(
                "kubernetes.mesh.namespace must match kubernetes.namespace for the current RQ2.1 renderer"
            )

    rq2_manifest_labels = any(
        key in raw_k8s
        for key in ("client_namespace", "security_condition", "mesh", "metadata", "resource_sampling")
    )
    return {
        "security_condition": str(raw_k8s.get("security_condition") or ("mtls" if mesh_enabled else "plain")),
        "client_namespace": str(raw_k8s.get("client_namespace") or namespace),
        "mesh_enabled": mesh_enabled,
        "mesh_implementation": implementation,
        "mesh_revision": mesh_revision,
        "mesh_namespace": mesh_namespace,
        "mesh_service_accounts": _normalize_service_accounts(mesh_raw.get("service_accounts") or {}),
        "mesh_proxy_resources": _normalize_proxy_resources(mesh_raw.get("proxy_resources") or {}),
        "mesh_peer_authentication_enabled": _as_bool(peer_raw.get("enabled"), mesh_enabled),
        "mesh_peer_authentication_namespace_mode": str(peer_raw.get("namespace_mode") or "PERMISSIVE"),
        "mesh_peer_authentication_strict_workloads": _normalize_strict_workloads(
            peer_raw.get("strict_workloads") or []
        ),
        "mesh_authorization_policy_enabled": _as_bool(authz_raw.get("enabled"), False),
        "mesh_authorization_policy_name": str(
            authz_raw.get("name") or DEFAULTS["mesh_authorization_policy_name"]
        ),
        "mesh_authorization_policy_downstream_segment_index": str(
            authz_raw.get("downstream_segment_index")
            or DEFAULTS["mesh_authorization_policy_downstream_segment_index"]
        ),
        "mesh_authorization_policy_source_segment_index": str(
            authz_raw.get("source_segment_index")
            or DEFAULTS["mesh_authorization_policy_source_segment_index"]
        ),
        "metadata_capture_mesh": _as_bool(metadata_raw.get("capture_mesh"), mesh_enabled),
        "metadata_record_control_plane_placement": _as_bool(
            metadata_raw.get("record_control_plane_placement"),
            mesh_enabled,
        ),
        "resource_sampling_enabled": _as_bool(sampling_raw.get("enabled"), False),
        "rq2_manifest_labels": rq2_manifest_labels,
    }


def _config_overrides(config_path: str) -> tuple[dict, list[dict]]:
    raw_config = _load_raw_config(config_path)
    raw_k8s = raw_config.get("kubernetes") or {}
    if not isinstance(raw_k8s, dict):
        raise ValueError(f"Config kubernetes section must be a mapping: {config_path}")

    experiment = load_config(config_path)
    if experiment.kubernetes is None:
        raise ValueError(f"Config has no kubernetes section: {config_path}")

    k8s = experiment.kubernetes
    threading = experiment.cpu_stabilisation.threading
    placement = k8s.placement
    overrides = {
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
    }
    overrides.update(_mesh_overrides(raw_k8s, k8s.namespace))
    return overrides, _condition_specs_from_experiment(experiment)


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


def _mesh_label_value(cfg: dict) -> str:
    return "true" if cfg.get("mesh_enabled") else "false"


def _common_labels(
    condition: str | None,
    cfg: dict,
    *,
    role: str,
    segment_index: int | None = None,
    include_experiment_condition: bool = True,
) -> dict[str, str]:
    labels = {
        "app": "thesis-inference",
        "experiment": str(cfg["experiment_label"]),
        "workload-role": role,
    }
    if cfg.get("rq2_manifest_labels"):
        labels["security-condition"] = str(cfg.get("security_condition") or "plain")
        labels["mesh-enabled"] = _mesh_label_value(cfg)
    if condition is not None:
        labels["condition"] = condition
        if include_experiment_condition:
            labels["experiment-condition"] = condition
    if segment_index is not None:
        labels["segment-index"] = str(segment_index)
    return labels


def _proxy_resource_annotations(cfg: dict) -> dict[str, str]:
    if not cfg.get("mesh_enabled"):
        return {}
    proxy = cfg.get("mesh_proxy_resources") or {}
    required = {
        "cpu_request": "sidecar.istio.io/proxyCPU",
        "cpu_limit": "sidecar.istio.io/proxyCPULimit",
        "memory_request": "sidecar.istio.io/proxyMemory",
        "memory_limit": "sidecar.istio.io/proxyMemoryLimit",
    }
    missing = [key for key in required if key not in proxy]
    if missing:
        raise ValueError(
            "kubernetes.mesh.proxy_resources is missing required keys when mesh is enabled: "
            + ", ".join(missing)
        )
    return {
        annotation: str(proxy[key])
        for key, annotation in required.items()
    }


def _service_account_name(condition: str, index: int, cfg: dict) -> str | None:
    accounts = cfg.get("mesh_service_accounts") or {}
    return accounts.get(str(index))


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
    labels = _common_labels(
        condition,
        cfg,
        role="service",
        segment_index=index,
        include_experiment_condition=False,
    )
    document = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": labels,
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
    service_account_name = _service_account_name(condition, index, cfg)
    if cfg.get("mesh_enabled") and not service_account_name:
        raise ValueError(
            f"Mesh-enabled condition {condition} is missing service account for segment {index}"
        )
    if service_account_name:
        pod_spec["serviceAccountName"] = service_account_name
    node_selector = _base_node_selector(cfg)
    if node_selector:
        pod_spec["nodeSelector"] = node_selector
    affinity = _service_affinity(condition_spec)
    if affinity:
        pod_spec["affinity"] = affinity

    deployment_labels = _common_labels(
        condition,
        cfg,
        role="service",
        segment_index=index,
        include_experiment_condition=False,
    )
    pod_labels = _common_labels(condition, cfg, role="service", segment_index=index)
    annotations = _proxy_resource_annotations(cfg)
    template_metadata = {"labels": pod_labels}
    if annotations:
        template_metadata["annotations"] = annotations

    document = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": deployment_labels,
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
                "metadata": template_metadata,
                "spec": pod_spec,
            },
        },
    }
    return _yaml_text(document)


def _generate_client_pod_yaml(cfg: dict, condition_spec: dict | None = None) -> str:
    labels = _common_labels(None, cfg, role="client")
    labels["role"] = "client"
    if cfg.get("rq2_manifest_labels"):
        labels["mesh-enabled"] = "false"
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
            "namespace": cfg["client_namespace"] or cfg["namespace"],
            "labels": labels,
        },
        "spec": pod_spec,
    }
    if cfg.get("mesh_enabled"):
        document["metadata"]["annotations"] = {"sidecar.istio.io/inject": "false"}
    header = [
        "# Generated benchmark client pod.",
        "# Regenerate from the experiment config before applying.",
    ]
    if condition_spec is not None:
        header.append(f"# Condition-specific placement manifest for {condition_spec['name']}.")
    return "\n".join(header) + "\n" + _yaml_text(document)


def _namespace_document(namespace: str, labels: dict[str, str]) -> dict:
    document = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": namespace,
            "labels": labels,
        },
    }
    return document


def _generate_namespaces_yaml(cfg: dict) -> str:
    service_namespace = str(cfg["namespace"])
    client_namespace = str(cfg.get("client_namespace") or service_namespace)
    experiment = str(cfg["experiment_label"])

    service_labels = {
        "experiment": experiment,
    }
    if cfg.get("rq2_manifest_labels"):
        service_labels.update({
            "workload-role": "inference",
            "security-condition": str(cfg.get("security_condition") or "plain"),
            "mesh-enabled": _mesh_label_value(cfg),
        })
    if cfg.get("mesh_enabled"):
        service_labels["istio.io/rev"] = str(cfg["mesh_revision"])

    docs = [_namespace_document(service_namespace, service_labels)]

    if client_namespace != service_namespace:
        client_labels = {
            "experiment": experiment,
        }
        if cfg.get("rq2_manifest_labels"):
            client_labels.update({
                "workload-role": "benchmark-client",
                "security-condition": str(cfg.get("security_condition") or "plain"),
                "mesh-enabled": "false",
            })
        docs.append(_namespace_document(client_namespace, client_labels))

    return "\n---\n".join(_yaml_text(document).rstrip() for document in docs) + "\n"


def _generate_service_accounts_yaml(condition_specs: list[dict], cfg: dict) -> str:
    if not cfg.get("mesh_enabled"):
        return ""

    docs = []
    for condition_spec in condition_specs:
        if condition_spec["type"] == "monolithic":
            continue
        condition = condition_spec["name"]
        n_segments = 1 if condition_spec["type"] == "split" else len(condition_spec["split_points"]) + 1
        for idx in range(1, n_segments + 1):
            account_name = _service_account_name(condition, idx, cfg)
            if not account_name:
                raise ValueError(
                    f"Mesh-enabled condition {condition} is missing service account for segment {idx}"
                )
            document = {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "name": account_name,
                    "namespace": cfg["namespace"],
                    "labels": _common_labels(condition, cfg, role="service-account", segment_index=idx),
                },
            }
            docs.append(document)

    return "\n---\n".join(_yaml_text(document).rstrip() for document in docs) + "\n" if docs else ""


def _peer_authentication_documents(condition_spec: dict, cfg: dict) -> list[dict]:
    if not (cfg.get("mesh_enabled") and cfg.get("mesh_peer_authentication_enabled")):
        return []

    namespace = cfg["namespace"]
    docs = [
        {
            "apiVersion": "security.istio.io/v1",
            "kind": "PeerAuthentication",
            "metadata": {
                "name": "default",
                "namespace": namespace,
                "labels": _common_labels(condition_spec["name"], cfg, role="mesh-policy"),
            },
            "spec": {
                "mtls": {
                    "mode": str(cfg.get("mesh_peer_authentication_namespace_mode") or "PERMISSIVE"),
                },
            },
        }
    ]

    for workload in cfg.get("mesh_peer_authentication_strict_workloads") or []:
        segment_index = str(workload["segment_index"])
        docs.append({
            "apiVersion": "security.istio.io/v1",
            "kind": "PeerAuthentication",
            "metadata": {
                "name": str(workload["name"]),
                "namespace": namespace,
                "labels": _common_labels(
                    condition_spec["name"],
                    cfg,
                    role="mesh-policy",
                    segment_index=int(segment_index),
                ),
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "condition": condition_spec["name"],
                        "segment-index": segment_index,
                        "workload-role": "service",
                    },
                },
                "mtls": {
                    "mode": str(workload.get("mode") or "STRICT"),
                },
            },
        })
    return docs


def _authorization_policy_documents(condition_spec: dict, cfg: dict) -> list[dict]:
    if not (cfg.get("mesh_enabled") and cfg.get("mesh_authorization_policy_enabled")):
        return []

    namespace = cfg["namespace"]
    downstream_segment = str(cfg.get("mesh_authorization_policy_downstream_segment_index") or "2")
    source_segment = str(cfg.get("mesh_authorization_policy_source_segment_index") or "1")
    source_service_account = (cfg.get("mesh_service_accounts") or {}).get(source_segment)
    if not source_service_account:
        raise ValueError(
            "kubernetes.mesh.authorization_policy requires a service account for "
            f"source_segment_index={source_segment}"
        )

    principal = f"cluster.local/ns/{namespace}/sa/{source_service_account}"
    return [
        {
            "apiVersion": "security.istio.io/v1",
            "kind": "AuthorizationPolicy",
            "metadata": {
                "name": str(cfg.get("mesh_authorization_policy_name") or "downstream-service1-only"),
                "namespace": namespace,
                "labels": _common_labels(
                    condition_spec["name"],
                    cfg,
                    role="mesh-policy",
                    segment_index=int(downstream_segment),
                ),
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "condition": condition_spec["name"],
                        "segment-index": downstream_segment,
                        "workload-role": "service",
                    },
                },
                "action": "ALLOW",
                "rules": [
                    {
                        "from": [
                            {
                                "source": {
                                    "principals": [principal],
                                },
                            }
                        ],
                    }
                ],
            },
        }
    ]


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
    for document in _peer_authentication_documents(condition_spec, cfg):
        docs.append(_yaml_text(document))
    for document in _authorization_policy_documents(condition_spec, cfg):
        docs.append(_yaml_text(document))
    return "---\n".join(docs)


def write_all(cfg: dict, condition_specs: list[dict], output_dir: str = OUTPUT_DIR) -> None:
    os.makedirs(output_dir, exist_ok=True)

    ns_path = os.path.join(output_dir, "00_namespace.yaml")
    with open(ns_path, "w", encoding="utf-8") as handle:
        handle.write(_generate_namespaces_yaml(cfg))
    print(f"Generated: {ns_path}")

    service_accounts_yaml = _generate_service_accounts_yaml(condition_specs, cfg)
    if service_accounts_yaml:
        service_accounts_path = os.path.join(output_dir, "01_service_accounts.yaml")
        with open(service_accounts_path, "w", encoding="utf-8") as handle:
            handle.write(service_accounts_yaml)
        print(f"Generated: {service_accounts_path}")

    for condition_spec in condition_specs:
        condition = condition_spec["name"]
        if condition_spec["type"] == "monolithic":
            descriptor = "client-only"
        elif condition_spec["type"] == "split":
            descriptor = "1 service"
        else:
            descriptor = f"{len(condition_spec['split_points']) + 1} services"
        out_path = os.path.join(output_dir, f"{condition}.yaml")
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(generate_condition(condition_spec, cfg))
        print(f"Generated: {out_path} ({descriptor})")

    client_path = os.path.join(output_dir, "99_benchmark_client.yaml")
    with open(client_path, "w", encoding="utf-8") as handle:
        handle.write(_generate_client_pod_yaml(cfg))
    print(f"Generated: {client_path}")

    if str(cfg.get("placement_strategy") or "none") != "none":
        for condition_spec in condition_specs:
            client_condition_path = os.path.join(
                output_dir,
                _client_manifest_file_name(condition_spec["name"]),
            )
            with open(client_condition_path, "w", encoding="utf-8") as handle:
                handle.write(_generate_client_pod_yaml(cfg, condition_spec))
            print(f"Generated: {client_condition_path} (condition-specific client)")

    print(f"\nAll manifests written to {output_dir}\nApply with: kubectl apply -f {output_dir}/")


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
    parser.add_argument("--client-namespace", default=None, help="Benchmark client namespace override")
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
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Directory for generated manifests. Defaults to k8s/aks/generated.",
    )
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

    resolved_namespace = args.namespace or cfg["namespace"]
    resolved_client_namespace = (
        args.client_namespace
        or cfg.get("client_namespace")
        or resolved_namespace
    )
    cfg.update(
        {
            "image": args.acr_image or cfg["image"],
            "namespace": resolved_namespace,
            "client_namespace": resolved_client_namespace,
            "mesh_namespace": resolved_namespace if cfg.get("mesh_enabled") else cfg.get("mesh_namespace"),
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
            "experiment_label": sanitize_k8s_name_component(resolved_namespace),
        }
    )

    print("Generating AKS manifests:")
    if args.config:
        print(f"  config    : {args.config}")
    print(f"  namespace : {cfg['namespace']}")
    print(f"  client ns : {cfg['client_namespace']}")
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
    print(f"  security condition: {cfg['security_condition']}")
    print(f"  mesh enabled: {cfg['mesh_enabled']}")
    if cfg.get("mesh_enabled"):
        print(f"  mesh implementation: {cfg.get('mesh_implementation') or 'unspecified'}")
        print(f"  mesh revision: {cfg['mesh_revision']}")
        print(f"  proxy resources: {cfg['mesh_proxy_resources']}")
        print(f"  authorization policy enabled: {cfg['mesh_authorization_policy_enabled']}")
    print(f"  conditions: {len(condition_specs)}")
    print()

    write_all(cfg, condition_specs, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
