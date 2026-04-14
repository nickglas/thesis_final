"""Benchmark orchestrator: manages the full R-round, M-iteration experiment.

Implements the nested repetition structure from Section 5:
  For each round r in 1..R:
      Generate condition-order permutation pi_r
      For each condition c in pi_r:
          Start/restart Service B (if applicable)
          Wait for service readiness
          Run W warmup iterations (discarded)
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
from src.benchmark.logging import ArtifactLogger
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
            output_dir = os.path.join("results", f"rq1_1_{ts}")
        self.output_dir = output_dir
        self.artifact_logger = ArtifactLogger(output_dir)

        # Fixed deterministic input tensor (same across all conditions / rounds)
        torch.manual_seed(config.seed)
        self.input_tensor = torch.randn(*config.input_shape)

        self.all_rows = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self):
        """Execute the full benchmark and save raw artifacts."""
        logger.info("=" * 60)
        logger.info("RQ1.1 Benchmark — Starting")
        logger.info("=" * 60)

        self.artifact_logger.save_config_copy(self.config_path)
        self.artifact_logger.save_environment()

        cfg = self.config

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

        # Persist raw per-iteration data
        self.artifact_logger.save_raw_iterations(self.all_rows)
        logger.info(f"Benchmark complete. {len(self.all_rows)} iterations recorded.")
        logger.info(f"Results directory: {self.output_dir}")

    # ------------------------------------------------------------------
    # Monolithic condition
    # ------------------------------------------------------------------

    def _run_monolithic(self, round_num: int, cond):
        client = MonolithicClient()

        # Warmup
        logger.info(f"    Warmup: {self.config.warmup_iterations} iterations")
        for _ in range(self.config.warmup_iterations):
            client.warmup_infer(self.input_tensor)

        # Measured iterations
        logger.info(f"    Measuring: {self.config.measured_iterations} iterations")
        for i in range(self.config.measured_iterations):
            metrics = client.infer(self.input_tensor)
            self.all_rows.append({
                "round": round_num,
                "condition": cond.name,
                "iteration": i + 1,
                **metrics,
            })

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
                # Warmup
                logger.info(f"    Warmup: {cfg.warmup_iterations} iterations")
                for _ in range(cfg.warmup_iterations):
                    client.warmup_infer(self.input_tensor)

                # Measured iterations
                logger.info(f"    Measuring: {cfg.measured_iterations} iterations")
                for i in range(cfg.measured_iterations):
                    metrics = client.infer(self.input_tensor)
                    self.all_rows.append({
                        "round": round_num,
                        "condition": cond.name,
                        "iteration": i + 1,
                        **metrics,
                    })
            finally:
                client.close()
        finally:
            self._stop_service_b(proc)

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
