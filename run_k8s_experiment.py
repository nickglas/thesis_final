"""Entry point for RQ1.4 Kubernetes chain benchmark experiments.

Usage:
    python run_k8s_experiment.py --config configs/rq1/1.4/rq1_4_smoke_test.yaml

Performs:
    Phase 1 — Local segment parity validation (pre-deployment check)
    Phase 2 — K8s benchmark (assumes services already deployed)
"""

import os
import sys
import logging
import argparse
import subprocess

import torch
import numpy as np

from src.benchmark.config import load_config
from src.benchmark.k8s_runner import K8sBenchmarkRunner
from src.models.resnet_splits import get_full_model, get_chain_segments


def _is_running_in_kubernetes() -> bool:
    """Best-effort detection of whether this process is running in a pod."""
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True
    return os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace")


def _assert_in_cluster_execution(config, config_path: str, logger):
    """Fail fast if the K8s benchmark phase is started from outside cluster."""
    if _is_running_in_kubernetes():
        return

    namespace = config.kubernetes.namespace
    logger.error(
        "Phase 2 must run from inside the Kubernetes cluster. "
        "This process is running outside the cluster, so ClusterIP DNS names "
        "like '*.svc.cluster.local' will not resolve from the host."
    )
    logger.error(
        "Run instead: kubectl exec -it -n %s benchmark-client -- "
        "python run_k8s_experiment.py --config %s",
        namespace,
        config_path,
    )
    sys.exit(1)


def _validate_chain_segments_local(config, logger):
    """Phase 1: Validate that chaining segments locally reproduces monolithic output.

    This is a pre-deployment sanity check that runs entirely in-process.
    Fail-closed: any mismatch aborts the experiment.
    """
    model = get_full_model()
    rng = np.random.RandomState(config.seed)

    results = {}
    seen_split_sets = set()

    for cond in config.conditions:
        if cond.type != "chain":
            continue
        split_key = tuple(cond.chain_split_points or [])
        if split_key in seen_split_sets:
            continue
        seen_split_sets.add(split_key)

        split_points = list(split_key)
        segments = get_chain_segments(split_points)

        all_match = True
        max_diff = 0.0

        for _ in range(config.parity_num_inputs):
            inp = torch.from_numpy(
                rng.randn(1, 3, 224, 224).astype(np.float32)
            )
            with torch.no_grad():
                mono_out = model(inp)
                out = inp
                for seg in segments:
                    out = seg(out)

            diff = (mono_out - out).abs().max().item()
            max_diff = max(max_diff, diff)
            if diff > config.parity_atol:
                all_match = False

        label = cond.name
        results[label] = {
            "match": all_match,
            "max_abs_diff": max_diff,
            "atol": config.parity_atol,
            "num_inputs": config.parity_num_inputs,
            "split_points": split_points,
            "num_segments": len(segments),
            "method": "local_chain_segments",
        }

        status = "PASS" if all_match else "FAIL"
        logger.info(
            f"  {label} ({len(segments)} segments): {status} "
            f"(max_abs_diff={max_diff:.2e})"
        )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="RQ1.4: K8s chain benchmark experiment"
    )
    parser.add_argument(
        "--config",
        default="configs/rq1/1.4/rq1_4_smoke_test.yaml",
        help="Path to experiment config YAML",
    )
    parser.add_argument("--output-dir", default=None,
                        help="Override output directory")
    parser.add_argument(
        "--skip-local-validation",
        action="store_true",
        help="Skip Phase 1 local segment validation (not recommended)",
    )
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Run run_analysis.py after the benchmark completes",
    )
    parser.add_argument(
        "--condition",
        default=None,
        help="Restrict the benchmark to a single condition name from the config",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("rq1_4")

    config = load_config(args.config)

    if args.condition is not None:
        selected_conditions = [
            cond for cond in config.conditions if cond.name == args.condition
        ]
        if not selected_conditions:
            logger.error(
                "Condition '%s' was not found in config %s",
                args.condition,
                args.config,
            )
            sys.exit(1)
        config.conditions = selected_conditions
        logger.info("Restricting benchmark run to condition: %s", args.condition)

    if config.kubernetes is None:
        logger.error(
            "Config file must include a 'kubernetes' section for K8s experiments."
        )
        sys.exit(1)

    # --- Phase 1: Local chain segment validation ---
    parity_results = {}
    if not args.skip_local_validation:
        logger.info("Phase 1: Local chain segment parity validation...")
        parity_results = _validate_chain_segments_local(config, logger)

        parity_pass = all(r["match"] for r in parity_results.values())
        if not parity_pass:
            logger.error(
                "Local chain segment validation FAILED. Experiment will not proceed."
            )
            sys.exit(1)
        logger.info("All local chain parity checks passed.")
    else:
        logger.warning("Skipping local validation (--skip-local-validation).")

    # --- Phase 2: K8s Benchmark ---
    _assert_in_cluster_execution(config, args.config, logger)
    logger.info("Phase 2: K8s chain benchmark...")
    runner = K8sBenchmarkRunner(config, args.config, args.output_dir)
    runner.parity_local_results = parity_results
    runner.run()
    results_dir = os.path.abspath(runner.output_dir)
    logger.info("Benchmark artifacts directory: %s", results_dir)
    if _is_running_in_kubernetes():
        logger.info(
            "This run executed inside a pod, so the results directory is pod-local. "
            "Copy it out with: kubectl cp %s/benchmark-client:%s <local-destination>",
            config.kubernetes.namespace,
            results_dir,
        )

    # --- Optional: post-experiment analysis ---
    if args.run_analysis:
        analysis_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "run_analysis.py",
        )
        logger.info(f"Running post-experiment analysis for {results_dir}")
        try:
            subprocess.run(
                [sys.executable, analysis_script, results_dir],
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(f"Analysis failed with exit code {exc.returncode}")
            sys.exit(exc.returncode)
    else:
        logger.info(
            "Experiment finished. Run run_analysis.py on %s or rerun with --run-analysis.",
            results_dir,
        )


if __name__ == "__main__":
    main()
