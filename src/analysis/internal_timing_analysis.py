"""Analysis and reporting for the internal timing mode.

Reads raw_timings.csv and produces:
  - summary.csv           per-unit summary statistics
  - round_consistency.csv per-unit per-round means + CV
  - timing_gaps.csv       parent vs sum-of-children consistency
  - report.md             human-readable markdown report
  - plots/compute_distribution.png

This module is part of the exploratory internal-timing mode and does
NOT modify the thesis-facing analysis modules.
"""

import os
import csv
import json
import math
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

def _load_raw_timings(path: str) -> List[Dict[str, Any]]:
    """Load raw_timings.csv and coerce types."""
    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "round": int(row["round"]),
                "iteration": int(row["iteration"]),
                "unit_name": row["unit_name"],
                "level": row["level"],
                "parent": row["parent"],
                "elapsed_ms": float(row["elapsed_ms"]),
            })
    return rows


# ------------------------------------------------------------------
# Statistics helpers
# ------------------------------------------------------------------

def _stats(values: List[float]) -> Dict[str, float]:
    """Compute summary statistics for a list of values."""
    n = len(values)
    if n == 0:
        return {}
    s = sorted(values)
    mean = sum(s) / n
    median = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2
    if n > 1:
        var = sum((x - mean) ** 2 for x in s) / (n - 1)
        std = math.sqrt(var)
    else:
        std = 0.0
    p95_idx = min(int(math.ceil(0.95 * n)) - 1, n - 1)
    return {
        "n": n,
        "mean_ms": round(mean, 6),
        "median_ms": round(median, 6),
        "std_ms": round(std, 6),
        "p95_ms": round(s[p95_idx], 6),
        "min_ms": round(s[0], 6),
        "max_ms": round(s[-1], 6),
    }


# ------------------------------------------------------------------
# Summary computation
# ------------------------------------------------------------------

def compute_summary(raw_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute per-unit summary statistics with pct_of_model."""
    # Group by unit
    by_unit: Dict[str, List[float]] = defaultdict(list)
    unit_meta: Dict[str, Dict[str, str]] = {}
    for row in raw_rows:
        by_unit[row["unit_name"]].append(row["elapsed_ms"])
        if row["unit_name"] not in unit_meta:
            unit_meta[row["unit_name"]] = {
                "level": row["level"],
                "parent": row["parent"],
            }

    # Model mean for pct_of_model
    model_mean = 0.0
    if "model" in by_unit:
        model_mean = sum(by_unit["model"]) / len(by_unit["model"])

    summaries = []
    for unit_name, values in by_unit.items():
        s = _stats(values)
        pct = (s["mean_ms"] / model_mean * 100) if model_mean > 0 else 0.0
        summaries.append({
            "unit_name": unit_name,
            "level": unit_meta[unit_name]["level"],
            "parent": unit_meta[unit_name]["parent"],
            **s,
            "pct_of_model": round(pct, 2),
        })

    # Sort by level priority then by pct_of_model descending
    level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    summaries.sort(key=lambda x: (level_order.get(x["level"], 9), -x["pct_of_model"]))
    return summaries


# ------------------------------------------------------------------
# Round consistency
# ------------------------------------------------------------------

def compute_round_consistency(raw_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute per-unit per-round means and cross-round CV."""
    # Group by (unit, round)
    by_unit_round: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    unit_levels: Dict[str, str] = {}
    for row in raw_rows:
        by_unit_round[row["unit_name"]][row["round"]].append(row["elapsed_ms"])
        unit_levels[row["unit_name"]] = row["level"]

    results = []
    for unit_name, rounds_data in by_unit_round.items():
        round_means = []
        for rnd in sorted(rounds_data.keys()):
            vals = rounds_data[rnd]
            rm = sum(vals) / len(vals)
            round_means.append(rm)
            results.append({
                "unit_name": unit_name,
                "level": unit_levels[unit_name],
                "round": rnd,
                "round_mean_ms": round(rm, 6),
                "round_n": len(vals),
            })

        # Compute CV across round means for this unit
        if len(round_means) > 1:
            gm = sum(round_means) / len(round_means)
            gstd = math.sqrt(sum((x - gm) ** 2 for x in round_means) / (len(round_means) - 1))
            cv = gstd / gm if gm > 0 else 0.0
        else:
            cv = 0.0

        # Attach round_cv to every row for this unit
        for r in results:
            if r["unit_name"] == unit_name and "round_cv" not in r:
                r["round_cv"] = round(cv, 6)

    return results


# ------------------------------------------------------------------
# Timing gaps
# ------------------------------------------------------------------

def compute_timing_gaps(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute parent vs sum-of-children timing gaps."""
    mean_by_name = {s["unit_name"]: s["mean_ms"] for s in summaries}
    parent_by_name = {s["unit_name"]: s["parent"] for s in summaries}

    # Find units that have children
    children_of: Dict[str, List[str]] = defaultdict(list)
    for s in summaries:
        if s["parent"]:
            children_of[s["parent"]].append(s["unit_name"])

    gaps = []
    for parent_name, child_names in children_of.items():
        if parent_name not in mean_by_name:
            continue
        parent_mean = mean_by_name[parent_name]
        children_sum = sum(mean_by_name.get(c, 0.0) for c in child_names)
        gap_ms = parent_mean - children_sum
        gap_pct = (gap_ms / parent_mean * 100) if parent_mean > 0 else 0.0
        gaps.append({
            "parent": parent_name,
            "parent_mean_ms": round(parent_mean, 6),
            "children_sum_ms": round(children_sum, 6),
            "gap_ms": round(gap_ms, 6),
            "gap_pct": round(gap_pct, 2),
            "num_children": len(child_names),
        })

    gaps.sort(key=lambda x: abs(x["gap_pct"]), reverse=True)
    return gaps


# ------------------------------------------------------------------
# Plot
# ------------------------------------------------------------------

def plot_compute_distribution(summaries: List[Dict[str, Any]],
                              output_path: str):
    """Generate a horizontal bar chart of compute distribution."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping plot generation")
        return

    # Filter to L1 + L2 units, sorted by pct_of_model
    plot_units = [s for s in summaries if s["level"] in ("L1", "L2")]
    plot_units.sort(key=lambda x: x["pct_of_model"])

    names = [s["unit_name"] for s in plot_units]
    pcts = [s["pct_of_model"] for s in plot_units]
    colours = ["#2196F3" if s["level"] == "L1" else "#90CAF9" for s in plot_units]

    fig, ax = plt.subplots(figsize=(10, max(6, len(names) * 0.4)))
    bars = ax.barh(names, pcts, color=colours, edgecolor="white", linewidth=0.5)

    ax.set_xlabel("% of Total Forward Pass")
    ax.set_title("ResNet-18 Internal Compute Distribution")

    # Add percentage labels
    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", fontsize=8)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="Stage (L1)"),
        Patch(facecolor="#90CAF9", label="Block (L2)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved compute distribution plot to {output_path}")


# ------------------------------------------------------------------
# Report generation
# ------------------------------------------------------------------

def generate_report(results_dir: str, config: Optional[Any] = None) -> str:
    """Generate a markdown report from internal timing results."""
    raw_path = os.path.join(results_dir, "raw_timings.csv")
    raw_rows = _load_raw_timings(raw_path)

    summaries = compute_summary(raw_rows)
    round_consistency = compute_round_consistency(raw_rows)
    timing_gaps = compute_timing_gaps(summaries)

    # Load supporting artifacts
    env = _load_json(os.path.join(results_dir, "environment.json"))
    warmup = _load_json(os.path.join(results_dir, "warmup_calibration.json"))
    overhead = _load_json(os.path.join(results_dir, "instrumentation_overhead.json"))
    validation = _load_json(os.path.join(results_dir, "validation.json"))

    # Build summary lookup
    by_name = {s["unit_name"]: s for s in summaries}

    lines = []
    lines.append("# Internal Timing Report — ResNet-18 Compute Distribution\n")

    # --- Config ---
    lines.append("## Configuration\n")
    config_path = os.path.join(results_dir, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config_text = f.read()
        lines.append("```yaml")
        lines.append(config_text.rstrip())
        lines.append("```\n")

    # --- Environment ---
    lines.append("## Environment\n")
    if env:
        lines.append(f"- **Platform:** {env.get('platform', 'N/A')}")
        lines.append(f"- **Processor:** {env.get('processor', 'N/A')}")
        lines.append(f"- **Python:** {env.get('python_version', 'N/A')}")
        lines.append(f"- **PyTorch:** {env.get('torch_version', 'N/A')}")
        lines.append(f"- **CPU count:** {env.get('cpu_count', 'N/A')}")
        lines.append(f"- **Git commit:** {env.get('git_commit', 'N/A')}")
        lines.append("")

    # --- Validation ---
    lines.append("## Functional Equivalence Validation\n")
    if validation:
        lines.append(f"- **Passed:** {validation.get('passed', 'N/A')}")
        lines.append(f"- **Inputs tested:** {validation.get('num_inputs', 'N/A')}")
        lines.append(f"- **Max abs diff:** {validation.get('max_abs_diff', 'N/A'):.2e}")
        lines.append(f"- **Tolerance:** {validation.get('atol', 'N/A'):.2e}")
        lines.append("")

    # --- Warmup ---
    lines.append("## Warmup\n")
    if warmup:
        lines.append(f"- **Total warmup iterations:** {warmup.get('total_iterations', 'N/A')}")
        lines.append(f"- **Stabilised:** {warmup.get('stabilised', 'N/A')}")
        stab_at = warmup.get('stabilised_at_iteration')
        lines.append(f"- **Stabilised at iteration:** {stab_at if stab_at else 'N/A'}")
        cv = warmup.get('final_window_cv')
        lines.append(f"- **Final window CV:** {cv:.4f}" if cv is not None else "- **Final window CV:** N/A")
        lines.append("")

    # --- Overhead ---
    lines.append("## Instrumentation Overhead\n")
    if overhead:
        lines.append(f"- **Plain forward mean:** {overhead.get('plain_mean_ms', 'N/A'):.4f} ms")
        lines.append(f"- **Instrumented forward mean:** {overhead.get('instrumented_mean_ms', 'N/A'):.4f} ms")
        lines.append(f"- **Overhead:** {overhead.get('overhead_ms', 'N/A'):.4f} ms ({overhead.get('overhead_pct', 'N/A'):.2f}%)")
        lines.append(f"- **Samples:** {overhead.get('n_samples', 'N/A')}")
        lines.append("")
    else:
        lines.append("Overhead measurement was disabled.\n")

    # --- Stage-Level Summary ---
    lines.append("## Stage-Level Summary (L1)\n")
    stage_units = [s for s in summaries if s["level"] == "L1"]
    stage_units.sort(key=lambda x: -x["pct_of_model"])
    lines.append(_format_summary_table(stage_units))
    lines.append("")

    # --- Block-Level Summary ---
    block_units = [s for s in summaries if s["level"] == "L2"]
    if block_units:
        lines.append("## Block-Level Summary (L2)\n")
        block_units.sort(key=lambda x: -x["pct_of_model"])
        lines.append(_format_summary_table(block_units))
        lines.append("")

    # --- Operation-Level Summary grouped by block ---
    op_units = [s for s in summaries if s["level"] == "L3"]
    if op_units:
        lines.append("## Operation-Level Summary (L3) — Grouped by Parent\n")
        parents_seen = []
        op_by_parent: Dict[str, List] = defaultdict(list)
        for s in op_units:
            op_by_parent[s["parent"]].append(s)
            if s["parent"] not in parents_seen:
                parents_seen.append(s["parent"])

        for parent in parents_seen:
            ops = op_by_parent[parent]
            ops.sort(key=lambda x: -x["pct_of_model"])
            lines.append(f"### {parent}\n")
            lines.append(_format_summary_table(ops))
            lines.append("")

    # --- Ranked Top Operations ---
    if op_units:
        lines.append("## Ranked Operations (Top 20 by Compute Share)\n")
        ranked = sorted(op_units, key=lambda x: -x["pct_of_model"])[:20]
        lines.append(_format_summary_table(ranked))
        lines.append("")
        # Flag tiny operations
        tiny = [s for s in ranked if s["mean_ms"] < 0.01]
        if tiny:
            lines.append("> **Note:** Operations with mean < 0.01 ms are near the resolution "
                         "limit of `time.perf_counter()` and should be interpreted with caution. "
                         "Their rankings may be unreliable.\n")

    # --- Timing Gap Analysis ---
    if timing_gaps:
        lines.append("## Timing Gap Analysis\n")
        lines.append("> *Parent timings and the sum of their children are measured independently. "
                     "A small positive residual (the \"timing gap\") is expected due to Python "
                     "interpreter overhead between `perf_counter()` calls. This gap does not "
                     "represent missing compute.*\n")
        lines.append("| Parent | Parent Mean (ms) | Children Sum (ms) | Gap (ms) | Gap (%) |")
        lines.append("|--------|-----------------|-------------------|----------|---------|")
        for g in timing_gaps:
            lines.append(
                f"| {g['parent']} | {g['parent_mean_ms']:.4f} | "
                f"{g['children_sum_ms']:.4f} | {g['gap_ms']:.4f} | {g['gap_pct']:.2f}% |"
            )
        lines.append("")

    # --- Cross-Round Consistency ---
    lines.append("## Cross-Round Consistency\n")
    # Show units with highest round CV
    unit_cvs: Dict[str, float] = {}
    for r in round_consistency:
        if "round_cv" in r:
            unit_cvs[r["unit_name"]] = r["round_cv"]
    if unit_cvs:
        sorted_cvs = sorted(unit_cvs.items(), key=lambda x: -x[1])[:15]
        lines.append("| Unit | Round CV |")
        lines.append("|------|----------|")
        for name, cv in sorted_cvs:
            lines.append(f"| {name} | {cv:.4f} |")
        lines.append("")

    # --- Observations ---
    lines.append("## Observations\n")
    observations = _generate_observations(summaries, timing_gaps)
    for obs in observations:
        lines.append(f"- {obs}")
    lines.append("")

    # --- Model total ---
    if "model" in by_name:
        m = by_name["model"]
        lines.append("## Model Total\n")
        lines.append(f"- **Mean forward pass:** {m['mean_ms']:.4f} ms")
        lines.append(f"- **Median:** {m['median_ms']:.4f} ms")
        lines.append(f"- **Std:** {m['std_ms']:.4f} ms")
        lines.append(f"- **p95:** {m['p95_ms']:.4f} ms")
        lines.append(f"- **Observations:** {m['n']}")
        lines.append("")

    report_text = "\n".join(lines)

    # Save artifacts
    _save_csv(os.path.join(results_dir, "summary.csv"), summaries)
    _save_csv(os.path.join(results_dir, "round_consistency.csv"), round_consistency)
    _save_csv(os.path.join(results_dir, "timing_gaps.csv"), timing_gaps)

    report_path = os.path.join(results_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Generate plot
    plot_path = os.path.join(results_dir, "plots", "compute_distribution.png")
    plot_compute_distribution(summaries, plot_path)

    return report_path


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _format_summary_table(units: List[Dict[str, Any]]) -> str:
    """Format a list of summary dicts as a markdown table."""
    lines = []
    lines.append("| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |")
    lines.append("|------|-----------|-------------|----------|----------|----------|----------|------------|")
    for u in units:
        lines.append(
            f"| {u['unit_name']} | {u['mean_ms']:.4f} | {u['median_ms']:.4f} | "
            f"{u['std_ms']:.4f} | {u['p95_ms']:.4f} | {u['min_ms']:.4f} | "
            f"{u['max_ms']:.4f} | {u['pct_of_model']:.2f}% |"
        )
    return "\n".join(lines)


def _generate_observations(summaries: List[Dict[str, Any]],
                           timing_gaps: List[Dict[str, Any]]) -> List[str]:
    """Generate conservative, descriptive observations."""
    obs = []
    by_name = {s["unit_name"]: s for s in summaries}

    # Model total
    if "model" in by_name:
        obs.append(f"Total mean forward pass: {by_name['model']['mean_ms']:.4f} ms.")

    # Top stage
    stages = [s for s in summaries if s["level"] == "L1"]
    if stages:
        stages.sort(key=lambda x: -x["pct_of_model"])
        top = stages[0]
        obs.append(
            f"Most expensive stage: `{top['unit_name']}` at {top['pct_of_model']:.1f}% "
            f"of total ({top['mean_ms']:.4f} ms)."
        )
        bottom = stages[-1]
        obs.append(
            f"Least expensive stage: `{bottom['unit_name']}` at {bottom['pct_of_model']:.1f}% "
            f"of total ({bottom['mean_ms']:.4f} ms)."
        )

    # Top block
    blocks = [s for s in summaries if s["level"] == "L2"]
    if blocks:
        blocks.sort(key=lambda x: -x["pct_of_model"])
        top_block = blocks[0]
        obs.append(
            f"Most expensive block: `{top_block['unit_name']}` at {top_block['pct_of_model']:.1f}% "
            f"of total ({top_block['mean_ms']:.4f} ms)."
        )

    # Conv vs other ops
    ops = [s for s in summaries if s["level"] == "L3"]
    if ops:
        conv_ops = [s for s in ops if "conv" in s["unit_name"]]
        bn_ops = [s for s in ops if ".bn" in s["unit_name"]]
        if conv_ops:
            conv_total = sum(s["mean_ms"] for s in conv_ops)
            model_mean = by_name.get("model", {}).get("mean_ms", 1.0)
            conv_pct = conv_total / model_mean * 100 if model_mean > 0 else 0.0
            obs.append(f"Convolution operations account for {conv_pct:.1f}% of total compute.")
        if bn_ops:
            bn_total = sum(s["mean_ms"] for s in bn_ops)
            model_mean = by_name.get("model", {}).get("mean_ms", 1.0)
            bn_pct = bn_total / model_mean * 100 if model_mean > 0 else 0.0
            obs.append(f"BatchNorm operations account for {bn_pct:.1f}% of total compute.")

    # Downsample blocks vs non-downsample blocks
    if blocks:
        ds_blocks = [s for s in blocks if s["unit_name"].endswith(".0") and
                     s["unit_name"].split(".")[0] in ("layer2", "layer3", "layer4")]
        non_ds_blocks = [s for s in blocks if s not in ds_blocks]
        if ds_blocks and non_ds_blocks:
            ds_mean = sum(s["mean_ms"] for s in ds_blocks) / len(ds_blocks)
            non_ds_mean = sum(s["mean_ms"] for s in non_ds_blocks) / len(non_ds_blocks)
            obs.append(
                f"Blocks with downsample average {ds_mean:.4f} ms vs "
                f"{non_ds_mean:.4f} ms for blocks without downsample."
            )

    # Timing gaps
    if timing_gaps:
        max_gap = max(timing_gaps, key=lambda x: abs(x["gap_pct"]))
        obs.append(
            f"Largest timing gap: `{max_gap['parent']}` "
            f"({max_gap['gap_ms']:.4f} ms, {max_gap['gap_pct']:.2f}%)."
        )

    return obs


def _load_json(path: str) -> Optional[Dict]:
    """Load a JSON file, return None if missing."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _save_csv(path: str, rows: List[Dict[str, Any]]):
    """Save a list of dicts as CSV."""
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
