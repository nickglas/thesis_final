"""gRPC chain service: runs one ModelSegment, forwards to the next service.

Each instance in a chain handles a single segment of the ResNet-18 model.
Non-terminal services forward their output to the next service in the chain
and propagate HopTiming data back to the client.

Prints 'READY' to stdout once the gRPC server is accepting connections.
"""

import os
import time
import numpy as np
import torch
import grpc
from concurrent import futures

from proto import inference_pb2, inference_pb2_grpc
from src.grpc_target import ResolvedInferenceClient
from src.models.resnet_splits import get_chain_segments


def _apply_thread_settings():
    """Mirror thread settings from environment variables."""
    intra = os.environ.get("PYTORCH_INTRA_OP_THREADS")
    inter = os.environ.get("PYTORCH_INTER_OP_THREADS")
    omp = os.environ.get("OMP_NUM_THREADS")

    if intra is not None:
        torch.set_num_threads(int(intra))
    elif omp is not None:
        torch.set_num_threads(int(omp))

    if inter is not None:
        torch.set_num_interop_threads(int(inter))
    else:
        torch.set_num_interop_threads(1)


class ChainServicer(inference_pb2_grpc.InferenceServiceServicer):
    """Serves one segment of a chain-decomposed ResNet-18.

    Parameters
    ----------
    segment_index : int
        0-based index of this segment in the chain.
    split_points : list[str]
        Ordered coarse split-point names defining the chain.
    next_client : ResolvedInferenceClient or None
        gRPC client for the next service in the chain. None for the last segment.
    """

    def __init__(self, segment_index: int, split_points: list,
                 next_client=None):
        segments = get_chain_segments(split_points)
        self.segment = segments[segment_index]
        self.segment_index = segment_index
        self.is_last = self.segment.is_last
        self.next_client = next_client

    def Infer(self, request, context):
        # Deserialize input
        t0 = time.perf_counter()
        arr = np.frombuffer(request.tensor_data, dtype=np.float32).copy()
        tensor = torch.from_numpy(arr.reshape(list(request.shape)))
        t1 = time.perf_counter()

        activation_bytes_in = len(request.tensor_data)

        # Compute (forward pass)
        with torch.no_grad():
            output = self.segment(tensor)
        t2 = time.perf_counter()

        # Serialize output
        out_bytes = output.contiguous().numpy().tobytes()
        out_shape = list(output.shape)
        t3 = time.perf_counter()

        if self.is_last:
            own_timing = inference_pb2.HopTiming(
                hop_index=self.segment_index + 1,  # 1-indexed
                deserialize_ms=(t1 - t0) * 1000,
                compute_ms=(t2 - t1) * 1000,
                serialize_ms=(t3 - t2) * 1000,
                forward_ms=0.0,  # last hop: no downstream call
                activation_bytes=activation_bytes_in,
            )
            return inference_pb2.InferResponse(
                tensor_data=out_bytes,
                shape=out_shape,
                hop_timings=[own_timing],
            )

        # Forward to next service — measure actual downstream wait time
        fwd_request = inference_pb2.InferRequest(
            tensor_data=out_bytes,
            shape=out_shape,
        )
        t_fwd_start = time.perf_counter()
        downstream_response = self.next_client.infer(fwd_request)
        t_fwd_end = time.perf_counter()

        own_timing = inference_pb2.HopTiming(
            hop_index=self.segment_index + 1,  # 1-indexed
            deserialize_ms=(t1 - t0) * 1000,
            compute_ms=(t2 - t1) * 1000,
            serialize_ms=(t3 - t2) * 1000,
            forward_ms=(t_fwd_end - t_fwd_start) * 1000,
            activation_bytes=activation_bytes_in,
        )

        # Propagate: own timing + all downstream timings
        all_timings = [own_timing]
        all_timings.extend(downstream_response.hop_timings)

        return inference_pb2.InferResponse(
            tensor_data=downstream_response.tensor_data,
            shape=list(downstream_response.shape),
            hop_timings=all_timings,
        )


def serve(segment_index: int, split_points: list,
          host: str = "0.0.0.0", port: int = 50051,
          next_address: str = None,
          max_message_bytes: int = 16 * 1024 * 1024):
    """Start a chain service for the given segment and block until termination."""
    _apply_thread_settings()

    # Connect to the next service if this is not the last segment
    next_client = None
    if next_address is not None:
        next_client = ResolvedInferenceClient(
            next_address,
            max_message_bytes=max_message_bytes,
        )

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=1),
        options=[
            ("grpc.max_send_message_length", max_message_bytes),
            ("grpc.max_receive_message_length", max_message_bytes),
        ],
    )
    servicer = ChainServicer(segment_index, split_points, next_client)
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(servicer, server)
    addr = f"{host}:{port}"
    server.add_insecure_port(addr)
    server.start()
    print("READY", flush=True)
    server.wait_for_termination()
