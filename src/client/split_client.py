"""Split inference client: runs PartA locally, calls Service B via gRPC.

Timing boundaries (Section 4):
  end-to-end:        before part_A(input) → after response deserialization
  service_a_compute: part_A forward pass only
  boundary_crossing: start of intermediate serialization → end of response deserialization
"""

import time
import numpy as np
import torch
import grpc

from proto import inference_pb2, inference_pb2_grpc
from src.models.resnet_splits import PartA, get_full_model


class SplitClient:

    def __init__(self, split_after: str, host: str = "127.0.0.1",
                 port: int = 50051, max_message_bytes: int = 16 * 1024 * 1024):
        model = get_full_model()
        self.part_a = PartA(model, split_after)
        self.part_a.eval()
        self.split_after = split_after

        self.channel = grpc.insecure_channel(
            f"{host}:{port}",
            options=[
                ("grpc.max_send_message_length", max_message_bytes),
                ("grpc.max_receive_message_length", max_message_bytes),
            ],
        )
        self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)

    def infer(self, input_tensor: torch.Tensor) -> dict:
        """Run split inference with full timing instrumentation per the measurement contract."""
        t_start = time.perf_counter()

        # Service A compute
        t_a_start = time.perf_counter()
        with torch.no_grad():
            intermediate = self.part_a(input_tensor)
        t_a_end = time.perf_counter()

        # --- Boundary crossing interval starts here ---
        t_boundary_start = time.perf_counter()

        # Serialize intermediate tensor
        t_ser_start = time.perf_counter()
        request_bytes = intermediate.contiguous().numpy().tobytes()
        request_shape = list(intermediate.shape)
        t_ser_end = time.perf_counter()

        # gRPC call
        request = inference_pb2.InferRequest(
            tensor_data=request_bytes,
            shape=request_shape,
        )
        response = self.stub.Infer(request)

        # Deserialize response
        t_deser_start = time.perf_counter()
        out_arr = np.frombuffer(response.tensor_data, dtype=np.float32).copy()
        _ = torch.from_numpy(out_arr.reshape(list(response.shape)))
        t_deser_end = time.perf_counter()

        t_boundary_end = time.perf_counter()
        # --- Boundary crossing interval ends here ---

        t_end = time.perf_counter()

        activation_bytes = len(request_bytes)

        return {
            "end_to_end_ms": (t_end - t_start) * 1000,
            "service_a_compute_ms": (t_a_end - t_a_start) * 1000,
            "service_b_compute_ms": response.compute_ms,
            "boundary_crossing_ms": (t_boundary_end - t_boundary_start) * 1000,
            "activation_bytes": activation_bytes,
            # Diagnostic
            "request_serialize_ms": (t_ser_end - t_ser_start) * 1000,
            "request_deserialize_ms": response.deserialize_ms,
            "response_serialize_ms": response.serialize_ms,
            "response_deserialize_ms": (t_deser_end - t_deser_start) * 1000,
        }

    def warmup_infer(self, input_tensor: torch.Tensor):
        """Single warmup inference call (minimal instrumentation)."""
        with torch.no_grad():
            intermediate = self.part_a(input_tensor)
        request_bytes = intermediate.contiguous().numpy().tobytes()
        request_shape = list(intermediate.shape)
        request = inference_pb2.InferRequest(
            tensor_data=request_bytes,
            shape=request_shape,
        )
        self.stub.Infer(request)

    def close(self):
        self.channel.close()
