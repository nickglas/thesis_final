"""gRPC Service B: receives intermediate tensor, runs PartB, returns output.

Designed to run as a separate OS process (real microservice boundary).
Prints 'READY' to stdout once the gRPC server is accepting connections.
"""

import time
import numpy as np
import torch
import grpc
from concurrent import futures

from proto import inference_pb2, inference_pb2_grpc
from src.models.resnet_splits import get_split_models


class InferenceServicer(inference_pb2_grpc.InferenceServiceServicer):

    def __init__(self, split_after: str):
        _, self.part_b = get_split_models(split_after)
        self.part_b.eval()

    def Infer(self, request, context):
        # Deserialize
        t0 = time.perf_counter()
        arr = np.frombuffer(request.tensor_data, dtype=np.float32).copy()
        tensor = torch.from_numpy(arr.reshape(list(request.shape)))
        t1 = time.perf_counter()

        # Compute
        with torch.no_grad():
            output = self.part_b(tensor)
        t2 = time.perf_counter()

        # Serialize
        out_bytes = output.contiguous().numpy().tobytes()
        out_shape = list(output.shape)
        t3 = time.perf_counter()

        return inference_pb2.InferResponse(
            tensor_data=out_bytes,
            shape=out_shape,
            deserialize_ms=(t1 - t0) * 1000,
            compute_ms=(t2 - t1) * 1000,
            serialize_ms=(t3 - t2) * 1000,
        )


def serve(split_after: str, host: str = "127.0.0.1", port: int = 50051,
          max_message_bytes: int = 16 * 1024 * 1024):
    """Start the gRPC server and block until termination."""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=1),
        options=[
            ("grpc.max_send_message_length", max_message_bytes),
            ("grpc.max_receive_message_length", max_message_bytes),
        ],
    )
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServicer(split_after), server
    )
    addr = f"{host}:{port}"
    server.add_insecure_port(addr)
    server.start()
    print("READY", flush=True)
    server.wait_for_termination()
