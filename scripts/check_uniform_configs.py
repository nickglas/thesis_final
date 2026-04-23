from __future__ import annotations

from pathlib import Path
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

THESIS_CONFIGS = {
    "RQ1.1": REPO_ROOT / "configs" / "rq1" / "1.1" / "rq1_1_fully_controlled.yaml",
    "RQ1.2": REPO_ROOT / "configs" / "rq1" / "1.2" / "rq1_2_fully_controlled.yaml",
    "RQ1.4": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4_fully_controlled.yaml",
    "RQ1.5": REPO_ROOT / "configs" / "rq1" / "1.5" / "rq1_5_full.yaml",
}

EXCLUDED_CONFIGS = {
    "Internal timing": REPO_ROOT / "configs" / "internal_timing" / "timing_full.yaml",
    "RQ1.1 experimental": REPO_ROOT / "configs" / "rq1" / "1.1" / "rq1_1_experimental.yaml",
    "RQ1.1 threaded": REPO_ROOT / "configs" / "rq1" / "1.1" / "rq1_1_threaded.yaml",
    "RQ1.2 experimental": REPO_ROOT / "configs" / "rq1" / "1.2" / "rq1_2_experimental.yaml",
    "RQ1.4 experimental": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4_experimental.yaml",
    "RQ1.4 threaded": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4_threaded.yaml",
    "RQ1.4 smoke": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4_smoke_test.yaml",
    "RQ1.5 smoke": REPO_ROOT / "configs" / "rq1" / "1.5" / "rq1_5_smoke.yaml",
}

SHARED_FIELDS = [
    "model.name",
    "model.pretrained",
    "model.device",
    "model.input_shape",
    "model.precision",
    "benchmark.rounds",
    "benchmark.warmup_iterations",
    "benchmark.measured_iterations",
    "benchmark.cooldown_seconds",
    "benchmark.seed",
    "grpc.port",
    "grpc.max_message_bytes",
    "carry_forward.near_best_window_pct",
    "carry_forward.degeneracy_threshold_pct",
    "parity.atol",
    "parity.num_inputs",
    "warmup_calibration.window",
    "warmup_calibration.cv_threshold",
    "cpu_stabilisation.threading.pytorch_intra_op",
    "cpu_stabilisation.threading.pytorch_inter_op",
    "cpu_stabilisation.threading.omp_num_threads",
    "cpu_stabilisation.threading.mkl_num_threads",
    "cpu_stabilisation.threading.openblas_num_threads",
    "cpu_stabilisation.affinity.enabled",
    "cpu_stabilisation.affinity.num_cores",
    "cpu_stabilisation.affinity.avoid_smt",
    "cpu_stabilisation.priority.enabled",
    "cpu_stabilisation.priority.nice_value",
]

RQ14_RQ15_CHAIN_FIELDS = [
    "benchmark.rounds",
    "benchmark.warmup_iterations",
    "benchmark.measured_iterations",
    "benchmark.cooldown_seconds",
    "benchmark.seed",
    "parity.atol",
    "parity.num_inputs",
    "warmup_calibration.window",
    "warmup_calibration.cv_threshold",
    "cpu_stabilisation.threading.pytorch_intra_op",
    "cpu_stabilisation.threading.pytorch_inter_op",
    "cpu_stabilisation.threading.omp_num_threads",
    "cpu_stabilisation.threading.mkl_num_threads",
    "cpu_stabilisation.threading.openblas_num_threads",
]

RQ15_PLATFORM_DIFFERENCES = [
    "cpu_stabilisation.governor.set_governor",
    "cpu_stabilisation.turbo.disable_turbo",
    "kubernetes.namespace",
    "kubernetes.image_pull_policy",
    "kubernetes.resources.memory_request",
    "kubernetes.resources.memory_limit",
    "kubernetes.client_resources.cpu_request",
    "kubernetes.client_resources.cpu_limit",
]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def get_path(data: dict, dotted_path: str):
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def format_value(value) -> str:
    if isinstance(value, list):
        return str(value)
    return str(value)


def check_shared_fields(configs: dict[str, dict], fields: list[str]) -> list[str]:
    errors: list[str] = []
    labels = list(configs)
    baseline_label = labels[0]
    baseline = configs[baseline_label]

    for dotted_path in fields:
        baseline_value = get_path(baseline, dotted_path)
        mismatches = []
        for label in labels[1:]:
            current_value = get_path(configs[label], dotted_path)
            if current_value != baseline_value:
                mismatches.append(
                    f"{label}={format_value(current_value)} vs {baseline_label}={format_value(baseline_value)}"
                )
        if mismatches:
            errors.append(f"{dotted_path}: " + "; ".join(mismatches))

    return errors


def chain_signature(config: dict) -> list[tuple[str, tuple[str, ...]]]:
    signature = []
    for condition in config["conditions"]:
        if condition["type"] != "chain":
            continue
        signature.append(
            (condition["name"], tuple(condition.get("chain_split_points") or []))
        )
    return signature


def print_section(title: str) -> None:
    print(title)
    print("-" * len(title))


def main() -> int:
    thesis_configs = {label: load_yaml(path) for label, path in THESIS_CONFIGS.items()}

    print_section("Uniform Config Audit")
    print("Comparable thesis-facing configs:")
    for label, path in THESIS_CONFIGS.items():
        print(f"- {label}: {path.relative_to(REPO_ROOT).as_posix()}")
    print()

    shared_errors = check_shared_fields(thesis_configs, SHARED_FIELDS)
    if shared_errors:
        print("Shared benchmark contract: FAIL")
        for error in shared_errors:
            print(f"- {error}")
        print()
    else:
        print("Shared benchmark contract: PASS")
        print("- RQ1.1, RQ1.2, RQ1.4, and RQ1.5 share the same model, benchmark cadence, parity settings, warmup calibration, and single-threaded CPU profile.")
        print()

    rq14 = thesis_configs["RQ1.4"]
    rq15 = thesis_configs["RQ1.5"]
    rq14_rq15_errors = check_shared_fields({"RQ1.4": rq14, "RQ1.5": rq15}, RQ14_RQ15_CHAIN_FIELDS)
    rq14_chain = chain_signature(rq14)
    rq15_chain = chain_signature(rq15)

    print("RQ1.4/RQ1.5 chain-family alignment:")
    if rq14_rq15_errors:
        print("- FAIL: shared chain benchmark fields drifted.")
        for error in rq14_rq15_errors:
            print(f"- {error}")
    elif rq14_chain != rq15_chain:
        print("- FAIL: chain condition sets differ.")
        print(f"- RQ1.4: {rq14_chain}")
        print(f"- RQ1.5: {rq15_chain}")
    else:
        print("- PASS: RQ1.4 and RQ1.5 use the same five chain conditions and the same shared timing/parity parameters.")
    print()

    print("Intentional RQ1.5 platform-specific differences:")
    for dotted_path in RQ15_PLATFORM_DIFFERENCES:
        print(
            f"- {dotted_path}: RQ1.4={format_value(get_path(rq14, dotted_path))}; "
            f"RQ1.5={format_value(get_path(rq15, dotted_path))}"
        )
    print("- kubernetes.image: RQ1.4 uses a local tag; RQ1.5 requires a pinned ACR digest for reproducible AKS pulls.")
    print()

    print("Not directly comparable with the thesis-facing benchmark set:")
    for label, path in EXCLUDED_CONFIGS.items():
        print(f"- {label}: {path.relative_to(REPO_ROOT).as_posix()}")
    print("- These configs are exploratory, threaded, or smoke-test profiles and should not be mixed with the frozen fully controlled runs.")
    print()

    print("Verdict:")
    if shared_errors or rq14_rq15_errors or rq14_chain != rq15_chain:
        print("- The thesis-facing configs are not uniform enough for direct comparison. Fix the failures above before running the experiments.")
        return 1

    print("- The thesis-facing configs are uniform on the core measurement contract.")
    print("- RQ1.5 still has documented AKS-specific control differences, so it is comparable to RQ1.4 by design, not bit-for-bit identical at the host-control level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())