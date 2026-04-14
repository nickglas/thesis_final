"""Functional equivalence validation for split models.

Verifies that every split configuration produces outputs numerically
equivalent to the monolithic ResNet-18 for a set of deterministic inputs.
This is a required precondition (Section 4 of the design document).
"""

import torch
import numpy as np
from src.models.resnet_splits import get_full_model, get_split_models, SPLIT_POINTS


def validate_equivalence(atol: float = 1e-5, num_inputs: int = 5, seed: int = 42) -> dict:
    """Check all split configurations against the monolithic model.

    Returns a dict keyed by split point with {match: bool, max_abs_diff: float}.
    """
    rng = np.random.RandomState(seed)
    model = get_full_model()

    results = {}
    for split_after in SPLIT_POINTS:
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
        }

    return results


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
