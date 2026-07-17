"""Chain inference client: sends input to the first chain service, collects per-hop timing.

Timing boundaries:
  end_to_end_ms:            before request serialization → after response deserialization
  non_compute_overhead_ms:  end_to_end - sum(hop compute_ms)
  num_hops:                 number of gRPC boundaries crossed (= num_services - 1 for chain,
                            1 for monolithic K8s baseline)
  total_activation_bytes:   sum of activation bytes transferred across all boundaries
  per-hop detail:           from HopTiming messages propagated through the chain (1-indexed)
"""

import time
import numpy as np
import torch

from proto import inference_pb2
from src.grpc_target import ResolvedInferenceClient


class ChainClient:
    """Client that sends an input tensor to the first service in a chain."""

    def __init__(self, first_address: str,
                 max_message_bytes: int = 16 * 1024 * 1024):
        self.client = ResolvedInferenceClient(
            first_address,
            max_message_bytes=max_message_bytes,
        )

    def infer_response(self, input_tensor: torch.Tensor):
        """Run one RPC and return the raw gRPC response object."""
        request_bytes = input_tensor.contiguous().numpy().tobytes()
        request_shape = list(input_tensor.shape)
        request = inference_pb2.InferRequest(
            tensor_data=request_bytes,
            shape=request_shape,
        )
        return self.client.infer(request)

    def infer(self, input_tensor: torch.Tensor) -> dict:
        """Run chain inference with full timing instrumentation."""
        t_start = time.perf_counter()

        # Serialize input
        t_ser_start = time.perf_counter()
        request_bytes = input_tensor.contiguous().numpy().tobytes()
        request_shape = list(input_tensor.shape)
        request = inference_pb2.InferRequest(
            tensor_data=request_bytes,
            shape=request_shape,
        )
        t_ser_end = time.perf_counter()

        # gRPC call to first service in chain
        response = self.client.infer(request)

        # Deserialize final output
        t_deser_start = time.perf_counter()
        out_arr = np.frombuffer(response.tensor_data, dtype=np.float32).copy()
        _ = torch.from_numpy(out_arr.reshape(list(response.shape)))
        t_deser_end = time.perf_counter()

        t_end = time.perf_counter()

        end_to_end_ms = (t_end - t_start) * 1000

        # Extract per-hop timing (hop_index is 1-indexed from service)
        hop_timings = []
        total_compute_ms = 0.0
        total_activation_bytes = 0
        for ht in response.hop_timings:
            hop = {
                "hop_index": ht.hop_index,
                "deserialize_ms": ht.deserialize_ms,
                "compute_ms": ht.compute_ms,
                "serialize_ms": ht.serialize_ms,
                "forward_ms": ht.forward_ms,
                "activation_bytes": ht.activation_bytes,
            }
            hop_timings.append(hop)
            total_compute_ms += ht.compute_ms
            total_activation_bytes += ht.activation_bytes

        non_compute_overhead_ms = end_to_end_ms - total_compute_ms

        # num_hops = gRPC boundaries crossed = num_services - 1
        # For monolithic K8s (1 service): num_hops = 1 (client → service boundary)
        # For chain with N services: num_hops = N - 1 (inter-service boundaries)
        num_services = len(hop_timings)
        num_hops = max(num_services - 1, 1)

        return {
            "end_to_end_ms": end_to_end_ms,
            "total_compute_ms": total_compute_ms,
            "non_compute_overhead_ms": non_compute_overhead_ms,
            "total_activation_bytes": total_activation_bytes,
            "num_hops": num_hops,
            "num_services": num_services,
            "hop_timings": hop_timings,
            # Client-side diagnostics
            "client_serialize_ms": (t_ser_end - t_ser_start) * 1000,
            "client_deserialize_ms": (t_deser_end - t_deser_start) * 1000,
        }

    def warmup_infer(self, input_tensor: torch.Tensor):
        """Single warmup inference call (minimal instrumentation)."""
        self.infer_response(input_tensor)

    def close(self):
        self.client.close()
