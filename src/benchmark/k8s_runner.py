"""Kubernetes benchmark runner for RQ1.4 chain experiments.

Assumes services are already deployed to the cluster and reachable via
standard Kubernetes DNS. The runner performs:

  For each round r in 1..R:
      Generate condition-order permutation
      For each condition c:
          Resolve all service addresses for the condition
          Wait for gRPC readiness on every service in the chain
          Run live chain parity validation (round 1 only)
          Run warmup with calibration check
          Run M measured iterations (recorded)
          Cooldown pause

Service deployment/teardown is handled externally (by the experiment
entrypoint or operator scripts), not by this runner.
"""

import os
import time
import random
import logging
import subprocess

import grpc
import torch
import numpy as np
from datetime import datetime

from src.benchmark.config import (
    ExperimentConfig,
    K8sConfig,
    format_k8s_service_name,
)
from src.benchmark.cpu_stabilisation import apply_cpu_stabilisation
from src.benchmark.logging import ArtifactLogger
from src.benchmark.warmup import run_warmup_calibrated
from src.client.chain_client import ChainClient
from src.models.resnet_splits import get_full_model, get_chain_segments

logger = logging.getLogger(__name__)

# Maximum hop columns in the CSV (chain_5svc = 5 services)
MAX_HOPS = 5


def _flatten_chain_metrics(metrics: dict) -> dict:
    """Flatten chain client metrics into the RQ1.4 CSV schema.

    Converts the nested hop_timings list into flat hop_N_* columns,
    zero-filling unused hop slots up to MAX_HOPS.
    """
    flat = {
        "end_to_end_ms": metrics["end_to_end_ms"],
        "total_compute_ms": metrics["total_compute_ms"],
        "non_compute_overhead_ms": metrics["non_compute_overhead_ms"],
        "total_activation_bytes": metrics["total_activation_bytes"],
        "num_hops": metrics["num_hops"],
    }

    for i in range(1, MAX_HOPS + 1):
        hop = None
        for h in metrics["hop_timings"]:
            if h["hop_index"] == i:
                hop = h
                break
        flat[f"hop_{i}_compute_ms"] = hop["compute_ms"] if hop else 0.0
        flat[f"hop_{i}_deserialize_ms"] = hop["deserialize_ms"] if hop else 0.0
        flat[f"hop_{i}_serialize_ms"] = hop["serialize_ms"] if hop else 0.0
        flat[f"hop_{i}_forward_ms"] = hop["forward_ms"] if hop else 0.0
        flat[f"hop_{i}_activation_bytes"] = hop["activation_bytes"] if hop else 0

    return flat


def resolve_all_service_addresses(cond, k8s_cfg: K8sConfig) -> list:
    """Resolve DNS addresses for every service in a chain condition.

    Returns a list of (service_name, address) tuples ordered by segment index.
    For monolithic_k8s_1svc: 1 service.  For chain_Nsvc: N services.
    """
    split_points = cond.chain_split_points or []
    n_services = len(split_points) + 1

    addresses = []
    for idx in range(1, n_services + 1):
        svc_name = format_k8s_service_name(
            k8s_cfg.service_name_template,
            cond.name,
            idx,
        )
        address = (
            f"{svc_name}.{k8s_cfg.namespace}"
            f".svc.cluster.local:{k8s_cfg.grpc_port}"
        )
        addresses.append((svc_name, address))
    return addresses


def wait_for_all_services(addresses: list, timeout: float = 60.0):
    """Block until every service in the chain is gRPC-ready.

    Parameters
    ----------
    addresses : list of (service_name, address) tuples
    timeout : float
        Per-service timeout in seconds.

    Raises RuntimeError if any service fails to become ready.
    """
    for svc_name, address in addresses:
        logger.info(f"      Waiting for {svc_name} at {address}...")
        channel = grpc.insecure_channel(address)
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout)
            logger.info(f"      {svc_name} READY")
        except grpc.FutureTimeoutError:
            raise RuntimeError(
                f"gRPC service {svc_name} not ready after {timeout}s "
                f"at {address}"
            )
        finally:
            channel.close()


def collect_k8s_metadata(cond, k8s_cfg: K8sConfig,
                         service_addresses: list) -> dict:
    """Collect Kubernetes deployment metadata for a condition.

    Gathers pod names, node placement, and cluster context where available.
    Failures are non-fatal — returns best-effort metadata.
    """
    meta = {
        "namespace": k8s_cfg.namespace,
        "condition": cond.name,
        "num_services": len(service_addresses),
        "split_points": cond.chain_split_points or [],
        "services": [],
    }

    # Cluster context
    try:
        ctx = subprocess.check_output(
            ["kubectl", "config", "current-context"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip()
        meta["cluster_context"] = ctx
    except Exception:
        meta["cluster_context"] = "unknown"

    # Cluster info (server URL)
    try:
        info = subprocess.check_output(
            ["kubectl", "cluster-info"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip()
        # Extract first line (control plane address)
        first_line = info.split("\n")[0] if info else ""
        meta["cluster_info"] = first_line
    except Exception:
        meta["cluster_info"] = "unknown"

    # Per-service pod details
    for svc_name, address in service_addresses:
        svc_meta = {
            "service_name": svc_name,
            "address": address,
            "pod_name": "unknown",
            "node_name": "unknown",
            "pod_ip": "unknown",
        }

        # Find the segment index from the service name suffix
        try:
            seg_idx = svc_name.rsplit("-", 1)[-1]
            pod_json = subprocess.check_output(
                [
                    "kubectl", "get", "pods",
                    "-n", k8s_cfg.namespace,
                    "-l", f"condition={cond.name},segment-index={seg_idx}",
                    "-o", "jsonpath="
                    "{.items[0].metadata.name}|"
                    "{.items[0].spec.nodeName}|"
                    "{.items[0].status.podIP}",
                ],
                stderr=subprocess.DEVNULL, timeout=10,
            ).decode().strip()
            parts = pod_json.split("|")
            if len(parts) >= 3:
                svc_meta["pod_name"] = parts[0] or "unknown"
                svc_meta["node_name"] = parts[1] or "unknown"
                svc_meta["pod_ip"] = parts[2] or "unknown"
        except Exception:
            pass

        meta["services"].append(svc_meta)

    meta["collected_at"] = datetime.now().isoformat()
    return meta


class K8sBenchmarkRunner:
    """Benchmark runner for RQ1.4 chain experiments on Kubernetes.

    Parameters
    ----------
    config : ExperimentConfig
        Full experiment configuration (must include kubernetes section).
    config_path : str
        Path to the YAML config file (copied to output).
    output_dir : str, optional
        Override output directory. Auto-generated if None.
    """

    def __init__(self, config: ExperimentConfig, config_path: str,
                 output_dir: str = None):
        self.config = config
        self.config_path = config_path

        if config.kubernetes is None:
            raise ValueError(
                "K8sBenchmarkRunner requires a 'kubernetes' section in config"
            )
        self.k8s_cfg = config.kubernetes

        if output_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = config.experiment_name.split()[0].lower().replace(".", "_")
            output_dir = os.path.join("results", f"{prefix}_{ts}")
        self.output_dir = output_dir
        self.artifact_logger = ArtifactLogger(output_dir)

        # Fixed deterministic input tensor
        torch.manual_seed(config.seed)
        self.input_tensor = torch.randn(*config.input_shape)

        self.all_rows = []
        self.parity_local_results = {}
        self._parity_grpc_results = {}
        self._warmup_calibrations = {}
        self._deployment_metadata = {}

    def run(self):
        """Execute the full benchmark and save raw artifacts."""
        logger.info("=" * 60)
        logger.info("%s K8s Benchmark — Starting", self.config.experiment_name)
        logger.info("=" * 60)

        # Apply CPU-behaviour stabilisation before any measurement
        self.stabilisation_meta = apply_cpu_stabilisation(
            self.config.cpu_stabilisation,
        )

        self.artifact_logger.save_config_copy(self.config_path)
        self.artifact_logger.save_environment(self.stabilisation_meta)

        cfg = self.config
        completed = False

        try:
            for round_num in range(1, cfg.rounds + 1):
                rng = random.Random(cfg.seed + round_num)
                order = list(range(len(cfg.conditions)))
                rng.shuffle(order)

                names = [cfg.conditions[i].name for i in order]
                logger.info(f"Round {round_num}/{cfg.rounds} — order: {names}")

                for idx in order:
                    cond = cfg.conditions[idx]
                    logger.info(f"  Condition: {cond.name}")
                    self._run_chain_condition(round_num, cond)

                    logger.info(f"  Cooldown: {cfg.cooldown_seconds}s")
                    time.sleep(cfg.cooldown_seconds)

            completed = True
        finally:
            self._persist_artifacts()
            if completed:
                logger.info(
                    f"Benchmark complete. {len(self.all_rows)} iterations recorded."
                )
            else:
                logger.warning(
                    "Benchmark interrupted after %s iterations. Partial artifacts saved.",
                    len(self.all_rows),
                )
            logger.info(f"Results directory: {self.output_dir}")

    def _persist_artifacts(self):
        self.artifact_logger.save_raw_iterations(self.all_rows)
        self.artifact_logger.save_json("parity_validation.json", {
            "local_validation": self.parity_local_results,
            "grpc_validation": self._parity_grpc_results,
        })
        self.artifact_logger.save_json(
            "warmup_calibration.json", self._warmup_calibrations
        )
        self.artifact_logger.save_json(
            "deployment_metadata.json", self._deployment_metadata
        )

    def _run_chain_condition(self, round_num: int, cond):
        """Run one chain condition (including monolithic_k8s_1svc)."""
        cfg = self.config
        k8s = self.k8s_cfg

        # Resolve ALL service addresses for the chain
        service_addresses = resolve_all_service_addresses(cond, k8s)
        first_svc_name, first_address = service_addresses[0]

        logger.info(
            f"    Chain: {len(service_addresses)} services, "
            f"first={first_svc_name}"
        )
        for svc_name, addr in service_addresses:
            logger.info(f"      {svc_name} -> {addr}")

        # Wait for ALL services in the chain to become gRPC-ready
        logger.info("    Checking full-chain readiness...")
        wait_for_all_services(service_addresses, timeout=k8s.readiness_timeout)
        logger.info("    All services ready")

        # Collect deployment metadata (once per condition, round 1)
        if round_num == 1:
            meta = collect_k8s_metadata(cond, k8s, service_addresses)
            self._deployment_metadata[cond.name] = meta
            logger.info(f"    Deployment metadata captured")

        client = ChainClient(first_address, k8s.max_message_bytes)
        try:
            # Live chain parity validation (round 1 only)
            if round_num == 1:
                self._validate_chain_parity(client, cond)

            # Warmup
            cal_key = f"{cond.name}_round{round_num}"
            cal = run_warmup_calibrated(
                infer_fn=client.warmup_infer,
                input_tensor=self.input_tensor,
                n=cfg.warmup_iterations,
                window=cfg.warmup_calibration_window,
                cv_threshold=cfg.warmup_calibration_cv_threshold,
            )
            self._warmup_calibrations[cal_key] = cal
            logger.info(
                f"    Warmup: {cal['total_iterations']} iterations, "
                f"stabilised={cal['stabilised']}, "
                f"stabilised_at={cal['stabilised_at_iteration']}"
            )

            # Measured iterations
            logger.info(f"    Measuring: {cfg.measured_iterations} iterations")
            for i in range(cfg.measured_iterations):
                metrics = client.infer(self.input_tensor)
                flat = _flatten_chain_metrics(metrics)
                row = {
                    "round": round_num,
                    "condition": cond.name,
                    "iteration": i + 1,
                    **flat,
                }
                self.all_rows.append(row)
                self.artifact_logger.append_raw_iterations([row])
        finally:
            client.close()

    def _validate_chain_parity(self, client: ChainClient, cond):
        """Live chain parity validation: send test inputs through the deployed
        chain and compare output to local monolithic model. Fail-closed."""
        cfg = self.config
        logger.info(
            f"    Chain parity validation: atol={cfg.parity_atol}, "
            f"inputs={cfg.parity_num_inputs}"
        )

        rng = np.random.RandomState(cfg.seed)
        model = get_full_model()

        all_match = True
        max_diff = 0.0

        for _ in range(cfg.parity_num_inputs):
            inp = torch.from_numpy(
                rng.randn(1, 3, 224, 224).astype(np.float32)
            )
            with torch.no_grad():
                mono_out = model(inp)

            chain_out = _infer_and_get_tensor(client, inp)
            diff = (mono_out - chain_out).abs().max().item()
            max_diff = max(max_diff, diff)
            if diff > cfg.parity_atol:
                all_match = False

        result = {
            "match": all_match,
            "max_abs_diff": max_diff,
            "atol": cfg.parity_atol,
            "num_inputs": cfg.parity_num_inputs,
            "method": "live_chain_grpc",
        }
        self._parity_grpc_results[cond.name] = result

        status = "PASS" if all_match else "FAIL"
        logger.info(f"    Chain parity: {status} (max_abs_diff={max_diff:.2e})")

        if not all_match:
            raise RuntimeError(
                f"Chain parity validation FAILED for {cond.name}. "
                f"max_abs_diff={max_diff:.2e} > atol={cfg.parity_atol}. "
                f"Benchmark aborted."
            )


def _infer_and_get_tensor(client: ChainClient,
                          input_tensor: torch.Tensor) -> torch.Tensor:
    """Run chain inference and return the output tensor."""
    from proto import inference_pb2

    request_bytes = input_tensor.contiguous().numpy().tobytes()
    request_shape = list(input_tensor.shape)
    response = client.stub.Infer(
        inference_pb2.InferRequest(
            tensor_data=request_bytes,
            shape=request_shape,
        )
    )
    out_arr = np.frombuffer(response.tensor_data, dtype=np.float32).copy()
    return torch.from_numpy(out_arr.reshape(list(response.shape)))
