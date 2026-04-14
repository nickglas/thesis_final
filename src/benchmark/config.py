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
    )
