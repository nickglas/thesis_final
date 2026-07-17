"""Helpers for stable gRPC targets in Kubernetes-style environments.

The benchmark code historically connected to service DNS names directly.
In local clusters with transient CoreDNS stalls, an already-running service can
still become temporarily unreachable if a fresh gRPC channel needs a hostname
lookup at the wrong moment. These helpers resolve a target once to a stable IP
address and reuse that channel for subsequent calls.
"""

from __future__ import annotations

import ipaddress
import socket
import time

import grpc

from proto import inference_pb2_grpc


_DEFAULT_RESOLUTION_ATTEMPTS = 5
_DEFAULT_RESOLUTION_BACKOFF_SECONDS = 0.25
_RETRYABLE_UNAVAILABLE_MARKERS = (
    "lookup error",
    "address lookup failed",
    "timeout while contacting dns servers",
    "name resolution",
    "failed to connect to all addresses",
)


def _split_target(target: str) -> tuple[str, int]:
    if ":" not in target:
        raise ValueError(f"gRPC target must be host:port, got {target!r}")
    host, port_text = target.rsplit(":", 1)
    return host, int(port_text)


def _is_ip_literal(host: str) -> bool:
    candidate = host
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        ipaddress.ip_address(candidate)
        return True
    except ValueError:
        return False


def resolve_target_address(
    target: str,
    resolution_attempts: int = _DEFAULT_RESOLUTION_ATTEMPTS,
    resolution_backoff_seconds: float = _DEFAULT_RESOLUTION_BACKOFF_SECONDS,
) -> str:
    """Resolve a gRPC host:port target to a stable IP:port target.

    If the host is already an IP literal, the original target is returned.
    """
    host, port = _split_target(target)
    if _is_ip_literal(host):
        return target

    last_error = None
    for attempt in range(resolution_attempts):
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            if not infos:
                raise socket.gaierror(f"No addresses returned for {host}")

            chosen_ip = None
            fallback_ip = None
            for family, _, _, _, sockaddr in infos:
                candidate_ip = sockaddr[0]
                if fallback_ip is None:
                    fallback_ip = candidate_ip
                if family == socket.AF_INET:
                    chosen_ip = candidate_ip
                    break

            resolved_ip = chosen_ip or fallback_ip
            return f"{resolved_ip}:{port}"
        except OSError as exc:
            last_error = exc
            if attempt + 1 < resolution_attempts:
                time.sleep(resolution_backoff_seconds)

    raise RuntimeError(
        f"Could not resolve gRPC target {target!r} after "
        f"{resolution_attempts} attempts: {last_error}"
    )


def build_insecure_channel(target: str, max_message_bytes: int):
    return grpc.insecure_channel(
        target,
        options=[
            ("grpc.max_send_message_length", max_message_bytes),
            ("grpc.max_receive_message_length", max_message_bytes),
        ],
    )


class ResolvedInferenceClient:
    """InferenceService client that resolves hostnames once and reuses the IP."""

    def __init__(
        self,
        target: str,
        max_message_bytes: int = 16 * 1024 * 1024,
        resolution_attempts: int = _DEFAULT_RESOLUTION_ATTEMPTS,
        resolution_backoff_seconds: float = _DEFAULT_RESOLUTION_BACKOFF_SECONDS,
    ):
        self.original_target = target
        self.max_message_bytes = max_message_bytes
        self.resolution_attempts = resolution_attempts
        self.resolution_backoff_seconds = resolution_backoff_seconds

        self.current_target = None
        self.channel = None
        self.stub = None

    def _connect(self, force_refresh: bool = False):
        if self.stub is not None and not force_refresh:
            return

        resolved_target = resolve_target_address(
            self.original_target,
            resolution_attempts=self.resolution_attempts,
            resolution_backoff_seconds=self.resolution_backoff_seconds,
        )

        if self.channel is not None:
            self.channel.close()

        self.current_target = resolved_target
        self.channel = build_insecure_channel(
            resolved_target,
            max_message_bytes=self.max_message_bytes,
        )
        self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)

    def infer(self, request):
        self._connect()
        try:
            return self.stub.Infer(request)
        except grpc.RpcError as exc:
            if self._should_retry(exc):
                self._connect(force_refresh=True)
                return self.stub.Infer(request)
            raise

    def close(self):
        if self.channel is not None:
            self.channel.close()
        self.channel = None
        self.stub = None

    @staticmethod
    def _should_retry(exc: grpc.RpcError) -> bool:
        if exc.code() != grpc.StatusCode.UNAVAILABLE:
            return False

        details = (exc.details() or "").lower()
        return any(marker in details for marker in _RETRYABLE_UNAVAILABLE_MARKERS)