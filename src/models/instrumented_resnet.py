"""Instrumented ResNet-18 wrapper for internal compute-distribution profiling.

Provides an explicit forward path with per-operation timing using
time.perf_counter().  The wrapper holds references to the original
pretrained modules — no weight copies are made.

Timing hierarchy
----------------
L0  model           — whole forward pass
L1  stem, layer1–4, avgpool, fc   — stage level (7 stages)
L2  layerN.B        — block level (8 BasicBlocks)
L3  layerN.B.op     — operation level inside each BasicBlock

Non-module operations (residual add, flatten) are timed explicitly.
The shared self.relu inside BasicBlock is disambiguated as relu1 / relu2.

This module is part of the exploratory internal-timing mode and does
NOT modify the thesis-facing split benchmark code path.
"""

import time
from typing import Dict, Tuple, Optional

import torch
import torch.nn as nn

from src.models.resnet_splits import get_full_model

# Timing levels
LEVEL_STAGE = "stage"
LEVEL_BLOCK = "block"
LEVEL_OPERATION = "operation"
LEVEL_FULL = "full"

VALID_LEVELS = {LEVEL_STAGE, LEVEL_BLOCK, LEVEL_OPERATION, LEVEL_FULL}

# Stage names at L1
STAGE_NAMES = ("stem", "layer1", "layer2", "layer3", "layer4", "avgpool", "fc")


def _pc() -> float:
    """Return perf_counter reading in milliseconds."""
    return time.perf_counter() * 1000


class InstrumentedResNet(nn.Module):
    """Instrumented ResNet-18 that times internal operations.

    Parameters
    ----------
    level : str
        Timing granularity: "stage", "block", "operation", or "full".
        "full" is an alias for "operation".
    include_stem_ops : bool
        If True and level is operation/full, time individual stem operations.
    """

    def __init__(self, level: str = "full", include_stem_ops: bool = True):
        super().__init__()
        if level not in VALID_LEVELS:
            raise ValueError(f"Invalid timing level: {level!r}. Valid: {sorted(VALID_LEVELS)}")

        self.level = LEVEL_OPERATION if level == LEVEL_FULL else level
        self.include_stem_ops = include_stem_ops

        model = get_full_model()

        # Stem modules
        self.conv1 = model.conv1
        self.bn1 = model.bn1
        self.relu = model.relu
        self.maxpool = model.maxpool

        # Residual stages (each is nn.Sequential of BasicBlocks)
        self.layer1 = model.layer1
        self.layer2 = model.layer2
        self.layer3 = model.layer3
        self.layer4 = model.layer4

        # Head
        self.avgpool = model.avgpool
        self.fc = model.fc

        self._stages = [
            ("layer1", self.layer1),
            ("layer2", self.layer2),
            ("layer3", self.layer3),
            ("layer4", self.layer4),
        ]

    # ------------------------------------------------------------------
    # Forward with timing
    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Run forward pass and return (output, timings_dict).

        timings_dict maps hierarchical unit names to elapsed milliseconds.
        """
        timings: Dict[str, float] = {}

        t_model_start = _pc()

        # ---- stem ----
        x = self._forward_stem(x, timings)

        # ---- layer1..layer4 ----
        for stage_name, stage_module in self._stages:
            x = self._forward_stage(x, stage_name, stage_module, timings)

        # ---- avgpool ----
        t0 = _pc()
        x = self.avgpool(x)
        timings["avgpool"] = _pc() - t0

        # ---- fc (includes flatten) ----
        t0 = _pc()
        x = torch.flatten(x, 1)
        x = self.fc(x)
        timings["fc"] = _pc() - t0

        timings["model"] = _pc() - t_model_start

        return x, timings

    # ------------------------------------------------------------------
    # Stem
    # ------------------------------------------------------------------

    def _forward_stem(self, x: torch.Tensor, timings: Dict[str, float]) -> torch.Tensor:
        t_stem_start = _pc()

        if self.level == LEVEL_OPERATION and self.include_stem_ops:
            t0 = _pc()
            x = self.conv1(x)
            timings["stem.conv1"] = _pc() - t0

            t0 = _pc()
            x = self.bn1(x)
            timings["stem.bn1"] = _pc() - t0

            t0 = _pc()
            x = self.relu(x)
            timings["stem.relu"] = _pc() - t0

            t0 = _pc()
            x = self.maxpool(x)
            timings["stem.maxpool"] = _pc() - t0
        else:
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            x = self.maxpool(x)

        timings["stem"] = _pc() - t_stem_start
        return x

    # ------------------------------------------------------------------
    # Residual stages
    # ------------------------------------------------------------------

    def _forward_stage(
        self,
        x: torch.Tensor,
        stage_name: str,
        stage_module: nn.Sequential,
        timings: Dict[str, float],
    ) -> torch.Tensor:
        t_stage_start = _pc()

        if self.level in (LEVEL_BLOCK, LEVEL_OPERATION):
            for block_idx in range(len(stage_module)):
                block = stage_module[block_idx]
                block_name = f"{stage_name}.{block_idx}"
                x = self._forward_block(x, block_name, block, timings)
        else:
            # Stage level only — run the whole stage without block timing
            x = stage_module(x)

        timings[stage_name] = _pc() - t_stage_start
        return x

    # ------------------------------------------------------------------
    # BasicBlock
    # ------------------------------------------------------------------

    def _forward_block(
        self,
        x: torch.Tensor,
        block_name: str,
        block: nn.Module,
        timings: Dict[str, float],
    ) -> torch.Tensor:
        t_block_start = _pc()

        if self.level == LEVEL_OPERATION:
            x = self._forward_block_ops(x, block_name, block, timings)
        else:
            # Block level — time the whole block, no per-op detail
            x = block(x)

        timings[block_name] = _pc() - t_block_start
        return x

    def _forward_block_ops(
        self,
        x: torch.Tensor,
        block_name: str,
        block: nn.Module,
        timings: Dict[str, float],
    ) -> torch.Tensor:
        """Execute a BasicBlock with per-operation timing."""
        identity = x

        # conv1
        t0 = _pc()
        out = block.conv1(x)
        timings[f"{block_name}.conv1"] = _pc() - t0

        # bn1
        t0 = _pc()
        out = block.bn1(out)
        timings[f"{block_name}.bn1"] = _pc() - t0

        # relu1 (mid-block relu)
        t0 = _pc()
        out = block.relu(out)
        timings[f"{block_name}.relu1"] = _pc() - t0

        # conv2
        t0 = _pc()
        out = block.conv2(out)
        timings[f"{block_name}.conv2"] = _pc() - t0

        # bn2
        t0 = _pc()
        out = block.bn2(out)
        timings[f"{block_name}.bn2"] = _pc() - t0

        # downsample (if present)
        if block.downsample is not None:
            t0 = _pc()
            identity = block.downsample(x)
            timings[f"{block_name}.downsample"] = _pc() - t0

        # residual add
        t0 = _pc()
        out = out + identity
        timings[f"{block_name}.add"] = _pc() - t0

        # relu2 (post-add relu)
        t0 = _pc()
        out = block.relu(out)
        timings[f"{block_name}.relu2"] = _pc() - t0

        return out

    # ------------------------------------------------------------------
    # Plain forward (no timing) for warmup
    # ------------------------------------------------------------------

    def warmup_forward(self, x: torch.Tensor) -> None:
        """Run an untimed forward pass for warmup/JIT purposes."""
        with torch.no_grad():
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            x = self.maxpool(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            x = self.avgpool(x)
            x = torch.flatten(x, 1)
            x = self.fc(x)


def validate_instrumented_equivalence(
    num_inputs: int = 5,
    atol: float = 1e-6,
    seed: int = 42,
    level: str = "full",
) -> Dict:
    """Validate that InstrumentedResNet produces identical outputs to the original model.

    Returns a dict with validation results.  Raises RuntimeError if any
    mismatch exceeds tolerance.
    """
    torch.manual_seed(seed)
    reference_model = get_full_model()
    instrumented = InstrumentedResNet(level=level)
    instrumented.eval()

    results = {
        "num_inputs": num_inputs,
        "atol": atol,
        "seed": seed,
        "level": level,
        "passed": True,
        "max_abs_diff": 0.0,
        "per_input": [],
    }

    for i in range(num_inputs):
        inp = torch.randn(1, 3, 224, 224)
        with torch.no_grad():
            ref_out = reference_model(inp)
            instr_out, _ = instrumented(inp)

        diff = (ref_out - instr_out).abs().max().item()
        results["per_input"].append({"input_idx": i, "max_abs_diff": diff})
        results["max_abs_diff"] = max(results["max_abs_diff"], diff)

        if diff > atol:
            results["passed"] = False

    if not results["passed"]:
        raise RuntimeError(
            f"InstrumentedResNet output differs from reference model. "
            f"Max abs diff: {results['max_abs_diff']:.2e}, tolerance: {atol:.2e}. "
            f"Cannot proceed with profiling."
        )

    return results
