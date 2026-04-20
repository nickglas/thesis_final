"""Local Kubernetes smoke test for RQ1.4 chain experiments.

This script automates the full local K8s validation path:

  1. Generate manifests for a small smoke subset from the experiment config
  2. Create namespace and apply manifests
  3. Wait for the expected pods to exist and become Ready
  4. Port-forward to the first service and wait for localhost gRPC readiness
  5. Run parity and timing checks
  6. Tear down all resources

Kubernetes readiness is only TCP-level at the pod manifest layer. Actual
serving readiness for the smoke path is validated here by gRPC reachability
after port-forward and by parity/timing checks against the live service.
"""

import argparse
import json
import os
import subprocess
import sys
import time

import grpc

# Add project root to path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.config import format_k8s_service_name, load_config


DEFAULT_NAMESPACE = "rq14-smoke"
DEFAULT_CONFIG_PATH = "configs/rq1/1.4/rq1_4_smoke_test.yaml"
SMOKE_CONDITION_NAMES = [
    "monolithic_k8s_1svc",
    "chain_3svc",
]
LOCAL_PORT = 50061  # port-forward target on localhost


def run_cmd(args, check=True, capture=False):
    """Run a subprocess, optionally capturing output."""
    print(f"  $ {' '.join(args)}")
    if capture:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout.strip()
    subprocess.run(args, check=check)
    return None


def kubectl(*args, check=True, capture=False):
    return run_cmd(["kubectl"] + list(args), check=check, capture=capture)


def wait_for_pods_ready(namespace, label_selector, expected_count, timeout=120):
    """Wait until the expected matching pods exist and are Ready."""
    print(
        f"  Waiting for pods: {label_selector} "
        f"(expected={expected_count}, timeout={timeout}s)"
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        output = kubectl(
            "get", "pods", "-n", namespace,
            "-l", label_selector,
            "-o", "json",
            capture=True, check=False,
        )
        if output:
            payload = json.loads(output)
            items = payload.get("items", [])
            if len(items) != expected_count:
                time.sleep(3)
                continue

            all_ready = True
            for item in items:
                ready = False
                for condition in item.get("status", {}).get("conditions", []):
                    if condition.get("type") == "Ready":
                        ready = condition.get("status") == "True"
                        break
                if not ready:
                    all_ready = False
                    break

            if all_ready:
                print(f"  All pods ready ({len(items)} pods)")
                return
        time.sleep(3)

    raise RuntimeError(
        f"Pods not ready after {timeout}s: {label_selector} "
        f"(expected {expected_count})"
    )


def wait_for_grpc_ready(address, timeout=1.0):
    """Wait for a gRPC address to become reachable."""
    channel = grpc.insecure_channel(address)
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout)
    finally:
        channel.close()


def port_forward(namespace, service_name, local_port, remote_port, timeout=30.0):
    """Start kubectl port-forward and wait for localhost gRPC readiness."""
    target = f"svc/{service_name}"
    cmd = [
        "kubectl", "port-forward", "-n", namespace,
        target, f"{local_port}:{remote_port}",
    ]
    print(f"  $ {' '.join(cmd)} &")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.time() + timeout
    address = f"localhost:{local_port}"
    while time.time() < deadline:
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode()
            raise RuntimeError(f"Port-forward failed: {stderr}")
        try:
            wait_for_grpc_ready(address, timeout=1.0)
            return proc
        except grpc.FutureTimeoutError:
            time.sleep(1)

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    raise RuntimeError(
        f"Port-forward did not expose a ready gRPC endpoint within {timeout}s"
    )


def stop_port_forward(proc):
    """Terminate a kubectl port-forward process cleanly."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def resolve_service_name(condition_name, k8s_config, index):
    """Resolve a service name via the shared config template."""
    return format_k8s_service_name(
        k8s_config.service_name_template,
        condition_name,
        index,
    )


def validate_chain(address, split_points, condition_name, max_message_bytes):
    """Send a test inference through a deployed chain and validate parity."""
    import numpy as np
    import torch

    from proto import inference_pb2, inference_pb2_grpc
    from src.client.chain_client import ChainClient
    from src.models.resnet_splits import get_full_model

    print(f"\n  Validating condition: {condition_name}")
    print(f"    Address: {address}")
    print(f"    Split points: {split_points or '(monolithic)'}")

    model = get_full_model()

    torch.manual_seed(42)
    inp = torch.randn(1, 3, 224, 224)

    with torch.no_grad():
        expected = model(inp)

    client = ChainClient(address, max_message_bytes=max_message_bytes)
    metrics = client.infer(inp)
    client.close()

    channel = grpc.insecure_channel(
        address,
        options=[
            ("grpc.max_send_message_length", max_message_bytes),
            ("grpc.max_receive_message_length", max_message_bytes),
        ],
    )
    try:
        stub = inference_pb2_grpc.InferenceServiceStub(channel)
        req = inference_pb2.InferRequest(
            tensor_data=inp.contiguous().numpy().tobytes(),
            shape=list(inp.shape),
        )
        resp = stub.Infer(req)
    finally:
        channel.close()

    out_arr = np.frombuffer(resp.tensor_data, dtype=np.float32).copy()
    out_tensor = torch.from_numpy(out_arr.reshape(list(resp.shape)))

    max_diff = (expected - out_tensor).abs().max().item()
    n_hops = metrics["num_hops"]
    n_services = metrics["num_services"]

    print(f"    max_abs_diff: {max_diff:.2e}")
    print(f"    num_services: {n_services}")
    print(f"    num_hops: {n_hops}")
    print(f"    end_to_end_ms: {metrics['end_to_end_ms']:.2f}")
    print(f"    total_compute_ms: {metrics['total_compute_ms']:.2f}")
    print(f"    non_compute_overhead_ms: {metrics['non_compute_overhead_ms']:.2f}")
    print(f"    total_activation_bytes: {metrics['total_activation_bytes']}")

    for hop in metrics["hop_timings"]:
        print(
            f"    hop_{hop['hop_index']}: "
            f"compute={hop['compute_ms']:.2f}ms "
            f"fwd={hop['forward_ms']:.2f}ms "
            f"act={hop['activation_bytes']}B"
        )

    if max_diff > 1e-5:
        print(f"  FAIL: parity check (max_diff={max_diff:.2e} > 1e-5)")
        return False

    expected_services = len(split_points) + 1
    if n_services != expected_services:
        print(f"  FAIL: expected {expected_services} services, got {n_services}")
        return False

    print(f"  PASS: {condition_name}")
    return True


def cleanup(namespace):
    """Delete the smoke-test namespace and all its resources."""
    print(f"\nCleaning up namespace {namespace}...")
    kubectl(
        "delete", "namespace", namespace,
        "--ignore-not-found=true",
        "--wait=false",
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Local K8s smoke test for RQ1.4"
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Experiment config YAML used to source K8s settings",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Skip teardown for debugging",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Override namespace for this smoke run",
    )
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(PROJECT_ROOT, "k8s"))
    from generate_manifests import (
        build_overrides_from_config,
        configured_chain_conditions,
        generate_condition,
        generate_namespace_yaml,
    )

    config = load_config(args.config)
    if config.kubernetes is None:
        raise RuntimeError("Smoke test requires a config with a kubernetes section")

    k8s_config = config.kubernetes
    namespace = args.namespace or DEFAULT_NAMESPACE
    generator_overrides = build_overrides_from_config(config)
    generator_overrides["namespace"] = namespace

    chain_conditions = configured_chain_conditions(config)
    conditions_to_test = []
    for condition_name in SMOKE_CONDITION_NAMES:
        if condition_name not in chain_conditions:
            raise RuntimeError(
                f"Smoke condition '{condition_name}' missing from {args.config}"
            )
        conditions_to_test.append((condition_name, chain_conditions[condition_name]))

    grpc_port = k8s_config.grpc_port
    max_message_bytes = k8s_config.max_message_bytes

    print("=" * 60)
    print("RQ1.4 Local Kubernetes Smoke Test")
    print("=" * 60)
    print(f"Config: {args.config}")
    print(f"Namespace: {namespace}")

    pf_procs = []
    all_passed = True

    try:
        print("\n[1/5] Generating manifests...")
        generate_namespace_yaml(namespace)
        for condition_name, split_points in conditions_to_test:
            generate_condition(condition_name, split_points, generator_overrides)

        print("\n[2/5] Creating namespace...")
        gen_dir = os.path.join(PROJECT_ROOT, "k8s", "base", "generated")
        kubectl("apply", "-f", os.path.join(gen_dir, "namespace.yaml"))
        time.sleep(2)

        local_port = LOCAL_PORT
        for condition_name, split_points in conditions_to_test:
            print(f"\n[3/5] Deploying {condition_name}...")
            manifest_path = os.path.join(gen_dir, f"{condition_name}.yaml")
            kubectl("apply", "-f", manifest_path)

            expected_services = len(split_points) + 1
            wait_for_pods_ready(
                namespace,
                f"condition={condition_name}",
                expected_services,
                timeout=180,
            )

            print(f"\n[4/5] Port-forwarding {condition_name}...")
            service_name = resolve_service_name(condition_name, k8s_config, 1)
            pf = port_forward(namespace, service_name, local_port, grpc_port)
            pf_procs.append(pf)

            address = f"localhost:{local_port}"
            passed = validate_chain(
                address,
                split_points,
                condition_name,
                max_message_bytes=max_message_bytes,
            )
            if not passed:
                all_passed = False

            stop_port_forward(pf)
            pf_procs.remove(pf)
            local_port += 1

            print(f"  Cleaning up {condition_name}...")
            kubectl("delete", "-f", manifest_path, "--wait=true", check=False)
            time.sleep(2)

    except Exception as exc:
        print(f"\nERROR: {exc}")
        all_passed = False
    finally:
        for pf in pf_procs:
            stop_port_forward(pf)

        if not args.keep:
            cleanup(namespace)

    print("\n" + "=" * 60)
    if all_passed:
        print("SMOKE TEST: ALL PASSED")
    else:
        print("SMOKE TEST: FAILED")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
