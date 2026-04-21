"""Benchmark orchestrator: manages the full R-round, M-iteration experiment.

Implements the nested repetition structure from Section 5:
  For each round r in 1..R:
      Generate condition-order permutation pi_r
      For each condition c in pi_r:
          Start/restart Service B (if applicable)
          Wait for service readiness
          Run gRPC parity validation (split conditions only)
          Run warmup with calibration check
          Run M measured iterations (recorded)
          Shut down Service B (if applicable)
          Cooldown pause
"""

import os
import sys
import time
import random
import subprocess
import logging

import torch
import grpc
from datetime import datetime

from src.benchmark.config import ExperimentConfig
from src.benchmark.cpu_stabilisation import apply_cpu_stabilisation
from src.benchmark.logging import ArtifactLogger
from src.benchmark.warmup import run_warmup_calibrated
from src.client.monolithic import MonolithicClient
from src.client.split_client import SplitClient

logger = logging.getLogger(__name__)


class BenchmarkRunner:

    def __init__(self, config: ExperimentConfig, config_path: str,
                 output_dir: str = None):
        self.config = config
        self.config_path = config_path

        if output_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Derive prefix from experiment name, e.g. "RQ1.2 ..." → "rq1_2"
            prefix = config.experiment_name.split()[0].lower().replace(".", "_")
            output_dir = os.path.join("results", f"{prefix}_{ts}")
        self.output_dir = output_dir
        self.artifact_logger = ArtifactLogger(output_dir)

        # Fixed deterministic input tensor (same across all conditions / rounds)
        torch.manual_seed(config.seed)
        self.input_tensor = torch.randn(*config.input_shape)

        self.all_rows = []

        # Set by run_experiment.py after local parity validation
        self.parity_local_results = {}
        self._parity_grpc_results = {}
        self._warmup_calibrations = {}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self):
        """Execute the full benchmark and save raw artifacts."""
        logger.info("=" * 60)
        logger.info("%s Benchmark — Starting", self.config.experiment_name)
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
                # Randomised condition order for this round (seeded)
                rng = random.Random(cfg.seed + round_num)
                order = list(range(len(cfg.conditions)))
                rng.shuffle(order)

                names = [cfg.conditions[i].name for i in order]
                logger.info(f"Round {round_num}/{cfg.rounds} — order: {names}")

                for idx in order:
                    cond = cfg.conditions[idx]
                    logger.info(f"  Condition: {cond.name}")

                    if cond.type == "monolithic":
                        self._run_monolithic(round_num, cond)
                    else:
                        self._run_split(round_num, cond)

                    # Cooldown between conditions
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

        parity_artifact = {
            "local_validation": self.parity_local_results,
            "grpc_validation": self._parity_grpc_results,
        }
        self.artifact_logger.save_json("parity_validation.json", parity_artifact)
        self.artifact_logger.save_json(
            "warmup_calibration.json", self._warmup_calibrations
        )

    # ------------------------------------------------------------------
    # Monolithic condition
    # ------------------------------------------------------------------

    def _run_monolithic(self, round_num: int, cond):
        client = MonolithicClient()
        cfg = self.config

        # Warmup with calibration
        cal_key = f"{cond.name}_round{round_num}"
        cal = run_warmup_calibrated(
            infer_fn=client.warmup_infer,
            input_tensor=self.input_tensor,
            n=cfg.warmup_iterations,
            window=cfg.warmup_calibration_window,
            cv_threshold=cfg.warmup_calibration_cv_threshold,
            max_extra_iterations=cfg.warmup_calibration_max_extra_iterations,
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
            row = {
                "round": round_num,
                "condition": cond.name,
                "iteration": i + 1,
                **metrics,
            }
            self.all_rows.append(row)
            self.artifact_logger.append_raw_iterations([row])

    # ------------------------------------------------------------------
    # Split condition
    # ------------------------------------------------------------------

    def _run_split(self, round_num: int, cond):
        cfg = self.config

        # Start Service B as a separate OS process
        proc = self._start_service_b(cond.split_after)
        try:
            # Verify gRPC channel is ready
            self._wait_for_channel(cfg.grpc_host, cfg.grpc_port)

            client = SplitClient(
                cond.split_after,
                cfg.grpc_host,
                cfg.grpc_port,
                cfg.grpc_max_message_bytes,
            )
            try:
                # gRPC parity validation (first round only to avoid redundancy)
                if round_num == 1:
                    self._validate_grpc_parity(client, cond)

                # Warmup with calibration
                cal_key = f"{cond.name}_round{round_num}"
                cal = run_warmup_calibrated(
                    infer_fn=client.warmup_infer,
                    input_tensor=self.input_tensor,
                    n=cfg.warmup_iterations,
                    window=cfg.warmup_calibration_window,
                    cv_threshold=cfg.warmup_calibration_cv_threshold,
                    max_extra_iterations=cfg.warmup_calibration_max_extra_iterations,
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
                    row = {
                        "round": round_num,
                        "condition": cond.name,
                        "iteration": i + 1,
                        **metrics,
                    }
                    self.all_rows.append(row)
                    self.artifact_logger.append_raw_iterations([row])
            finally:
                client.close()
        finally:
            self._stop_service_b(proc)

    def _validate_grpc_parity(self, client, cond):
        """Run gRPC round-trip parity check. Fail-closed on mismatch."""
        from src.models.validation import _infer_and_get_tensor
        from src.models.resnet_splits import get_full_model
        import numpy as np

        cfg = self.config
        logger.info(f"    gRPC parity validation: atol={cfg.parity_atol}, "
                     f"inputs={cfg.parity_num_inputs}")

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
            split_out = _infer_and_get_tensor(client, inp)

            diff = (mono_out - split_out).abs().max().item()
            max_diff = max(max_diff, diff)
            if diff > cfg.parity_atol:
                all_match = False

        result = {
            "match": all_match,
            "max_abs_diff": max_diff,
            "atol": cfg.parity_atol,
            "num_inputs": cfg.parity_num_inputs,
            "method": "grpc_round_trip",
        }
        self._parity_grpc_results[cond.split_after] = result

        status = "PASS" if all_match else "FAIL"
        logger.info(f"    gRPC parity: {status} (max_abs_diff={max_diff:.2e})")

        if not all_match:
            raise RuntimeError(
                f"gRPC parity validation FAILED for {cond.name} "
                f"(split_after={cond.split_after}). "
                f"max_abs_diff={max_diff:.2e} > atol={cfg.parity_atol}. "
                f"Benchmark aborted."
            )

    # ------------------------------------------------------------------
    # Service B process management
    # ------------------------------------------------------------------

    def _start_service_b(self, split_after: str) -> subprocess.Popen:
        cfg = self.config
        cmd = [
            sys.executable, "-u", "-m", "src.services.service_b_runner",
            "--split_after", split_after,
            "--host", cfg.grpc_host,
            "--port", str(cfg.grpc_port),
            "--max_message_bytes", str(cfg.grpc_max_message_bytes),
        ]
        logger.info(f"    Starting Service B (split_after={split_after})")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        # Propagate thread-count variables so Service B uses identical settings
        for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            if var in os.environ:
                env[var] = os.environ[var]
        # Propagate PyTorch thread counts for Service B to apply
        threading = cfg.cpu_stabilisation.threading
        env["PYTORCH_INTRA_OP_THREADS"] = str(threading.pytorch_intra_op)
        env["PYTORCH_INTER_OP_THREADS"] = str(threading.pytorch_inter_op)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        # Wait for the READY signal on stdout
        line = proc.stdout.readline()
        if not line or line.decode().strip() != "READY":
            proc.terminate()
            stderr = proc.stderr.read().decode()
            raise RuntimeError(
                f"Service B failed to start. stdout={line!r}, stderr={stderr}"
            )
        logger.info("    Service B ready")
        return proc

    def _stop_service_b(self, proc: subprocess.Popen):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        logger.info("    Service B stopped")

    def _wait_for_channel(self, host: str, port: int, timeout: float = 30.0):
        """Block until the gRPC channel reports READY."""
        channel = grpc.insecure_channel(f"{host}:{port}")
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout)
        except grpc.FutureTimeoutError:
            raise RuntimeError(
                f"gRPC channel not ready after {timeout}s on {host}:{port}"
            )
        finally:
            channel.close()
