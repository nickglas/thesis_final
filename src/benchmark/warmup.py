"""Warmup execution for benchmark stabilization.

Section 5 of the design document specifies W = 50 warmup iterations
before each condition in each round, excluded from all summaries.
"""

import torch
from typing import Callable


def run_warmup(infer_fn: Callable[[torch.Tensor], None],
               input_tensor: torch.Tensor, n: int):
    """Run n warmup iterations using the provided inference function.

    All results are discarded.
    """
    for _ in range(n):
        infer_fn(input_tensor)
