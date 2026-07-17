"""Experiment configuration loading, dataclasses, and K8s naming helpers."""

import re
import yaml
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConditionConfig:
    name: str
    type: str           # "monolithic", "split", or "chain"
    split_after: Optional[str] = None
    chain_split_points: Optional[List[str]] = None


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
class K8sResourceConfig:
    """Pod resource requests/limits for Kubernetes deployments.

    When requests == limits, the pod receives Guaranteed QoS class,
    which is the strongest scheduling guarantee Kubernetes offers.
    """
    cpu_request: str = "4"
    cpu_limit: str = "4"
    memory_request: str = "1Gi"
    memory_limit: str = "1Gi"


@dataclass
class K8sPlacementConfig:
    """Explicit placement controls for Kubernetes benchmark pods.

    Strategies:
      - "none" / "prefer_same_node" / "strict_same_node": single-node colocation
        (existing behaviour for RQ1.4 and RQ1.5 thesis-facing primary runs).
      - "multi_node_anti_affinity": forces every chain segment plus the client
        onto distinct nodes via pod anti-affinity. Used by RQ1.4b/1.5b multi-node
        sensitivity stages so every gRPC hop crosses a node boundary.
    """
    strategy: str = "none"
    require_same_node: bool = False
    fail_if_not_colocated: bool = False
    node_selector: Dict[str, str] = field(default_factory=dict)
    node_pool: Optional[str] = None
    tolerations: List[Dict[str, Any]] = field(default_factory=list)
    require_control_plane_isolation: bool = False
    min_nodes: Optional[int] = None
    require_distinct_nodes: bool = False
    require_dedicated_client_node: bool = False


@dataclass
class K8sConfig:
    """Kubernetes deployment configuration for RQ1.4+ experiments."""
    namespace: str = "rq14"
    service_name_template: str = "{condition}-svc-{index}"
    grpc_port: int = 50051
    max_message_bytes: int = 16 * 1024 * 1024
    readiness_timeout: float = 60.0
    image: str = "thesis-inference:latest"
    image_pull_policy: str = "IfNotPresent"
    resources: K8sResourceConfig = field(default_factory=K8sResourceConfig)
    client_resources: K8sResourceConfig = field(default_factory=K8sResourceConfig)
    placement: K8sPlacementConfig = field(default_factory=K8sPlacementConfig)


def sanitize_k8s_name_component(value: str) -> str:
    """Convert an arbitrary identifier into a DNS-safe K8s name component."""
    sanitized = value.lower().replace("_", "-")
    sanitized = re.sub(r"[^a-z0-9-]", "-", sanitized)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "default"


def format_k8s_service_name(template: str, condition_name: str, index: int) -> str:
    """Format a K8s resource/service name using the sanitized condition form."""
    return template.format(
        condition=sanitize_k8s_name_component(condition_name),
        index=index,
    )

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

    # gRPC (only used by the local split runner; chain/K8s configs may omit it)
    grpc_host: str = "127.0.0.1"
    grpc_port: int = 50051
    grpc_max_message_bytes: int = 16 * 1024 * 1024

    # Carry-forward (only meaningful for RQ1.1/RQ1.2; chain configs may omit it)
    near_best_window_pct: float = 5.0
    degeneracy_threshold_pct: float = 10.0

    # Parity validation
    parity_atol: float = 1e-5
    parity_num_inputs: int = 5

    # Warmup calibration
    warmup_calibration_window: int = 10
    warmup_calibration_cv_threshold: float = 0.02
    warmup_calibration_max_extra_iterations: int = -1

    # CPU stabilisation
    cpu_stabilisation: CpuStabilisationConfig = field(
        default_factory=CpuStabilisationConfig
    )

    # Kubernetes (optional, for RQ1.4+ chain experiments)
    kubernetes: Optional[K8sConfig] = None


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
            chain_split_points=c.get("chain_split_points"),
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

    grpc_raw = raw.get("grpc") or {}
    carry_forward_raw = raw.get("carry_forward") or {}

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
        grpc_host=grpc_raw.get("host", "127.0.0.1"),
        grpc_port=grpc_raw.get("port", 50051),
        grpc_max_message_bytes=grpc_raw.get("max_message_bytes", 16 * 1024 * 1024),
        near_best_window_pct=carry_forward_raw.get("near_best_window_pct", 5.0),
        degeneracy_threshold_pct=carry_forward_raw.get("degeneracy_threshold_pct", 10.0),
        parity_atol=raw.get("parity", {}).get("atol", 1e-5),
        parity_num_inputs=raw.get("parity", {}).get("num_inputs", 5),
        warmup_calibration_window=raw.get("warmup_calibration", {}).get("window", 10),
        warmup_calibration_cv_threshold=raw.get("warmup_calibration", {}).get("cv_threshold", 0.02),
        warmup_calibration_max_extra_iterations=raw.get("warmup_calibration", {}).get("max_extra_iterations", -1),
        cpu_stabilisation=cpu_stab,
        kubernetes=_parse_k8s_config(raw.get("kubernetes")),
    )


def _parse_k8s_config(raw) -> Optional[K8sConfig]:
    if raw is None:
        return None
    res_raw = raw.get("resources", {})
    resources = K8sResourceConfig(
        cpu_request=str(res_raw.get("cpu_request", "4")),
        cpu_limit=str(res_raw.get("cpu_limit", "4")),
        memory_request=str(res_raw.get("memory_request", "1Gi")),
        memory_limit=str(res_raw.get("memory_limit", "1Gi")),
    )
    client_res_raw = raw.get("client_resources", res_raw)
    client_resources = K8sResourceConfig(
        cpu_request=str(client_res_raw.get("cpu_request", resources.cpu_request)),
        cpu_limit=str(client_res_raw.get("cpu_limit", resources.cpu_limit)),
        memory_request=str(client_res_raw.get("memory_request", resources.memory_request)),
        memory_limit=str(client_res_raw.get("memory_limit", resources.memory_limit)),
    )
    placement_raw = raw.get("placement", {}) or {}
    node_selector_raw = placement_raw.get("node_selector", {}) or {}
    tolerations_raw = placement_raw.get("tolerations", []) or []
    tolerations: List[Dict[str, Any]] = []
    if isinstance(tolerations_raw, list):
        for item in tolerations_raw:
            if not isinstance(item, dict):
                continue
            toleration: Dict[str, Any] = {}
            for key, value in item.items():
                if value in (None, ""):
                    continue
                if key == "tolerationSeconds":
                    toleration[str(key)] = value
                else:
                    toleration[str(key)] = str(value)
            if toleration:
                tolerations.append(toleration)
    min_nodes_raw = placement_raw.get("min_nodes")
    min_nodes = (
        int(min_nodes_raw)
        if min_nodes_raw not in (None, "")
        else None
    )
    placement = K8sPlacementConfig(
        strategy=str(placement_raw.get("strategy", "none")),
        require_same_node=bool(placement_raw.get("require_same_node", False)),
        fail_if_not_colocated=bool(placement_raw.get("fail_if_not_colocated", False)),
        node_selector={
            str(key): str(value)
            for key, value in node_selector_raw.items()
        },
        node_pool=(
            str(placement_raw.get("node_pool"))
            if placement_raw.get("node_pool") not in (None, "")
            else None
        ),
        tolerations=tolerations,
        require_control_plane_isolation=bool(
            placement_raw.get("require_control_plane_isolation", False)
        ),
        min_nodes=min_nodes,
        require_distinct_nodes=bool(
            placement_raw.get("require_distinct_nodes", False)
        ),
        require_dedicated_client_node=bool(
            placement_raw.get("require_dedicated_client_node", False)
        ),
    )
    return K8sConfig(
        namespace=raw.get("namespace", "rq14"),
        service_name_template=raw.get("service_name_template", "{condition}-svc-{index}"),
        grpc_port=raw.get("grpc_port", 50051),
        max_message_bytes=raw.get("max_message_bytes", 16 * 1024 * 1024),
        readiness_timeout=raw.get("readiness_timeout", 60.0),
        image=raw.get("image", "thesis-inference:latest"),
        image_pull_policy=raw.get("image_pull_policy", "IfNotPresent"),
        resources=resources,
        client_resources=client_resources,
        placement=placement,
    )
