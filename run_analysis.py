"""Post-experiment analysis.

Reads raw_iterations.csv, computes all statistics, applies the
carry-forward rule, generates plots, and writes a summary report.
"""

import os
import json
import argparse
import logging

import yaml

from src.benchmark.config import load_config
from src.analysis.statistics import (
    load_raw_iterations,
    compute_condition_summary,
    compute_round_summaries,
    compute_cross_condition,
    compute_effect_sizes,
    compute_round_consistency,
    apply_carry_forward_rule,
)
from src.analysis.plots import generate_all_plots
from src.benchmark.logging import ArtifactLogger


def main():
    parser = argparse.ArgumentParser(
        description="Analyse benchmark results"
    )
    parser.add_argument("results_dir",
                        help="Path to results directory (e.g. results/rq1_1_20260414_...)")
    parser.add_argument("--config", default=None,
                        help="Config YAML (defaults to results_dir/config.yaml)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory for derived analysis artifacts. Defaults to results_dir "
            "when writable, otherwise falls back to a sibling *_analysis directory."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("analysis")

    results_dir = args.results_dir
    output_dir = _resolve_analysis_output_dir(results_dir, args.output_dir, logger)
    config_path = args.config or os.path.join(results_dir, "config.yaml")
    config = load_config(config_path)
    config_snapshot = _load_yaml_snapshot(config_path, logger)
    environment_path = os.path.join(results_dir, "environment.json")
    environment_snapshot = _load_json_snapshot(environment_path, logger)
    artifact = ArtifactLogger(output_dir)

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

    # ----- Cross-round consistency -----
    round_consistency = compute_round_consistency(round_sums)
    artifact.save_json("round_consistency.json", round_consistency)
    for rc in round_consistency:
        logger.info(
            f"  {rc['condition']}: round_std={rc['round_std_ms']:.4f} ms  "
            f"round_cv={rc['round_cv']:.4f}"
        )

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
    if carry_forward.get("applicable", True):
        logger.info(f"  Raw fastest:        {carry_forward['raw_fastest']}")
        logger.info(f"  Selected main:      {carry_forward['selected_main']}")
        logger.info(f"  Selected reference: {carry_forward['selected_reference']}")
        logger.info(f"  Rejected:           {carry_forward['rejected']}")
        logger.info(f"  Fallback used:      {carry_forward.get('fallback_used', False)}")
        if carry_forward.get("fallback_used"):
            logger.warning(f"  NOTE: {carry_forward['fallback_note']}")
    else:
        logger.info(f"  Not applicable:     {carry_forward.get('reason', 'n/a')}")

    # ----- Plots -----
    generate_all_plots(results_dir, output_dir)
    logger.info("Plots generated")

    # ----- Summary report -----
    _generate_report(results_dir, output_dir, summaries, round_sums,
                     round_consistency, cross, effects, carry_forward,
                     experiment_name=config.experiment_name,
                     config_path=config_path,
                     config_snapshot=config_snapshot,
                     environment_path=environment_path,
                     environment_snapshot=environment_snapshot)
    if output_dir == results_dir:
        logger.info(f"Analysis complete. All artifacts in {output_dir}")
    else:
        logger.info(
            "Analysis complete. Derived artifacts in %s (source data read from %s)",
            output_dir,
            results_dir,
        )


# ------------------------------------------------------------------

def _resolve_analysis_output_dir(results_dir, requested_output_dir, logger):
    if requested_output_dir:
        os.makedirs(requested_output_dir, exist_ok=True)
        return requested_output_dir

    if os.path.isdir(results_dir) and os.access(results_dir, os.W_OK | os.X_OK):
        return results_dir

    normalized_results_dir = os.path.normpath(results_dir)
    parent_dir = os.path.dirname(normalized_results_dir)
    base_name = os.path.basename(normalized_results_dir)
    fallback_dir = os.path.join(parent_dir, f"{base_name}_analysis")
    os.makedirs(fallback_dir, exist_ok=True)
    logger.warning(
        "Results directory %s is not writable; writing derived analysis artifacts to %s",
        results_dir,
        fallback_dir,
    )
    return fallback_dir


def _load_yaml_snapshot(path, logger):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Config snapshot not found at %s", path)
    except Exception as exc:
        logger.warning("Could not read config snapshot %s: %s", path, exc)
    return None


def _load_json_snapshot(path, logger):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Environment snapshot not found at %s", path)
    except Exception as exc:
        logger.warning("Could not read environment snapshot %s: %s", path, exc)
    return None


def _flatten_mapping(mapping, prefix=""):
    rows = []
    if not isinstance(mapping, dict):
        return rows

    for key, value in mapping.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            rows.extend(_flatten_mapping(value, full_key))
        else:
            rows.append((full_key, value))
    return rows


def _format_report_value(value):
    if value is None:
        text = "n/a"
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value) if value else "n/a"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _append_settings_table(lines, rows):
    if not rows:
        lines.append("_No recorded settings._")
        return

    lines.append("| Setting | Value |")
    lines.append("|---|---|")
    for key, value in rows:
        lines.append(f"| {key} | {_format_report_value(value)} |")


def _append_config_details(lines, config_path, config_snapshot):
    lines.extend([
        "\n## Configuration Used\n",
        f"- **Config snapshot:** `{config_path}`",
    ])

    if not config_snapshot:
        lines.extend(["", "_Config snapshot unavailable._"])
        return

    section_order = [
        "experiment",
        "model",
        "benchmark",
        "grpc",
        "kubernetes",
        "carry_forward",
        "parity",
        "warmup_calibration",
        "cpu_stabilisation",
    ]

    for section_name in section_order:
        section = config_snapshot.get(section_name)
        if not section:
            continue
        lines.extend([f"\n### {section_name.replace('_', ' ').title()}\n"])
        _append_settings_table(lines, _flatten_mapping(section))

    conditions = config_snapshot.get("conditions")
    if conditions:
        lines.extend([
            "\n### Conditions\n",
            "| Condition | Type | Split After | Chain Split Points |",
            "|---|---|---|---|",
        ])
        for condition in conditions:
            if isinstance(condition, dict):
                lines.append(
                    f"| {_format_report_value(condition.get('name'))} | "
                    f"{_format_report_value(condition.get('type'))} | "
                    f"{_format_report_value(condition.get('split_after'))} | "
                    f"{_format_report_value(condition.get('chain_split_points'))} |"
                )
            else:
                lines.append(
                    f"| {_format_report_value(condition)} | n/a | n/a | n/a |"
                )


def _append_environment_details(lines, environment_path, environment_snapshot):
    lines.extend([
        "\n## Environment Used\n",
        f"- **Environment snapshot:** `{environment_path}`",
    ])

    if not environment_snapshot:
        lines.extend(["", "_Environment snapshot unavailable._"])
        return

    runtime_rows = [
        (key, value)
        for key, value in environment_snapshot.items()
        if key != "cpu_stabilisation"
    ]
    if runtime_rows:
        lines.extend(["\n### Runtime\n"])
        _append_settings_table(lines, runtime_rows)

    cpu_stabilisation = environment_snapshot.get("cpu_stabilisation")
    if cpu_stabilisation:
        lines.extend(["\n### CPU Stabilisation Observed\n"])
        if isinstance(cpu_stabilisation, dict):
            _append_settings_table(lines, _flatten_mapping(cpu_stabilisation))
        else:
            _append_settings_table(lines, [("cpu_stabilisation", cpu_stabilisation)])


def _generate_report(source_results_dir, output_dir, summaries, round_sums,
                     round_consistency, cross, effects, carry_forward,
                     experiment_name="RQ1.1", config_path=None,
                     config_snapshot=None, environment_path=None,
                     environment_snapshot=None):
    """Write a Markdown summary report."""
    lines = [f"# {experiment_name} Experiment Report\n"]
    if output_dir != source_results_dir:
        lines.extend([
            "> Source results directory: "
            f"`{source_results_dir}`.",
            "> Derived analysis artifacts directory: "
            f"`{output_dir}`.\n",
        ])

    if config_path:
        _append_config_details(lines, config_path, config_snapshot)
    if environment_path:
        _append_environment_details(lines, environment_path, environment_snapshot)

    lines.extend([
        "## Condition Summaries\n",
        "| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |",
        "|---|---|---|---|---|---|---|",
    ])
    for s in summaries:
        lines.append(
            f"| {s['condition']} | {s['n']} | {s['mean_ms']:.3f} | "
            f"{s['median_ms']:.3f} | {s['std_ms']:.3f} | {s['p95_ms']:.3f} | "
            f"[{s['ci95_lower_ms']:.3f}, {s['ci95_upper_ms']:.3f}] |"
        )

    # ----- Round-level summaries -----
    lines.extend(["\n## Per-Round Summaries\n"])
    lines.append("| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |")
    lines.append("|---|---|---|---|---|---|---|")
    for rs in round_sums:
        lines.append(
            f"| {rs['round']} | {rs['condition']} | {rs['n']} | "
            f"{rs['mean_ms']:.3f} | {rs['median_ms']:.3f} | "
            f"{rs['std_ms']:.3f} | {rs['p95_ms']:.3f} |"
        )

    # ----- Cross-round consistency -----
    lines.extend(["\n## Cross-Round Consistency\n"])
    lines.append(
        "| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | "
        "Round Range (ms) | Round CV |"
    )
    lines.append("|---|---|---|---|---|---|")
    for rc in round_consistency:
        lines.append(
            f"| {rc['condition']} | {rc['n_rounds']} | "
            f"{rc['grand_mean_ms']:.3f} | {rc['round_std_ms']:.4f} | "
            f"{rc['round_range_ms']:.4f} | {rc['round_cv']:.4f} |"
        )

    # ----- Overhead -----
    baseline_label = cross[0].get("baseline_condition", "monolithic") if cross else "monolithic"
    lines.extend([f"\n## Overhead vs {baseline_label}\n"])
    if cross:
        lines.append(
            "| Condition | Overhead (ms) | Overhead (%) "
            "| Activation (KB) | Boundary / Non-Compute (ms) |"
        )
        lines.append("|---|---|---|---|---|")
        for cc in cross:
            lines.append(
                f"| {cc['condition']} | {cc['overhead_ms']:.3f} | "
                f"{cc['overhead_pct']:.1f}% | "
                f"{cc['activation_bytes'] / 1024:.1f} | "
                f"{cc['boundary_crossing_ms']:.3f} |"
            )

    # ----- Effect sizes (secondary, with caveats) -----
    lines.extend([
        "\n## Effect Sizes (Supplementary)\n",
        "> **Methodological note:** Effect sizes below are computed from pooled "
        "per-iteration data. With N = 1,000 iterations per condition, "
        "Mann-Whitney p-values are near-zero for any non-trivial difference "
        "and should not be interpreted as strong evidence of practical "
        "significance. Cohen's d provides a more informative measure of "
        "effect magnitude. Cross-round consistency (above) is a more "
        "defensible indicator of result stability.\n",
    ])
    if effects:
        lines.append("| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |")
        lines.append("|---|---|---|---|---|")
        for e in effects:
            d = abs(e['cohens_d'])
            if d < 0.2:
                interp = "negligible"
            elif d < 0.5:
                interp = "small"
            elif d < 0.8:
                interp = "medium"
            else:
                interp = "large"
            lines.append(
                f"| {e['condition']} | {e['cohens_d']:.3f} | {interp} | "
                f"{e['mann_whitney_u']:.1f} | {e['mann_whitney_p']:.2e} |"
            )

    # ----- Carry-forward -----
    lines.extend(["\n## Carry-Forward Selection\n"])
    if carry_forward.get("applicable", True):
        lines.extend([
            f"- **Raw fastest boundary:** {carry_forward['raw_fastest']} "
            f"({carry_forward['raw_fastest_mean_ms']:.3f} ms)",
            f"- **Near-best window:** {carry_forward['near_best_window_pct']}% "
            f"→ threshold {carry_forward['near_best_threshold_ms']:.3f} ms",
            f"- **Near-best candidates:** "
            f"{', '.join(carry_forward['near_best_candidates'])}",
            f"- **Degenerate candidates:** "
            f"{', '.join(carry_forward['degenerate_candidates']) or 'None'}",
            f"- **Degeneracy threshold:** "
            f"{carry_forward['degeneracy_threshold_pct']}% of split compute",
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

        fallback = carry_forward.get("fallback_used", False)
        lines.append(f"- **Fallback used:** {fallback}")
        if fallback:
            lines.extend([
                "",
                f"> **⚠ Fallback note:** {carry_forward['fallback_note']}",
            ])

        lines.extend([
            "\n## Carry-Forward Rule (as implemented)\n",
            "1. Identify `raw_fastest`: split with lowest mean end-to-end latency.",
            f"2. Near-best window: all splits within {carry_forward['near_best_window_pct']}% "
            "of `raw_fastest` mean.",
            f"3. Degeneracy filter: exclude candidates where the minor compute side "
            f"contributes < {carry_forward['degeneracy_threshold_pct']}% of total "
            "split compute (`service_a` + `service_b`).",
            "4. If non-degenerate near-best candidates exist: select `selected_main` "
            "by (`mean_ms`, `activation_bytes`), with `selected_reference` as runner-up.",
            "5. If ALL near-best candidates are degenerate: `selected_main = None`, "
            "`selected_reference = raw_fastest` (reference only, not promoted).",
            "6. Tie-break: prefer lower `activation_bytes_mean`.",
        ])
    else:
        lines.extend([
            "- **Status:** Not applicable",
            f"- **Reason:** {carry_forward.get('reason', 'n/a')}",
        ])

    # ----- Methodology notes -----
    lines.extend([
        "\n## Methodology Notes\n",
        "- **Parity validation:** Functional equivalence was verified as a "
        "mandatory precondition for both local (PartA→PartB) and gRPC "
        "round-trip paths. Results are recorded in `parity_validation.json`.",
        "- **Warmup calibration:** Each condition×round warmup was monitored "
        "for latency stabilisation using a trailing-window coefficient of "
        "variation (CV) check. Calibration results are recorded in "
        "`warmup_calibration.json`.",
        "- **Statistical reporting:** Per-iteration significance tests "
        "(Mann-Whitney U) are reported as supplementary. With large N, "
        "p-values are inflated and should not be over-interpreted. "
        "Cross-round consistency and confidence intervals are the primary "
        "evidence of result stability.",
        "- **Carry-forward rule:** " + (
            "The selection rule is predeclared and fully explicit. No hidden "
            "fallback promotes degenerate candidates to `selected_main`."
            if carry_forward.get("applicable", True)
            else "Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage."
        ),
    ])

    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
