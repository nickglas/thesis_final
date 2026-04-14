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
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip functional-equivalence check")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("rq1_1")

    # --- Phase 1: Functional equivalence (precondition) ---
    if not args.skip_validation:
        logger.info("Validating functional equivalence of split configurations...")
        results = validate_equivalence()
        for split, info in results.items():
            status = "PASS" if info["match"] else "FAIL"
            logger.info(f"  {split}: {status}  (max_abs_diff={info['max_abs_diff']:.2e})")
            if not info["match"]:
                logger.error(f"Equivalence check FAILED for {split}. Aborting.")
                sys.exit(1)
        logger.info("All equivalence checks passed.")

    # --- Phase 2: Benchmark ---
    config = load_config(args.config)
    runner = BenchmarkRunner(config, args.config, args.output_dir)
    runner.run()

    logger.info("Experiment finished. Run run_analysis.py on the results directory.")


if __name__ == "__main__":
    main()
