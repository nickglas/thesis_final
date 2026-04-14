"""Post-experiment analysis for RQ1.1 results.

Reads raw_iterations.csv, computes all statistics, applies the
carry-forward rule, generates plots, and writes a summary report.
"""

import os
import argparse
import logging

from src.benchmark.config import load_config
from src.analysis.statistics import (
    load_raw_iterations,
    compute_condition_summary,
    compute_round_summaries,
    compute_cross_condition,
    compute_effect_sizes,
    apply_carry_forward_rule,
)
from src.analysis.plots import generate_all_plots
from src.benchmark.logging import ArtifactLogger


def main():
    parser = argparse.ArgumentParser(
        description="Analyse RQ1.1 benchmark results"
    )
    parser.add_argument("results_dir",
                        help="Path to results directory (e.g. results/rq1_1_20260414_...)")
    parser.add_argument("--config", default=None,
                        help="Config YAML (defaults to results_dir/config.yaml)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("rq1_1_analysis")

    results_dir = args.results_dir
    config_path = args.config or os.path.join(results_dir, "config.yaml")
    config = load_config(config_path)
    artifact = ArtifactLogger(results_dir)

    # ----- Load raw data -----
    raw_path = os.path.join(results_dir, "raw_iterations.csv")
    rows = load_raw_iterations(raw_path)
    logger.info(f"Loaded {len(rows)} raw iterations from {raw_path}")

    # ----- Per-condition summaries -----
    conditions = []
    seen = set()
    for r in rows:
        if r["condition"] not in seen:
            conditions.append(r["condition"])
            seen.add(r["condition"])

    summaries = []
    for cond in conditions:
        s = compute_condition_summary(rows, cond)
        summaries.append(s)
        logger.info(
            f"  {cond}: mean={s['mean_ms']:.3f} ms  "
            f"std={s['std_ms']:.3f} ms  "
            f"CI=[{s['ci95_lower_ms']:.3f}, {s['ci95_upper_ms']:.3f}]"
        )
    artifact.save_csv("condition_summaries.csv", summaries)

    # ----- Per-round summaries -----
    round_sums = compute_round_summaries(rows)
    artifact.save_csv("round_summaries.csv", round_sums)

    # ----- Cross-condition comparisons -----
    cross = compute_cross_condition(summaries)
    artifact.save_csv("cross_condition.csv", cross)
    for cc in cross:
        logger.info(
            f"  {cc['condition']}: overhead={cc['overhead_ms']:.3f} ms "
            f"({cc['overhead_pct']:.1f}%)"
        )

    # ----- Effect sizes -----
    effects = compute_effect_sizes(rows, summaries)
    artifact.save_csv("effect_sizes.csv", effects)

    # ----- Carry-forward selection -----
    carry_forward = apply_carry_forward_rule(
        summaries, cross,
        config.near_best_window_pct,
        config.degeneracy_threshold_pct,
    )
    artifact.save_json("carry_forward.json", carry_forward)
    logger.info("Carry-forward selection:")
    logger.info(f"  Raw fastest:        {carry_forward['raw_fastest']}")
    logger.info(f"  Selected main:      {carry_forward['selected_main']}")
    logger.info(f"  Selected reference: {carry_forward['selected_reference']}")
    logger.info(f"  Rejected:           {carry_forward['rejected']}")

    # ----- Plots -----
    generate_all_plots(results_dir)
    logger.info("Plots generated")

    # ----- Summary report -----
    _generate_report(results_dir, summaries, cross, effects, carry_forward)
    logger.info(f"Analysis complete. All artifacts in {results_dir}")


# ------------------------------------------------------------------

def _generate_report(results_dir, summaries, cross, effects, carry_forward):
    """Write a Markdown summary report."""
    lines = [
        "# RQ1.1 Experiment Report\n",
        "## Condition Summaries\n",
        "| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['condition']} | {s['n']} | {s['mean_ms']:.3f} | "
            f"{s['median_ms']:.3f} | {s['std_ms']:.3f} | {s['p95_ms']:.3f} | "
            f"[{s['ci95_lower_ms']:.3f}, {s['ci95_upper_ms']:.3f}] |"
        )

    lines.extend(["\n## Overhead vs Monolithic\n"])
    if cross:
        lines.append(
            "| Condition | Overhead (ms) | Overhead (%) "
            "| Activation (KB) | Boundary Crossing (ms) |"
        )
        lines.append("|---|---|---|---|---|")
        for cc in cross:
            lines.append(
                f"| {cc['condition']} | {cc['overhead_ms']:.3f} | "
                f"{cc['overhead_pct']:.1f}% | "
                f"{cc['activation_bytes'] / 1024:.1f} | "
                f"{cc['boundary_crossing_ms']:.3f} |"
            )

    lines.extend(["\n## Effect Sizes\n"])
    if effects:
        lines.append("| Condition | Cohen's d | Mann-Whitney U | p-value |")
        lines.append("|---|---|---|---|")
        for e in effects:
            lines.append(
                f"| {e['condition']} | {e['cohens_d']:.3f} | "
                f"{e['mann_whitney_u']:.1f} | {e['mann_whitney_p']:.2e} |"
            )

    lines.extend([
        "\n## Carry-Forward Selection\n",
        f"- **Raw fastest boundary:** {carry_forward['raw_fastest']} "
        f"({carry_forward['raw_fastest_mean_ms']:.3f} ms)",
        f"- **Near-best window:** {carry_forward['near_best_window_pct']}% "
        f"→ threshold {carry_forward['near_best_threshold_ms']:.3f} ms",
        f"- **Near-best candidates:** "
        f"{', '.join(carry_forward['near_best_candidates'])}",
        f"- **Degenerate candidates:** "
        f"{', '.join(carry_forward['degenerate_candidates']) or 'None'}",
    ])

    if carry_forward["selected_main"]:
        lines.append(
            f"- **Selected main candidate:** {carry_forward['selected_main']} "
            f"({carry_forward['selected_main_mean_ms']:.3f} ms)"
        )
    else:
        lines.append("- **Selected main candidate:** None")

    if carry_forward.get("selected_reference"):
        lines.append(
            f"- **Selected reference candidate:** "
            f"{carry_forward['selected_reference']} "
            f"({carry_forward['selected_reference_mean_ms']:.3f} ms)"
        )
    else:
        lines.append("- **Selected reference candidate:** None")

    lines.append(
        f"- **Rejected:** {', '.join(carry_forward['rejected']) or 'None'}"
    )

    with open(os.path.join(results_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
