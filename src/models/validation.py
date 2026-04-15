"""Functional equivalence validation for split models.

Verifies that every configured split condition produces outputs numerically
equivalent to the monolithic ResNet-18 for a set of deterministic inputs.
This is a required precondition (Section 4 of the design document).

Two validation modes:
  1. Local:  PartA → PartB in-process (always run).
  2. gRPC:   PartA → gRPC → Service B → response (run when a live service
             is reachable, otherwise skipped with a recorded note).
"""

import time
import numpy as np
import torch
from typing import Dict, List, Optional

from src.models.resnet_splits import get_full_model, get_split_models, SPLIT_POINTS


def validate_equivalence(
    split_points: Optional[List[str]] = None,
    atol: float = 1e-5,
    num_inputs: int = 5,
    seed: int = 42,
) -> Dict[str, dict]:
    """Check split configurations against the monolithic model (local path).

    Parameters
    ----------
    split_points : list of str, optional
        Which split points to validate.  Defaults to all SPLIT_POINTS.
    atol : float
        Absolute tolerance for element-wise comparison.
    num_inputs : int
        Number of deterministic random inputs to check.
    seed : int
        RNG seed for reproducible validation inputs.

    Returns
    -------
    dict
        Keyed by split point.  Each value contains:
          match (bool), max_abs_diff (float), atol (float),
          num_inputs (int), method (str).
    """
    if split_points is None:
        split_points = list(SPLIT_POINTS)

    rng = np.random.RandomState(seed)
    model = get_full_model()

    results = {}
    for split_after in split_points:
        part_a, part_b = get_split_models(split_after)
        all_match = True
        max_diff = 0.0

        for _ in range(num_inputs):
            inp = torch.from_numpy(rng.randn(1, 3, 224, 224).astype(np.float32))
            with torch.no_grad():
                mono_out = model(inp)
                intermediate = part_a(inp)
                split_out = part_b(intermediate)

            diff = (mono_out - split_out).abs().max().item()
            max_diff = max(max_diff, diff)
            if diff > atol:
                all_match = False

        results[split_after] = {
            "match": all_match,
            "max_abs_diff": max_diff,
            "atol": atol,
            "num_inputs": num_inputs,
            "method": "local_partA_partB",
        }

    return results


def validate_equivalence_grpc(
    split_points: Optional[List[str]] = None,
    atol: float = 1e-5,
    num_inputs: int = 5,
    seed: int = 42,
    grpc_host: str = "127.0.0.1",
    grpc_port: int = 50051,
    grpc_max_message_bytes: int = 16 * 1024 * 1024,
) -> Dict[str, dict]:
    """Check split configurations through the actual gRPC round-trip.

    Requires Service B to be running for each split point.
    This is called from the runner between service start and warmup.

    Returns same structure as validate_equivalence, with method='grpc_round_trip'.
    """
    from src.client.split_client import SplitClient

    if split_points is None:
        split_points = list(SPLIT_POINTS)

    rng = np.random.RandomState(seed)
    model = get_full_model()

    results = {}
    for split_after in split_points:
        client = SplitClient(split_after, grpc_host, grpc_port, grpc_max_message_bytes)
        try:
            all_match = True
            max_diff = 0.0

            for _ in range(num_inputs):
                inp = torch.from_numpy(rng.randn(1, 3, 224, 224).astype(np.float32))
                with torch.no_grad():
                    mono_out = model(inp)

                # Full gRPC round-trip
                metrics = client.infer(inp)
                # Reconstruct output from the last infer call's raw response
                # We need to get the actual tensor back — use a dedicated method
                split_out = _infer_and_get_tensor(client, inp)

                diff = (mono_out - split_out).abs().max().item()
                max_diff = max(max_diff, diff)
                if diff > atol:
                    all_match = False

            results[split_after] = {
                "match": all_match,
                "max_abs_diff": max_diff,
                "atol": atol,
                "num_inputs": num_inputs,
                "method": "grpc_round_trip",
            }
        finally:
            client.close()

    return results


def _infer_and_get_tensor(client, input_tensor: torch.Tensor) -> torch.Tensor:
    """Run split inference through gRPC and return the output tensor."""
    from proto import inference_pb2
    import grpc

    with torch.no_grad():
        intermediate = client.part_a(input_tensor)

    request_bytes = intermediate.contiguous().numpy().tobytes()
    request_shape = list(intermediate.shape)
    request = inference_pb2.InferRequest(
        tensor_data=request_bytes,
        shape=request_shape,
    )
    response = client.stub.Infer(request)
    out_arr = np.frombuffer(response.tensor_data, dtype=np.float32).copy()
    return torch.from_numpy(out_arr.reshape(list(response.shape)))


if __name__ == "__main__":
    print("Validating functional equivalence of all split configurations...")
    results = validate_equivalence()
    all_ok = True
    for split, info in results.items():
        status = "PASS" if info["match"] else "FAIL"
        print(f"  {split}: {status}  (max_abs_diff = {info['max_abs_diff']:.2e})")
        if not info["match"]:
            all_ok = False
    if all_ok:
        print("All split configurations match the monolithic model.")
    else:
        print("ERROR: Some split configurations do NOT match.")
        raise SystemExit(1)
