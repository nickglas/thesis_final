"""Statistical analysis for RQ1.1 benchmark results.

Implements:
  - Per-condition summary statistics (mean, median, std, percentiles, CI)
  - Per-round summaries
  - Cross-condition overhead comparisons
  - Effect sizes (Cohen's d) and non-parametric tests (Mann-Whitney U)
  - Carry-forward selection rule (Section 6)
"""

import csv
import math
import numpy as np
from scipy import stats
from typing import Any, Dict, List


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

def load_raw_iterations(path: str) -> List[Dict[str, Any]]:
    """Load raw_iterations.csv and coerce numeric columns."""
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            for key in row:
                if key in ("round", "iteration", "activation_bytes"):
                    row[key] = int(float(row[key]))
                elif key != "condition":
                    try:
                        row[key] = float(row[key])
                    except (ValueError, TypeError):
                        pass
            rows.append(row)
    return rows


# ------------------------------------------------------------------
# Per-condition summaries
# ------------------------------------------------------------------

def compute_condition_summary(rows: List[Dict], condition: str) -> Dict:
    """Compute the full statistical summary for one condition."""
    cond_rows = [r for r in rows if r["condition"] == condition]
    if not cond_rows:
        return {}

    latencies = np.array([r["end_to_end_ms"] for r in cond_rows])
    n = len(latencies)

    summary = {
        "condition": condition,
        "n": n,
        "mean_ms": float(np.mean(latencies)),
        "median_ms": float(np.median(latencies)),
        "std_ms": float(np.std(latencies, ddof=1)),
        "min_ms": float(np.min(latencies)),
        "max_ms": float(np.max(latencies)),
        "p5_ms": float(np.percentile(latencies, 5)),
        "p25_ms": float(np.percentile(latencies, 25)),
        "p75_ms": float(np.percentile(latencies, 75)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "p99_ms": float(np.percentile(latencies, 99)),
    }

    # 95% confidence interval (t-distribution)
    se = summary["std_ms"] / math.sqrt(n)
    t_crit = stats.t.ppf(0.975, df=n - 1)
    summary["ci95_lower_ms"] = summary["mean_ms"] - t_crit * se
    summary["ci95_upper_ms"] = summary["mean_ms"] + t_crit * se

    # Secondary metrics for split conditions
    summary["service_a_compute_ms_mean"] = float(
        np.mean([r["service_a_compute_ms"] for r in cond_rows])
    )
    summary["service_b_compute_ms_mean"] = float(
        np.mean([r["service_b_compute_ms"] for r in cond_rows])
    )
    summary["boundary_crossing_ms_mean"] = float(
        np.mean([r["boundary_crossing_ms"] for r in cond_rows])
    )
    summary["activation_bytes_mean"] = float(
        np.mean([r["activation_bytes"] for r in cond_rows])
    )

    return summary


# ------------------------------------------------------------------
# Per-round summaries
# ------------------------------------------------------------------

def compute_round_summaries(rows: List[Dict]) -> List[Dict]:
    """Compute per-(round, condition) summary statistics."""
    groups: Dict[tuple, list] = {}
    for r in rows:
        key = (r["round"], r["condition"])
        groups.setdefault(key, []).append(r)

    summaries = []
    for (round_num, condition), group_rows in sorted(groups.items()):
        latencies = np.array([r["end_to_end_ms"] for r in group_rows])
        summaries.append({
            "round": round_num,
            "condition": condition,
            "n": len(latencies),
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "std_ms": float(np.std(latencies, ddof=1)),
            "min_ms": float(np.min(latencies)),
            "max_ms": float(np.max(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
        })
    return summaries


# ------------------------------------------------------------------
# Cross-condition comparisons
# ------------------------------------------------------------------

def compute_cross_condition(summaries: List[Dict]) -> List[Dict]:
    """Compute overhead of each split condition relative to monolithic."""
    mono = next((s for s in summaries if s["condition"] == "monolithic"), None)
    if not mono:
        return []

    comparisons = []
    for s in summaries:
        if s["condition"] == "monolithic":
            continue
        overhead_ms = s["mean_ms"] - mono["mean_ms"]
        overhead_pct = (
            (overhead_ms / mono["mean_ms"]) * 100 if mono["mean_ms"] > 0
            else float("inf")
        )
        comparisons.append({
            "condition": s["condition"],
            "split_mean_ms": s["mean_ms"],
            "monolith_mean_ms": mono["mean_ms"],
            "overhead_ms": overhead_ms,
            "overhead_pct": overhead_pct,
            "activation_bytes": s.get("activation_bytes_mean", 0),
            "service_a_compute_ms": s.get("service_a_compute_ms_mean", 0),
            "service_b_compute_ms": s.get("service_b_compute_ms_mean", 0),
            "boundary_crossing_ms": s.get("boundary_crossing_ms_mean", 0),
        })
    return comparisons


def compute_effect_sizes(rows: List[Dict], summaries: List[Dict]) -> List[Dict]:
    """Compute Cohen's d and Mann-Whitney U for each split vs monolithic."""
    mono_lat = np.array([
        r["end_to_end_ms"] for r in rows if r["condition"] == "monolithic"
    ])
    if len(mono_lat) == 0:
        return []

    effects = []
    for s in summaries:
        if s["condition"] == "monolithic":
            continue
        split_lat = np.array([
            r["end_to_end_ms"] for r in rows if r["condition"] == s["condition"]
        ])
        if len(split_lat) == 0:
            continue

        # Cohen's d (pooled)
        pooled_std = math.sqrt(
            ((len(mono_lat) - 1) * np.var(mono_lat, ddof=1) +
             (len(split_lat) - 1) * np.var(split_lat, ddof=1)) /
            (len(mono_lat) + len(split_lat) - 2)
        )
        cohens_d = (
            (np.mean(split_lat) - np.mean(mono_lat)) / pooled_std
            if pooled_std > 0 else float("inf")
        )

        # Mann-Whitney U
        u_stat, p_value = stats.mannwhitneyu(
            mono_lat, split_lat, alternative="two-sided"
        )

        effects.append({
            "condition": s["condition"],
            "cohens_d": float(cohens_d),
            "mann_whitney_u": float(u_stat),
            "mann_whitney_p": float(p_value),
        })
    return effects


# ------------------------------------------------------------------
# Carry-forward selection rule (Section 6)
# ------------------------------------------------------------------

def apply_carry_forward_rule(summaries: List[Dict], cross_condition: List[Dict],
                             near_best_pct: float,
                             degeneracy_pct: float) -> Dict:
    """Apply the predeclared carry-forward rule.

    1. Primary criterion:  minimise mean end-to-end latency among splits.
    2. Near-best window:   within near_best_pct % of the best split mean.
    3. Degeneracy filter:  reject candidates where one side contributes
                           less than degeneracy_pct % of total split compute.
    4. Tie-break:          prefer lower activation_bytes_mean.

    Returns a dict with output categories:
      raw_fastest, selected_main, selected_reference, rejected
    """
    splits = [s for s in summaries if s["condition"] != "monolithic"]
    if not splits:
        return {"error": "No split conditions found"}

    # 1. Raw fastest boundary
    raw_fastest = min(splits, key=lambda s: s["mean_ms"])

    # 2. Near-best window
    best_mean = raw_fastest["mean_ms"]
    threshold = best_mean * (1 + near_best_pct / 100)
    near_best = [s for s in splits if s["mean_ms"] <= threshold]

    # 3. Degeneracy filter
    def is_degenerate(s):
        a = s.get("service_a_compute_ms_mean", 0)
        b = s.get("service_b_compute_ms_mean", 0)
        total = a + b
        if total <= 0:
            return True
        minor_share_pct = min(a, b) / total * 100
        return minor_share_pct < degeneracy_pct

    non_degenerate = [s for s in near_best if not is_degenerate(s)]

    # 4. Selection with tie-break on activation bytes
    def sort_key(s):
        return (s["mean_ms"], s.get("activation_bytes_mean", 0))

    if non_degenerate:
        selected_main = min(non_degenerate, key=sort_key)
        remaining = [s for s in non_degenerate
                     if s["condition"] != selected_main["condition"]]
        selected_reference = min(remaining, key=sort_key) if remaining else None
    else:
        # Fallback: all near-best are degenerate
        selected_main = min(near_best, key=sort_key)
        selected_reference = None

    # Build rejected list
    selected_names = {selected_main["condition"]}
    if selected_reference:
        selected_names.add(selected_reference["condition"])
    rejected = [s["condition"] for s in splits
                if s["condition"] not in selected_names]

    return {
        "raw_fastest": raw_fastest["condition"],
        "raw_fastest_mean_ms": raw_fastest["mean_ms"],
        "near_best_window_pct": near_best_pct,
        "near_best_threshold_ms": threshold,
        "near_best_candidates": [s["condition"] for s in near_best],
        "degeneracy_threshold_pct": degeneracy_pct,
        "degenerate_candidates": [s["condition"] for s in near_best
                                  if is_degenerate(s)],
        "selected_main": selected_main["condition"],
        "selected_main_mean_ms": selected_main["mean_ms"],
        "selected_reference": (selected_reference["condition"]
                               if selected_reference else None),
        "selected_reference_mean_ms": (selected_reference["mean_ms"]
                                       if selected_reference else None),
        "rejected": rejected,
    }
