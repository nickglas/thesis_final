"""Main entry point for the RQ1.1 benchmark experiment."""

import sys
import logging
import argparse

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

    logger.info("Experiment finished. Run run_analysis.py on the results directory.")


if __name__ == "__main__":
    main()
