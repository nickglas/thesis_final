"""Local smoke test: validates chain service behavior for RQ1.4.

Tests two configurations:
  1. Monolithic 1-service (empty split points) — verifies the monolithic K8s baseline path
  2. 3-service chain (split at layer1, layer3) — verifies multi-hop forwarding

Validates: output parity, metric semantics (forward_ms, num_hops,
total_activation_bytes), 1-indexed hop reporting.
"""

import os
import subprocess
import sys
import time
import torch
import numpy as np

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PYTHON = sys.executable
BASE_PORT = 50060


def start_chain(split_points, base_port):
    """Start chain services as subprocesses. Returns list of Popen objects."""
    n_segments = len(split_points) + 1
    procs = []
    for seg_idx in reversed(range(n_segments)):
        port = base_port + seg_idx
        cmd = [
            PYTHON, "-m", "src.services.chain_service_runner",
            "--segment_index", str(seg_idx),
            "--host", "127.0.0.1",
            "--port", str(port),
        ]
        if split_points:
            cmd += ["--split_points"] + split_points
        # else: omit --split_points entirely (defaults to empty list)
        if seg_idx < n_segments - 1:
            cmd += ["--next_address", f"127.0.0.1:{base_port + seg_idx + 1}"]

        print(f"  Starting segment {seg_idx} on port {port}...")
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        procs.insert(0, p)
        line = p.stdout.readline()
        assert "READY" in line, f"Segment {seg_idx} did not report READY: {line}"
        print(f"  Segment {seg_idx} READY")
    return procs


def stop_chain(procs):
    """Terminate all service processes."""
    for p in procs:
        p.terminate()
        p.wait()


def run_test(split_points, base_port, x, ref_output):
    """Run a single chain configuration test. Returns True on success."""
    n_segments = len(split_points) + 1
    label = f"{n_segments}-service" if split_points else "monolithic (1-service)"
    print(f"\n--- Testing {label}: split_points={split_points} ---")

    procs = start_chain(split_points, base_port)
    try:
        from src.client.chain_client import ChainClient

        client = ChainClient(f"127.0.0.1:{base_port}")
        client.warmup_infer(x)

        result = client.infer(x)

        # Display metrics
        print(f"  end_to_end_ms:          {result['end_to_end_ms']:.2f}")
        print(f"  total_compute_ms:       {result['total_compute_ms']:.2f}")
        print(f"  non_compute_overhead_ms:{result['non_compute_overhead_ms']:.2f}")
        print(f"  total_activation_bytes: {result['total_activation_bytes']}")
        print(f"  num_hops:               {result['num_hops']}")
        print(f"  num_services:           {result['num_services']}")
        for hop in result["hop_timings"]:
            print(
                f"    hop_{hop['hop_index']}: "
                f"compute={hop['compute_ms']:.2f}ms "
                f"deser={hop['deserialize_ms']:.2f}ms "
                f"ser={hop['serialize_ms']:.2f}ms "
                f"fwd={hop['forward_ms']:.2f}ms "
                f"bytes={hop['activation_bytes']}"
            )

        # --- Parity check ---
        from proto import inference_pb2
        resp = client.stub.Infer(
            inference_pb2.InferRequest(
                tensor_data=x.contiguous().numpy().tobytes(),
                shape=list(x.shape),
            )
        )
        out_arr = np.frombuffer(resp.tensor_data, dtype=np.float32).copy()
        chain_out = torch.from_numpy(out_arr.reshape(list(resp.shape)))
        diff = (ref_output - chain_out).abs().max().item()
        print(f"  Parity: max_diff={diff:.2e}, match={diff < 1e-5}")
        assert diff < 1e-5, f"Parity failed: max_diff={diff}"

        # --- Semantic assertions ---
        # num_services matches expected segment count
        assert result["num_services"] == n_segments, (
            f"Expected {n_segments} services, got {result['num_services']}"
        )

        # num_hops = boundaries crossed
        if n_segments == 1:
            expected_hops = 1  # monolithic: client→service boundary
        else:
            expected_hops = n_segments - 1  # inter-service boundaries
        assert result["num_hops"] == expected_hops, (
            f"Expected num_hops={expected_hops}, got {result['num_hops']}"
        )

        # hop indices are 1-indexed
        for i, hop in enumerate(result["hop_timings"]):
            assert hop["hop_index"] == i + 1, (
                f"Expected 1-indexed hop_index={i + 1}, got {hop['hop_index']}"
            )

        # forward_ms: 0 for last hop, >0 for non-terminal hops (in multi-service)
        last_hop = result["hop_timings"][-1]
        assert last_hop["forward_ms"] == 0.0, (
            f"Last hop forward_ms should be 0, got {last_hop['forward_ms']}"
        )
        if n_segments > 1:
            for hop in result["hop_timings"][:-1]:
                assert hop["forward_ms"] > 0, (
                    f"Non-terminal hop_{hop['hop_index']} forward_ms should be >0, "
                    f"got {hop['forward_ms']}"
                )

        # total_activation_bytes: sum of all hop activation bytes
        expected_total = sum(h["activation_bytes"] for h in result["hop_timings"])
        assert result["total_activation_bytes"] == expected_total, (
            f"total_activation_bytes mismatch: {result['total_activation_bytes']} "
            f"vs sum={expected_total}"
        )

        client.close()
        print(f"  {label} PASSED")
        return True

    finally:
        stop_chain(procs)


def main():
    from src.models.resnet_splits import get_full_model

    torch.manual_seed(42)
    x = torch.randn(1, 3, 224, 224)
    model = get_full_model()
    with torch.no_grad():
        ref = model(x)

    # Test 1: Monolithic (empty split points, 1 service)
    ok1 = run_test([], BASE_PORT, x, ref)

    # Test 2: 3-service chain (split at layer1, layer3)
    ok2 = run_test(["layer1", "layer3"], BASE_PORT + 10, x, ref)

    print("\n" + "=" * 50)
    if ok1 and ok2:
        print("ALL SMOKE TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
