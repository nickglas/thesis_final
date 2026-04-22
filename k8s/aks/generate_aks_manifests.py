"""Generate Kubernetes manifests for the RQ1.5 AKS deployment.

Produces Deployment + ClusterIP Service YAML for each service segment plus a
benchmark client pod manifest. The generator can now use an experiment config
YAML as the source of truth so the rendered manifests stay aligned with the
benchmark config and emitted artifacts.
"""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
AKS_DIR = SCRIPT_DIR
OUTPUT_DIR = os.path.join(AKS_DIR, "generated")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.config import format_k8s_service_name, load_config

CONDITIONS = {
    "monolithic_k8s_1svc": [],
    "chain_2svc": ["layer2"],
    "chain_3svc": ["layer1", "layer3"],
    "chain_4svc": ["layer1", "layer2", "layer3"],
    "chain_5svc": ["layer1", "layer2", "layer3", "layer4"],
}

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
}


def _svc_name(condition: str, index: int, cfg: dict) -> str:
    return format_k8s_service_name(cfg["service_name_template"], condition, index)


def _config_overrides(config_path: str) -> dict:
    experiment = load_config(config_path)
    if experiment.kubernetes is None:
        raise ValueError(f"Config has no kubernetes section: {config_path}")

    k8s = experiment.kubernetes
    threading = experiment.cpu_stabilisation.threading
    return {
        "service_name_template": k8s.service_name_template,
        "namespace": k8s.namespace,
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
    }


def _generate_service_yaml(condition: str, index: int, cfg: dict) -> str:
    name = _svc_name(condition, index, cfg)
    ns = cfg["namespace"]
    port = cfg["grpc_port"]
    exp = cfg["experiment_label"]
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: thesis-inference
    condition: {condition}
    segment-index: "{index}"
    experiment: {exp}
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


def _generate_deployment_yaml(
    condition: str,
    index: int,
    n_segments: int,
    split_points: list,
    cfg: dict,
) -> str:
    name = _svc_name(condition, index, cfg)
    ns = cfg["namespace"]
    image = cfg["image"]
    port = cfg["grpc_port"]
    pull_policy = cfg["image_pull_policy"]
    exp = cfg["experiment_label"]
    nodepool = cfg["nodepool"]

    args = [
        "--segment_index", str(index - 1),
        "--host", "0.0.0.0",
        "--port", str(port),
        "--max_message_bytes", str(cfg["max_message_bytes"]),
    ]
    if split_points:
        args += ["--split_points"] + split_points
    if index < n_segments:
        next_name = _svc_name(condition, index + 1, cfg)
        next_addr = f"{next_name}.{ns}.svc.cluster.local:{port}"
        args += ["--next_address", next_addr]

    args_yaml = "\n".join(f'            - "{arg}"' for arg in args)
    exp_cond = condition

    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: thesis-inference
    condition: {condition}
    segment-index: "{index}"
    experiment: {exp}
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
        experiment: {exp}
        experiment-condition: {exp_cond}
    spec:
      nodeSelector:
        agentpool: {nodepool}
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  experiment-condition: {exp_cond}
              topologyKey: "kubernetes.io/hostname"
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
              value: "{cfg['pytorch_intra_op_threads']}"
            - name: PYTORCH_INTER_OP_THREADS
              value: "{cfg['pytorch_inter_op_threads']}"
            - name: OMP_NUM_THREADS
              value: "{cfg['omp_num_threads']}"
            - name: MKL_NUM_THREADS
              value: "{cfg['mkl_num_threads']}"
            - name: OPENBLAS_NUM_THREADS
              value: "{cfg['openblas_num_threads']}"
          resources:
            requests:
              cpu: "{cfg['cpu_request']}"
              memory: "{cfg['memory_request']}"
            limits:
              cpu: "{cfg['cpu_limit']}"
              memory: "{cfg['memory_limit']}"
          readinessProbe:
            tcpSocket:
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 6
"""


def _generate_client_pod_yaml(cfg: dict) -> str:
    return f"""# Generated benchmark client pod.
# Regenerate from the experiment config before applying.
apiVersion: v1
kind: Pod
metadata:
  name: benchmark-client
  namespace: {cfg['namespace']}
  labels:
    app: thesis-inference
    role: client
    experiment: {cfg['experiment_label']}
spec:
  restartPolicy: Never
  containers:
    - name: client
      image: "{cfg['image']}"
      imagePullPolicy: {cfg['image_pull_policy']}
      command: ["sleep", "infinity"]
      env:
        - name: PYTORCH_INTRA_OP_THREADS
          value: "{cfg['pytorch_intra_op_threads']}"
        - name: PYTORCH_INTER_OP_THREADS
          value: "{cfg['pytorch_inter_op_threads']}"
        - name: OMP_NUM_THREADS
          value: "{cfg['omp_num_threads']}"
        - name: MKL_NUM_THREADS
          value: "{cfg['mkl_num_threads']}"
        - name: OPENBLAS_NUM_THREADS
          value: "{cfg['openblas_num_threads']}"
        - name: MY_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: MY_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: MY_POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
      resources:
        requests:
          cpu: "{cfg['client_cpu_request']}"
          memory: "{cfg['client_memory_request']}"
        limits:
          cpu: "{cfg['client_cpu_limit']}"
          memory: "{cfg['client_memory_limit']}"
"""


def _generate_namespace_yaml(namespace: str) -> str:
    return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
  labels:
    experiment: rq15
"""


def generate_condition(condition: str, split_points: list, cfg: dict) -> str:
    n_segments = len(split_points) + 1
    docs = []
    for idx in range(1, n_segments + 1):
        docs.append(_generate_service_yaml(condition, idx, cfg))
        docs.append(_generate_deployment_yaml(condition, idx, n_segments, split_points, cfg))
    return "---\n".join(docs)


def write_all(cfg: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ns_path = os.path.join(OUTPUT_DIR, "00_namespace.yaml")
    with open(ns_path, "w") as handle:
        handle.write(_generate_namespace_yaml(cfg["namespace"]))
    print(f"Generated: {ns_path}")

    for condition, split_points in CONDITIONS.items():
        n_segments = len(split_points) + 1
        out_path = os.path.join(OUTPUT_DIR, f"{condition}.yaml")
        with open(out_path, "w") as handle:
            handle.write(generate_condition(condition, split_points, cfg))
        print(f"Generated: {out_path} ({n_segments} services)")

    client_path = os.path.join(OUTPUT_DIR, "99_benchmark_client.yaml")
    with open(client_path, "w") as handle:
        handle.write(_generate_client_pod_yaml(cfg))
    print(f"Generated: {client_path}")

    print(f"\nAll manifests written to {OUTPUT_DIR}\nApply with: kubectl apply -f {OUTPUT_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Generate AKS manifests for RQ1.5 conditions")
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Experiment config YAML. When provided, image, service resources, "
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
    if args.config:
        try:
            cfg.update(_config_overrides(args.config))
        except ValueError as exc:
            parser.error(str(exc))

    cfg.update({
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
    })

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
    print()

    write_all(cfg)


if __name__ == "__main__":
    main()
