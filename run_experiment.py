"""Main entry point for the RQ1.1 benchmark experiment."""

import os
import sys
import logging
import argparse
import subprocess

from src.models.validation import validate_equivalence
from src.benchmark.config import load_config
from src.benchmark.runner import BenchmarkRunner


def main():
    parser = argparse.ArgumentParser(
        description="RQ1.1: Coarse-boundary screening benchmark"
    )
    parser.add_argument("--config", default="configs/rq1_1.yaml",
                        help="Path to experiment config YAML")
    parser.add_argument("--output-dir", default=None,
                        help="Override output directory")
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="Run run_analysis.py automatically after the benchmark completes",
    )
    parser.add_argument(
        "--analysis-output-dir",
        default=None,
        help="Optional output directory for derived analysis artifacts",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("rq1_1")

    config = load_config(args.config)

    # --- Phase 1: Functional equivalence (mandatory precondition) ---
    # Extract split points from configured conditions
    split_points = [
        c.split_after for c in config.conditions
        if c.type == "split" and c.split_after is not None
    ]

    logger.info("Validating functional equivalence (local path)...")
    logger.info(f"  Split points: {split_points}")
    logger.info(f"  Tolerance: {config.parity_atol}")
    logger.info(f"  Validation inputs: {config.parity_num_inputs}")

    parity_results = validate_equivalence(
        split_points=split_points,
        atol=config.parity_atol,
        num_inputs=config.parity_num_inputs,
    )

    parity_pass = True
    for split, info in parity_results.items():
        status = "PASS" if info["match"] else "FAIL"
        logger.info(f"  {split}: {status}  (max_abs_diff={info['max_abs_diff']:.2e})")
        if not info["match"]:
            parity_pass = False

    if not parity_pass:
        logger.error("Parity validation FAILED. Benchmark will not proceed.")
        sys.exit(1)

    logger.info("All local parity checks passed.")

    # --- Phase 2: Benchmark ---
    runner = BenchmarkRunner(config, args.config, args.output_dir)
    # Pass parity results so the runner can save them and run gRPC validation
    runner.parity_local_results = parity_results
    runner.run()

    if args.run_analysis:
        analysis_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "run_analysis.py",
        )
        results_dir = os.path.abspath(runner.output_dir)
        analysis_cmd = [sys.executable, analysis_script, results_dir]
        if args.analysis_output_dir:
            analysis_cmd.extend(["--output-dir", args.analysis_output_dir])

        logger.info(
            "Experiment finished. Running post-experiment analysis for %s",
            results_dir,
        )
        try:
            subprocess.run(analysis_cmd, check=True)
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Post-experiment analysis failed with exit code %s",
                exc.returncode,
            )
            sys.exit(exc.returncode)
        logger.info("Post-experiment analysis complete.")
    else:
        logger.info("Experiment finished. Run run_analysis.py on the results directory.")


if __name__ == "__main__":
    main()
