"""Warmup execution with empirical stabilisation check.

Section 5 of the design document specifies W = 50 warmup iterations
before each condition in each round, excluded from all summaries.

This module runs at least W warmup iterations and additionally checks whether
latency has stabilised by monitoring the coefficient of variation (CV) over a
trailing window. The calibration result records both the first time a stable
window is observed and whether the final trailing window also remains stable,
so the artifact is auditable without relying on a single ambiguous boolean.

The benchmark always runs at least W iterations. If extra warmup iterations
are configured, execution continues until the current trailing window is
stable or the extra-iteration budget is exhausted. With no extra budget, the
runner proceeds after W and records that the final warmup window was unstable.
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
    max_extra_iterations: int = -1,
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
    max_extra_iterations : int
        Additional iterations allowed beyond n while the current trailing
        window remains unstable. The configured n remains the minimum warmup
        count. A negative value means "adaptive until stable", guarded by an
        internal safety cap.

    Returns
    -------
    dict
        Calibration metadata:
          configured_iterations, total_iterations, stabilised (legacy bool),
          stabilised_once (bool), first_stabilised_at_iteration (int or None),
          final_window_stabilised (bool or None), stop_reason,
          stabilised_at_iteration (legacy alias),
          extra_iterations_used, max_extra_iterations,
          requested_max_extra_iterations, effective_max_extra_iterations,
          adaptive_until_stable, unbounded_extra_iterations,
          final_window_cv, cv_threshold, window_size,
          warmup_latencies_ms (list of all warmup timings).
    """
    _UNLIMITED_WARMUP_CAP = 10_000
    latencies = []
    stabilised = False
    stabilised_at = None
    stop_reason = "iteration_limit_reached"
    requested_max_extra_iterations = max_extra_iterations

    if max_extra_iterations < 0:
        unbounded_extra_iterations = True
        total_limit = n + _UNLIMITED_WARMUP_CAP
        effective_max_extra_iterations = _UNLIMITED_WARMUP_CAP
    else:
        unbounded_extra_iterations = False
        effective_max_extra_iterations = max(0, max_extra_iterations)
        total_limit = n + effective_max_extra_iterations

    adaptive_until_stable = effective_max_extra_iterations > 0

    def trailing_cv() -> float | None:
        if len(latencies) < window:
            return None
        tail = latencies[-window:]
        mean = sum(tail) / len(tail)
        if mean <= 0:
            return None
        std = math.sqrt(sum((x - mean) ** 2 for x in tail) / len(tail))
        return std / mean

    for i in range(total_limit):
        t0 = time.perf_counter()
        infer_fn(input_tensor)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

        cv = trailing_cv()
        current_window_stabilised = cv is not None and cv < cv_threshold

        if not stabilised and current_window_stabilised:
            stabilised = True
            stabilised_at = i + 1

        if (i + 1) < n:
            continue

        if current_window_stabilised:
            stop_reason = "current_window_stabilised"
            break

        if effective_max_extra_iterations == 0:
            stop_reason = "minimum_reached_no_extra_allowed"
            break

    # Final CV for the last window
    final_cv = trailing_cv()
    final_window_stabilised = None
    if final_cv is not None:
        final_window_stabilised = final_cv < cv_threshold

    if not final_window_stabilised:
        cv_text = f"{final_cv:.4f}" if final_cv is not None else "unavailable"
        logger.warning(
            f"Warmup final window did not stabilise within {len(latencies)} "
            f"iterations (CV={cv_text}, threshold={cv_threshold}, "
            f"stop_reason={stop_reason}). Proceeding after the available "
            "warmup budget."
        )

    return {
        "configured_iterations": n,
        "total_iterations": len(latencies),
        "stabilised": stabilised,
        "stabilised_once": stabilised,
        "first_stabilised_at_iteration": stabilised_at,
        "stabilised_at_iteration": stabilised_at,
        "final_window_stabilised": final_window_stabilised,
        "stop_reason": stop_reason,
        "extra_iterations_used": max(0, len(latencies) - n),
        "max_extra_iterations": requested_max_extra_iterations,
        "requested_max_extra_iterations": requested_max_extra_iterations,
        "effective_max_extra_iterations": effective_max_extra_iterations,
        "adaptive_until_stable": adaptive_until_stable,
        "unbounded_extra_iterations": unbounded_extra_iterations,
        "final_window_cv": final_cv,
        "cv_threshold": cv_threshold,
        "window_size": window,
        "warmup_latencies_ms": [round(l, 4) for l in latencies],
    }
