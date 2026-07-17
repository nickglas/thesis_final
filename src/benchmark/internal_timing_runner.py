"""Internal timing benchmark runner.

Executes the instrumented ResNet-18 forward pass over multiple rounds
and iterations, collecting per-unit timing measurements.  Produces
raw_timings.csv and supporting artifacts.

This module is part of the exploratory internal-timing mode and does
NOT modify the thesis-facing split benchmark runner.
"""

import os
import time
import logging
from typing import Dict, Any, List

import torch

from src.models.instrumented_resnet import (
    InstrumentedResNet,
    validate_instrumented_equivalence,
)
from src.models.resnet_splits import get_full_model
from src.benchmark.internal_timing_config import InternalTimingConfig
from src.benchmark.cpu_stabilisation import apply_cpu_stabilisation
from src.benchmark.warmup import run_warmup_calibrated
from src.benchmark.logging import ArtifactLogger

logger = logging.getLogger(__name__)

# Hierarchy level tags for the raw CSV
_LEVEL_TAGS = {
    "model": "L0",
    "stem": "L1", "layer1": "L1", "layer2": "L1", "layer3": "L1",
    "layer4": "L1", "avgpool": "L1", "fc": "L1",
}


def _unit_level(name: str) -> str:
    """Determine the hierarchy level tag for a timing unit name."""
    if name in _LEVEL_TAGS:
        return _LEVEL_TAGS[name]
    parts = name.split(".")
    if len(parts) == 2 and parts[0].startswith("layer"):
        # e.g. "layer3.0" — block level
        return "L2"
    if len(parts) == 2 and parts[0] == "stem":
        # e.g. "stem.conv1" — operation level
        return "L3"
    if len(parts) == 3:
        # e.g. "layer3.0.conv1" — operation level
        return "L3"
    return "L3"


def _unit_parent(name: str) -> str:
    """Determine the parent unit for a timing unit name."""
    if name == "model":
        return ""
    parts = name.split(".")
    if len(parts) == 1:
        # L1 stage — parent is model
        return "model"
    if len(parts) == 2:
        if parts[0] == "stem":
            return "stem"
        # block like layer3.0 — parent is stage
        return parts[0]
    if len(parts) == 3:
        # op like layer3.0.conv1 — parent is block
        return f"{parts[0]}.{parts[1]}"
    return ""


class InternalTimingRunner:
    """Runner for the internal timing benchmark."""

    def __init__(self, config: InternalTimingConfig, config_path: str,
                 output_dir: str):
        self.config = config
        self.config_path = config_path
        self.output_dir = output_dir
        self.logger = ArtifactLogger(output_dir)

    def run(self) -> str:
        """Execute the full internal timing benchmark.  Returns output_dir."""
        cfg = self.config

        # 1. Apply CPU stabilisation
        logger.info("Applying CPU stabilisation...")
        stab_meta = apply_cpu_stabilisation(cfg.cpu_stabilisation)

        # 2. Save config copy and environment
        self.logger.save_config_copy(self.config_path)
        self.logger.save_environment(stab_meta)

        # 3. Functional equivalence validation
        logger.info("Validating instrumented model equivalence...")
        val_result = validate_instrumented_equivalence(
            num_inputs=cfg.validation.num_inputs,
            atol=cfg.validation.atol,
            seed=cfg.benchmark.seed,
            level=cfg.timing.level,
        )
        self.logger.save_json("validation.json", val_result)
        logger.info(
            f"Equivalence validation passed (max diff: {val_result['max_abs_diff']:.2e})"
        )

        # 4. Create instrumented model and fixed input
        model = InstrumentedResNet(
            level=cfg.timing.level,
            include_stem_ops=cfg.timing.include_stem_ops,
        )
        model.eval()

        torch.manual_seed(cfg.benchmark.seed)
        input_tensor = torch.randn(*cfg.input_shape)

        # 5. Warmup
        logger.info(f"Running {cfg.benchmark.warmup_iterations} warmup iterations...")
        warmup_result = run_warmup_calibrated(
            infer_fn=model.warmup_forward,
            input_tensor=input_tensor,
            n=cfg.benchmark.warmup_iterations,
            window=cfg.warmup_calibration.window,
            cv_threshold=cfg.warmup_calibration.cv_threshold,
            max_extra_iterations=cfg.warmup_calibration.max_extra_iterations,
        )
        self.logger.save_json("warmup_calibration.json", warmup_result)
        logger.info(
            f"Warmup complete. Stabilised: {warmup_result['stabilised']} "
            f"(CV: {warmup_result['final_window_cv']:.4f})"
        )

        # 6. Measure instrumentation overhead
        overhead = None
        if cfg.timing.measure_overhead:
            overhead = self._measure_overhead(model, input_tensor)
            self.logger.save_json("instrumentation_overhead.json", overhead)
            logger.info(
                f"Instrumentation overhead: {overhead['overhead_ms']:.4f} ms "
                f"({overhead['overhead_pct']:.2f}%)"
            )

        # 7. Measurement loop
        logger.info(
            f"Starting measurement: {cfg.benchmark.rounds} rounds × "
            f"{cfg.benchmark.measured_iterations} iterations"
        )
        raw_rows = self._run_measurement_loop(model, input_tensor)

        # 8. Save raw timings
        self.logger.save_csv("raw_timings.csv", raw_rows)
        logger.info(f"Saved {len(raw_rows)} raw timing rows to raw_timings.csv")

        return self.output_dir

    def _measure_overhead(self, model: InstrumentedResNet,
                          input_tensor: torch.Tensor) -> Dict[str, Any]:
        """Measure instrumentation overhead by comparing plain vs instrumented forward.

        Methodology:
        - Both models are warmed up equally before measurement.
        - Measurements are interleaved (ABAB) to neutralise ordering/cache effects.
        - Both paths are timed from the same outer window (perf_counter wrapping
          the torch.no_grad + forward call) so the comparison is symmetric.
        """
        n_overhead = 50
        n_warmup = 20
        plain_model = get_full_model()
        plain_model.eval()

        # Warm up BOTH models equally
        for _ in range(n_warmup):
            with torch.no_grad():
                _ = plain_model(input_tensor)
        for _ in range(n_warmup):
            with torch.no_grad():
                _ = model.warmup_forward(input_tensor)

        # Interleaved measurement (ABAB) with symmetric outer timing
        plain_times = []
        instr_times = []
        for _ in range(n_overhead):
            # Plain
            t0 = time.perf_counter()
            with torch.no_grad():
                _ = plain_model(input_tensor)
            plain_times.append((time.perf_counter() - t0) * 1000)

            # Instrumented — timed from same outer window
            t0 = time.perf_counter()
            with torch.no_grad():
                _, _ = model(input_tensor)
            instr_times.append((time.perf_counter() - t0) * 1000)

        plain_mean = sum(plain_times) / len(plain_times)
        instr_mean = sum(instr_times) / len(instr_times)
        overhead_ms = instr_mean - plain_mean
        overhead_pct = (overhead_ms / plain_mean * 100) if plain_mean > 0 else 0.0

        return {
            "n_samples": n_overhead,
            "n_warmup": n_warmup,
            "plain_mean_ms": round(plain_mean, 4),
            "instrumented_mean_ms": round(instr_mean, 4),
            "overhead_ms": round(overhead_ms, 4),
            "overhead_pct": round(overhead_pct, 2),
            "method": "interleaved_outer_timing",
        }

    def _run_measurement_loop(self, model: InstrumentedResNet,
                              input_tensor: torch.Tensor) -> List[Dict[str, Any]]:
        """Run the measurement loop and return flat timing rows."""
        cfg = self.config
        rows: List[Dict[str, Any]] = []

        for round_num in range(1, cfg.benchmark.rounds + 1):
            logger.info(f"Round {round_num}/{cfg.benchmark.rounds}")
            for iteration in range(1, cfg.benchmark.measured_iterations + 1):
                with torch.no_grad():
                    _, timings = model(input_tensor)

                for unit_name, elapsed_ms in timings.items():
                    rows.append({
                        "round": round_num,
                        "iteration": iteration,
                        "unit_name": unit_name,
                        "level": _unit_level(unit_name),
                        "parent": _unit_parent(unit_name),
                        "elapsed_ms": round(elapsed_ms, 6),
                    })

        return rows
