"""Monolithic inference client with timing instrumentation.

Timing boundary (Section 4):
  start = immediately before model(input)
  stop  = immediately after return
"""

import time
import torch
from src.models.resnet_splits import get_full_model


class MonolithicClient:

    def __init__(self):
        self.model = get_full_model()

    def infer(self, input_tensor: torch.Tensor) -> dict:
        """Run monolithic inference and return the measurement-contract metrics."""
        t_start = time.perf_counter()
        with torch.no_grad():
            output = self.model(input_tensor)
        t_end = time.perf_counter()

        return {
            "end_to_end_ms": (t_end - t_start) * 1000,
            "service_a_compute_ms": (t_end - t_start) * 1000,
            "service_b_compute_ms": 0.0,
            "boundary_crossing_ms": 0.0,
            "activation_bytes": 0,
            # Diagnostic (not applicable for monolithic)
            "request_serialize_ms": 0.0,
            "request_deserialize_ms": 0.0,
            "response_serialize_ms": 0.0,
            "response_deserialize_ms": 0.0,
        }

    def warmup_infer(self, input_tensor: torch.Tensor):
        """Single warmup inference call (no timing overhead)."""
        with torch.no_grad():
            self.model(input_tensor)
