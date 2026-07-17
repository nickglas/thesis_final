"""Entry point for the exploratory internal timing mode.

Profiles the internal compute distribution of ResNet-18 using an
instrumented forward path.  Completely separate from the thesis-facing
split benchmark entry point (run_experiment.py).

Usage:
    python run_internal_timing.py --config configs/internal_timing/timing_full.yaml
    python run_internal_timing.py --config configs/internal_timing/timing_smoke_test.yaml --run-analysis
"""

import argparse
import datetime
import logging
import os
import sys

from src.benchmark.internal_timing_config import load_internal_timing_config
from src.benchmark.internal_timing_runner import InternalTimingRunner


def main():
    parser = argparse.ArgumentParser(
        description="Internal timing mode: profile ResNet-18 compute distribution"
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to internal timing YAML config file"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory (default: results/internal_timing_<timestamp>)"
    )
    parser.add_argument(
        "--run-analysis", action="store_true",
        help="Run analysis and generate report after profiling"
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load config
    config = load_internal_timing_config(args.config)
    logger.info(f"Loaded config: {config.experiment_name}")

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = config.experiment_name.replace(" ", "_")
        output_dir = os.path.join("results", f"{prefix}_{timestamp}")

    logger.info(f"Output directory: {output_dir}")

    # Run benchmark
    runner = InternalTimingRunner(config, args.config, output_dir)
    results_dir = runner.run()
    logger.info(f"Benchmark complete. Results in: {results_dir}")

    # Optionally run analysis
    if args.run_analysis:
        logger.info("Running analysis...")
        from src.analysis.internal_timing_analysis import generate_report
        report_path = generate_report(results_dir, config)
        logger.info(f"Report generated: {report_path}")

    logger.info("Done.")


if __name__ == "__main__":
    main()
