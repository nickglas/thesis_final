"""Configuration dataclass and loader for the internal timing mode.

Separate from the thesis-facing ExperimentConfig to avoid modifying
src/benchmark/config.py.  Reuses CpuStabilisationConfig and its
sub-dataclasses for CPU-behaviour controls.
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Optional

from src.benchmark.config import (
    CpuStabilisationConfig,
    ThreadingConfig,
    AffinityConfig,
    PriorityConfig,
    GovernorConfig,
    TurboConfig,
)


@dataclass
class TimingConfig:
    """Controls for the internal timing instrumentation."""
    level: str = "full"                 # stage | block | operation | full
    include_stem_ops: bool = True       # L3 operations inside stem
    include_timing_gaps: bool = True    # parent-vs-children consistency
    measure_overhead: bool = True       # compare instrumented vs plain forward


@dataclass
class BenchmarkConfig:
    """Measurement loop parameters."""
    rounds: int = 3
    warmup_iterations: int = 30
    measured_iterations: int = 100
    seed: int = 42


@dataclass
class ValidationConfig:
    """Functional-equivalence validation parameters."""
    num_inputs: int = 5
    atol: float = 1e-6


@dataclass
class WarmupCalibrationConfig:
    """Warmup stabilisation-check parameters."""
    window: int = 10
    cv_threshold: float = 0.02


@dataclass
class InternalTimingConfig:
    """Top-level configuration for the internal timing mode."""
    # Metadata
    experiment_name: str = "internal_timing_resnet18"
    experiment_description: str = ""

    # Model
    model_name: str = "resnet18"
    pretrained: bool = True
    device: str = "cpu"
    input_shape: List[int] = field(default_factory=lambda: [1, 3, 224, 224])
    precision: str = "fp32"

    # Timing
    timing: TimingConfig = field(default_factory=TimingConfig)

    # Benchmark
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)

    # Validation
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    # Warmup calibration
    warmup_calibration: WarmupCalibrationConfig = field(
        default_factory=WarmupCalibrationConfig
    )

    # CPU stabilisation (reused from existing config)
    cpu_stabilisation: CpuStabilisationConfig = field(
        default_factory=CpuStabilisationConfig
    )


def load_internal_timing_config(path: str) -> InternalTimingConfig:
    """Load internal timing configuration from a YAML file."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    exp = raw.get("experiment", {})
    model = raw.get("model", {})
    timing_raw = raw.get("timing", {})
    bench = raw.get("benchmark", {})
    val = raw.get("validation", {})
    warmup_raw = raw.get("warmup_calibration", {})
    stab_raw = raw.get("cpu_stabilisation", {})

    # Parse cpu_stabilisation sub-sections
    threading_raw = stab_raw.get("threading", {})
    affinity_raw = stab_raw.get("affinity", {})
    priority_raw = stab_raw.get("priority", {})
    governor_raw = stab_raw.get("governor", {})
    turbo_raw = stab_raw.get("turbo", {})

    cpu_stab = CpuStabilisationConfig(
        threading=ThreadingConfig(
            pytorch_intra_op=threading_raw.get("pytorch_intra_op", 4),
            pytorch_inter_op=threading_raw.get("pytorch_inter_op", 1),
            omp_num_threads=threading_raw.get("omp_num_threads", 4),
            mkl_num_threads=threading_raw.get("mkl_num_threads", 4),
            openblas_num_threads=threading_raw.get("openblas_num_threads", 4),
        ),
        affinity=AffinityConfig(
            enabled=affinity_raw.get("enabled", True),
            num_cores=affinity_raw.get("num_cores", 4),
            avoid_smt=affinity_raw.get("avoid_smt", True),
            explicit_cpus=affinity_raw.get("explicit_cpus", None),
        ),
        priority=PriorityConfig(
            enabled=priority_raw.get("enabled", True),
            nice_value=priority_raw.get("nice_value", -5),
        ),
        governor=GovernorConfig(
            set_governor=governor_raw.get("set_governor", False),
            requested_mode=governor_raw.get("requested_mode", "performance"),
        ),
        turbo=TurboConfig(
            disable_turbo=turbo_raw.get("disable_turbo", False),
        ),
    )

    return InternalTimingConfig(
        experiment_name=exp.get("name", "internal_timing_resnet18"),
        experiment_description=exp.get("description", ""),
        model_name=model.get("name", "resnet18"),
        pretrained=model.get("pretrained", True),
        device=model.get("device", "cpu"),
        input_shape=model.get("input_shape", [1, 3, 224, 224]),
        precision=model.get("precision", "fp32"),
        timing=TimingConfig(
            level=timing_raw.get("level", "full"),
            include_stem_ops=timing_raw.get("include_stem_ops", True),
            include_timing_gaps=timing_raw.get("include_timing_gaps", True),
            measure_overhead=timing_raw.get("measure_overhead", True),
        ),
        benchmark=BenchmarkConfig(
            rounds=bench.get("rounds", 3),
            warmup_iterations=bench.get("warmup_iterations", 30),
            measured_iterations=bench.get("measured_iterations", 100),
            seed=bench.get("seed", 42),
        ),
        validation=ValidationConfig(
            num_inputs=val.get("num_inputs", 5),
            atol=val.get("atol", 1e-6),
        ),
        warmup_calibration=WarmupCalibrationConfig(
            window=warmup_raw.get("window", 10),
            cv_threshold=warmup_raw.get("cv_threshold", 0.02),
        ),
        cpu_stabilisation=cpu_stab,
    )
