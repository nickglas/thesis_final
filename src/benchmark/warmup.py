"""Warmup execution with empirical stabilisation check.

Section 5 of the design document specifies W = 50 warmup iterations
before each condition in each round, excluded from all summaries.

This module runs the full W warmup iterations and additionally
checks whether latency has stabilised by monitoring the coefficient
of variation (CV) over a trailing window.  The calibration result
is recorded as an artifact so the thesis can document whether the
chosen warmup count was sufficient.

The benchmark always runs at least W iterations.  If stabilisation
has not been reached by iteration W, a warning is logged but
execution continues (the configured count is treated as a minimum).
"""

import time
import math
import torch
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


def run_warmup(infer_fn: Callable[[torch.Tensor], None],
               input_tensor: torch.Tensor, n: int):
    """Run n warmup iterations using the provided inference function.

    All results are discarded.
    """
    for _ in range(n):
        infer_fn(input_tensor)


def run_warmup_calibrated(
    infer_fn: Callable[[torch.Tensor], None],
    input_tensor: torch.Tensor,
    n: int,
    window: int = 10,
    cv_threshold: float = 0.02,
) -> Dict[str, Any]:
    """Run warmup iterations with empirical stabilisation detection.

    Parameters
    ----------
    infer_fn : callable
        Warmup inference function (no return value needed).
    input_tensor : torch.Tensor
        Input to pass to infer_fn.
    n : int
        Configured number of warmup iterations (always run in full).
    window : int
        Trailing window size for CV computation.
    cv_threshold : float
        CV below this value indicates stabilisation.

    Returns
    -------
    dict
        Calibration metadata:
          total_iterations, stabilised (bool),
          stabilised_at_iteration (int or None),
          final_window_cv, cv_threshold, window_size,
          warmup_latencies_ms (list of all warmup timings).
    """
    latencies = []
    stabilised = False
    stabilised_at = None

    for i in range(n):
        t0 = time.perf_counter()
        infer_fn(input_tensor)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

        # Check stabilisation once we have enough data
        if not stabilised and len(latencies) >= window:
            tail = latencies[-window:]
            mean = sum(tail) / len(tail)
            if mean > 0:
                std = math.sqrt(sum((x - mean) ** 2 for x in tail) / len(tail))
                cv = std / mean
                if cv < cv_threshold:
                    stabilised = True
                    stabilised_at = i + 1

    # Final CV for the last window
    final_cv = None
    if len(latencies) >= window:
        tail = latencies[-window:]
        mean = sum(tail) / len(tail)
        if mean > 0:
            std = math.sqrt(sum((x - mean) ** 2 for x in tail) / len(tail))
            final_cv = std / mean

    if not stabilised:
        logger.warning(
            f"Warmup did not stabilise within {n} iterations "
            f"(CV={final_cv:.4f} > threshold={cv_threshold}). "
            f"Proceeding with configured warmup count."
        )

    return {
        "total_iterations": n,
        "stabilised": stabilised,
        "stabilised_at_iteration": stabilised_at,
        "final_window_cv": final_cv,
        "cv_threshold": cv_threshold,
        "window_size": window,
        "warmup_latencies_ms": [round(l, 4) for l in latencies],
    }
