"""Experiment configuration loading and dataclasses."""

import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConditionConfig:
    name: str
    type: str           # "monolithic" or "split"
    split_after: Optional[str] = None


@dataclass
class ThreadingConfig:
    """Thread-count settings for PyTorch, OpenMP, MKL, and OpenBLAS."""
    pytorch_intra_op: int = 4
    pytorch_inter_op: int = 1
    omp_num_threads: int = 4
    mkl_num_threads: int = 4
    openblas_num_threads: int = 4


@dataclass
class AffinityConfig:
    """CPU core-pinning settings."""
    enabled: bool = True
    num_cores: int = 4
    avoid_smt: bool = True
    explicit_cpus: Optional[List[int]] = None


@dataclass
class PriorityConfig:
    """Process priority (nice) settings."""
    enabled: bool = True
    nice_value: int = -5


@dataclass
class GovernorConfig:
    """CPU frequency governor settings."""
    set_governor: bool = False
    requested_mode: str = "performance"


@dataclass
class TurboConfig:
    """Turbo boost control settings."""
    disable_turbo: bool = False


@dataclass
class CpuStabilisationConfig:
    """Top-level CPU stabilisation configuration."""
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    affinity: AffinityConfig = field(default_factory=AffinityConfig)
    priority: PriorityConfig = field(default_factory=PriorityConfig)
    governor: GovernorConfig = field(default_factory=GovernorConfig)
    turbo: TurboConfig = field(default_factory=TurboConfig)


@dataclass
class ThreadingConfig:
    """Thread-count settings for PyTorch, OpenMP, MKL, and OpenBLAS."""
    pytorch_intra_op: int = 4
    pytorch_inter_op: int = 1
    omp_num_threads: int = 4
    mkl_num_threads: int = 4
    openblas_num_threads: int = 4


@dataclass
class AffinityConfig:
    """CPU core-pinning settings."""
    enabled: bool = True
    num_cores: int = 4
    avoid_smt: bool = True
    explicit_cpus: Optional[List[int]] = None


@dataclass
class PriorityConfig:
    """Process priority (nice) settings."""
    enabled: bool = True
    nice_value: int = -5


@dataclass
class GovernorConfig:
    """CPU frequency governor settings."""
    set_governor: bool = False
    requested_mode: str = "performance"


@dataclass
class TurboConfig:
    """Turbo boost control settings."""
    disable_turbo: bool = False


@dataclass
class CpuStabilisationConfig:
    """Top-level CPU stabilisation configuration."""
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    affinity: AffinityConfig = field(default_factory=AffinityConfig)
    priority: PriorityConfig = field(default_factory=PriorityConfig)
    governor: GovernorConfig = field(default_factory=GovernorConfig)
    turbo: TurboConfig = field(default_factory=TurboConfig)


@dataclass
class ExperimentConfig:
    # Experiment metadata
    experiment_name: str
    experiment_description: str

    # Model
    model_name: str
    pretrained: bool
    device: str
    input_shape: List[int]
    precision: str

    # Conditions
    conditions: List[ConditionConfig]

    # Benchmark
    rounds: int
    warmup_iterations: int
    measured_iterations: int
    cooldown_seconds: int
    seed: int

    # gRPC
    grpc_host: str
    grpc_port: int
    grpc_max_message_bytes: int

    # Carry-forward
    near_best_window_pct: float
    degeneracy_threshold_pct: float

    # Parity validation
    parity_atol: float = 1e-5
    parity_num_inputs: int = 5

    # Warmup calibration
    warmup_calibration_window: int = 10
    warmup_calibration_cv_threshold: float = 0.02

    # CPU stabilisation
    cpu_stabilisation: CpuStabilisationConfig = field(
        default_factory=CpuStabilisationConfig
    )


def load_config(path: str) -> ExperimentConfig:
    """Load experiment configuration from a YAML file."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    conditions = []
    for c in raw["conditions"]:
        conditions.append(ConditionConfig(
            name=c["name"],
            type=c["type"],
            split_after=c.get("split_after"),
        ))

    # Parse cpu_stabilisation section
    stab_raw = raw.get("cpu_stabilisation", {})
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

    return ExperimentConfig(
        experiment_name=raw["experiment"]["name"],
        experiment_description=raw["experiment"]["description"],
        model_name=raw["model"]["name"],
        pretrained=raw["model"]["pretrained"],
        device=raw["model"]["device"],
        input_shape=raw["model"]["input_shape"],
        precision=raw["model"]["precision"],
        conditions=conditions,
        rounds=raw["benchmark"]["rounds"],
        warmup_iterations=raw["benchmark"]["warmup_iterations"],
        measured_iterations=raw["benchmark"]["measured_iterations"],
        cooldown_seconds=raw["benchmark"]["cooldown_seconds"],
        seed=raw["benchmark"]["seed"],
        grpc_host=raw["grpc"]["host"],
        grpc_port=raw["grpc"]["port"],
        grpc_max_message_bytes=raw["grpc"]["max_message_bytes"],
        near_best_window_pct=raw["carry_forward"]["near_best_window_pct"],
        degeneracy_threshold_pct=raw["carry_forward"]["degeneracy_threshold_pct"],
        parity_atol=raw.get("parity", {}).get("atol", 1e-5),
        parity_num_inputs=raw.get("parity", {}).get("num_inputs", 5),
        warmup_calibration_window=raw.get("warmup_calibration", {}).get("window", 10),
        warmup_calibration_cv_threshold=raw.get("warmup_calibration", {}).get("cv_threshold", 0.02),
        cpu_stabilisation=cpu_stab,
    )
