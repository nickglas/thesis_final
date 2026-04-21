"""Generate Kubernetes manifests for RQ1.4 chain conditions.

Produces Deployment + ClusterIP Service YAML for each service segment
needed by a given chain configuration. All segments use the same
container image with different CLI arguments.

Usage:
    python k8s/generate_manifests.py --condition chain_3svc --split-points layer1 layer3
    python k8s/generate_manifests.py --condition monolithic_k8s_1svc
    python k8s/generate_manifests.py --all

Output goes to k8s/base/generated/.

Design alignment:
  - Service naming follows the config template: {condition}-svc-{index}
  - Thread settings are config-driven, not scattered literals
  - readinessProbe is TCP-level on the gRPC port only
  - End-to-end serving readiness is enforced at runtime by the benchmark
    runner's full-chain gRPC readiness checks and live parity validation
  - Portable for later AKS overlay (values flow from config/defaults)
"""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(SCRIPT_DIR, "base")
OUTPUT_DIR = os.path.join(BASE_DIR, "generated")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.config import (
    ExperimentConfig,
    format_k8s_service_name,
    load_config,
)

# Centralized defaults — single source of truth.
# Override at generation time via CLI args or the `overrides` dict.
DEFAULTS = {
    "namespace": "rq14",
    "image": "thesis-inference:latest",
    "grpc_port": 50051,
    "max_message_bytes": 16 * 1024 * 1024,
    "image_pull_policy": "IfNotPresent",
    # Thread settings (must match config.yaml cpu_stabilisation)
    "pytorch_intra_op_threads": 4,
    "pytorch_inter_op_threads": 1,
    "omp_num_threads": 4,
    "mkl_num_threads": 4,
    "openblas_num_threads": 4,
    # Service naming template (matches K8sConfig.service_name_template)
    "service_name_template": "{condition}-svc-{index}",
    # Pod resource requests/limits (Guaranteed QoS when requests == limits)
    "cpu_request": "4",
    "cpu_limit": "4",
    "memory_request": "1Gi",
    "memory_limit": "1Gi",
}

# All RQ1.4 conditions
CONDITIONS = {
    "monolithic_k8s_1svc": [],
    "chain_2svc": ["layer2"],
    "chain_3svc": ["layer1", "layer3"],
    "chain_4svc": ["layer1", "layer2", "layer3"],
    "chain_5svc": ["layer1", "layer2", "layer3", "layer4"],
}


def _service_name(condition: str, index: int, template: str = None) -> str:
    """Canonical service name from the config-driven template."""
    tmpl = template or DEFAULTS["service_name_template"]
    return format_k8s_service_name(tmpl, condition, index)


def build_overrides_from_config(config: ExperimentConfig) -> dict:
    """Map experiment config values into manifest-generation overrides."""
    overrides = {}

    if config.kubernetes is not None:
        overrides.update({
            "namespace": config.kubernetes.namespace,
            "service_name_template": config.kubernetes.service_name_template,
            "grpc_port": config.kubernetes.grpc_port,
            "max_message_bytes": config.kubernetes.max_message_bytes,
            "image": config.kubernetes.image,
            "image_pull_policy": config.kubernetes.image_pull_policy,
            "cpu_request": config.kubernetes.resources.cpu_request,
            "cpu_limit": config.kubernetes.resources.cpu_limit,
            "memory_request": config.kubernetes.resources.memory_request,
            "memory_limit": config.kubernetes.resources.memory_limit,
        })

    threading = config.cpu_stabilisation.threading
    overrides.update({
        "pytorch_intra_op_threads": threading.pytorch_intra_op,
        "pytorch_inter_op_threads": threading.pytorch_inter_op,
        "omp_num_threads": threading.omp_num_threads,
        "mkl_num_threads": threading.mkl_num_threads,
      "openblas_num_threads": threading.openblas_num_threads,
    })

    return overrides


def configured_chain_conditions(config: ExperimentConfig) -> dict:
    """Return chain conditions from an experiment config as name->split_points."""
    return {
        condition.name: (condition.chain_split_points or [])
        for condition in config.conditions
        if condition.type == "chain"
    }


def _generate_service_yaml(condition: str, index: int, cfg: dict) -> str:
    name = _service_name(condition, index, cfg.get("service_name_template"))
    ns = cfg["namespace"]
    port = cfg["grpc_port"]
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: thesis-inference
    condition: {condition}
    segment-index: "{index}"
spec:
  type: ClusterIP
  selector:
    app: thesis-inference
    condition: {condition}
    segment-index: "{index}"
  ports:
    - name: grpc
      port: {port}
      targetPort: {port}
      protocol: TCP
"""


def _generate_deployment_yaml(condition: str, index: int, n_segments: int,
                              split_points: list, cfg: dict) -> str:
    name = _service_name(condition, index, cfg.get("service_name_template"))
    ns = cfg["namespace"]
    image = cfg["image"]
    port = cfg["grpc_port"]
    pull_policy = cfg["image_pull_policy"]

    # Build container args
    args = [
        "--segment_index", str(index - 1),  # 0-based for the service
        "--host", "0.0.0.0",
        "--port", str(port),
        "--max_message_bytes", str(cfg["max_message_bytes"]),
    ]
    if split_points:
        args += ["--split_points"] + split_points

    # Next-hop address (if not last segment)
    if index < n_segments:
        next_name = _service_name(
            condition, index + 1, cfg.get("service_name_template")
        )
        next_addr = f"{next_name}.{ns}.svc.cluster.local:{port}"
        args += ["--next_address", next_addr]

    args_yaml = "\n".join(f'            - "{a}"' for a in args)

    # Thread env vars from config-driven defaults
    intra = cfg.get("pytorch_intra_op_threads", DEFAULTS["pytorch_intra_op_threads"])
    inter = cfg.get("pytorch_inter_op_threads", DEFAULTS["pytorch_inter_op_threads"])
    omp = cfg.get("omp_num_threads", DEFAULTS["omp_num_threads"])
    mkl = cfg.get("mkl_num_threads", DEFAULTS["mkl_num_threads"])
    openblas = cfg.get("openblas_num_threads", DEFAULTS["openblas_num_threads"])

    # Resource requests/limits from config-driven values
    cpu_req = cfg.get("cpu_request", DEFAULTS["cpu_request"])
    cpu_lim = cfg.get("cpu_limit", DEFAULTS["cpu_limit"])
    mem_req = cfg.get("memory_request", DEFAULTS["memory_request"])
    mem_lim = cfg.get("memory_limit", DEFAULTS["memory_limit"])

    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: thesis-inference
    condition: {condition}
    segment-index: "{index}"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: thesis-inference
      condition: {condition}
      segment-index: "{index}"
  template:
    metadata:
      labels:
        app: thesis-inference
        condition: {condition}
        segment-index: "{index}"
    spec:
      containers:
        - name: inference
          image: {image}
          imagePullPolicy: {pull_policy}
          ports:
            - containerPort: {port}
              name: grpc
          args:
{args_yaml}
          env:
            - name: PYTORCH_INTRA_OP_THREADS
              value: "{intra}"
            - name: PYTORCH_INTER_OP_THREADS
              value: "{inter}"
            - name: OMP_NUM_THREADS
              value: "{omp}"
            - name: MKL_NUM_THREADS
              value: "{mkl}"
            - name: OPENBLAS_NUM_THREADS
              value: "{openblas}"
          resources:
            requests:
              cpu: "{cpu_req}"
              memory: "{mem_req}"
            limits:
              cpu: "{cpu_lim}"
              memory: "{mem_lim}"
          securityContext:
            capabilities:
              add:
                - SYS_NICE
          readinessProbe:
            tcpSocket:
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 6
"""


def generate_condition(condition: str, split_points: list,
                       overrides: dict = None):
    """Generate all manifests for a single condition."""
    cfg = {**DEFAULTS, **(overrides or {})}
    n_segments = len(split_points) + 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    manifests = []
    for idx in range(1, n_segments + 1):
        svc_yaml = _generate_service_yaml(condition, idx, cfg)
        dep_yaml = _generate_deployment_yaml(
            condition, idx, n_segments, split_points, cfg,
        )
        manifests.append(svc_yaml)
        manifests.append(dep_yaml)

    # Write combined manifest
    out_path = os.path.join(OUTPUT_DIR, f"{condition}.yaml")
    with open(out_path, "w") as f:
        f.write("---\n".join(manifests))
    print(f"Generated: {out_path} ({n_segments} services)")
    return out_path


def generate_namespace_yaml(namespace: str):
    """Generate namespace manifest."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "namespace.yaml")
    with open(out_path, "w") as f:
        f.write(f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
""")
    print(f"Generated: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate K8s manifests for RQ1.4 conditions"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional experiment config YAML to source shared K8s values from",
    )
    parser.add_argument("--condition", choices=list(CONDITIONS.keys()),
                        help="Generate manifests for a specific condition")
    parser.add_argument("--split-points", nargs="*", default=None,
                        help="Override split points (for custom conditions)")
    parser.add_argument("--all", action="store_true",
                        help="Generate manifests for all RQ1.4 conditions")
    parser.add_argument("--namespace", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--image-pull-policy", default=None)
    args = parser.parse_args()

    config = load_config(args.config) if args.config else None
    configured_conditions = (
        configured_chain_conditions(config) if config else CONDITIONS
    )

    overrides = build_overrides_from_config(config) if config else {}
    cli_overrides = {
        key: value for key, value in {
            "namespace": args.namespace,
            "image": args.image,
            "image_pull_policy": args.image_pull_policy,
        }.items()
        if value is not None
    }
    overrides.update(cli_overrides)

    if args.all:
        namespace = overrides.get("namespace", DEFAULTS["namespace"])
        generate_namespace_yaml(namespace)
        for cond, splits in configured_conditions.items():
            generate_condition(cond, splits, overrides)
    elif args.condition:
        if args.split_points is not None:
            splits = args.split_points
        elif args.condition in configured_conditions:
            splits = configured_conditions[args.condition]
        else:
            splits = CONDITIONS[args.condition]
        namespace = overrides.get("namespace", DEFAULTS["namespace"])
        generate_namespace_yaml(namespace)
        generate_condition(args.condition, splits, overrides)
    else:
        parser.error("Specify --condition or --all")


if __name__ == "__main__":
    main()
