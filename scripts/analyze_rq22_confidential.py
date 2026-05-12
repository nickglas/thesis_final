#!/usr/bin/env python3
"""Aggregate and summarize RQ2.2 confidential service2 benchmark artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "results"
STANDARD_KEY = "standard"
CONFIDENTIAL_KEY = "confidential"


class AnalysisError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze an RQ2.2 rolling confidential benchmark artifact. "
            "Writes merged raw iterations, condition summaries, paired deltas, plots, and Markdown."
        )
    )
    parser.add_argument(
        "artifact_dir",
        nargs="?",
        help="RQ2.2 artifact directory. Defaults to the latest results/rq2_2_confidential_* run.",
    )
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--output-dir", default=None, help="Defaults to <artifact_dir>/analysis.")
    return parser.parse_args()


def latest_artifact(results_root: Path) -> Path:
    candidates = [
        path
        for path in results_root.glob("rq2_2_confidential_*")
        if path.is_dir() and (path / "rq22_rolling_summary.json").exists()
    ]
    if not candidates:
        raise AnalysisError(f"No RQ2.2 artifacts found under {results_root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def localize_path(path_value: str | Path) -> Path:
    text = str(path_value)
    if text.startswith("/mnt/") and len(text) > 6 and text[6] == "/":
        drive = text[5].upper()
        rest = text[7:].replace("/", "\\")
        return Path(f"{drive}:\\{rest}")
    return Path(text)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def coerce_row(row: dict[str, str]) -> dict[str, Any]:
    coerced: dict[str, Any] = {}
    for key, value in row.items():
        if key in {"condition"}:
            coerced[key] = value
        elif key in {"round", "iteration", "num_hops"} or key.endswith("_bytes"):
            coerced[key] = int(float(value)) if value not in {"", None} else None
        else:
            coerced[key] = float(value) if value not in {"", None} else None
    return coerced


def load_rows(summary: dict[str, Any], artifact_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    completed = summary.get("completed") or []
    for record in completed:
        benchmark_dir = localize_path(record.get("benchmark_dir") or "")
        if not benchmark_dir.exists():
            condition_dir = artifact_dir / "conditions" / Path(str(record.get("manifest_dir") or "")).parent.name
            benchmark_dir = condition_dir / "benchmark"
        raw_path = benchmark_dir / "raw_iterations.csv"
        if not raw_path.exists():
            raise AnalysisError(f"Missing raw iterations for execution {record.get('execution_index')}: {raw_path}")
        with raw_path.open("r", encoding="utf-8", newline="") as handle:
            for raw_row in csv.DictReader(handle):
                row = coerce_row(raw_row)
                row.update(
                    {
                        "paired_pass": int(record["pass"]),
                        "execution_index": int(record["execution_index"]),
                        "condition_key": str(record["condition_key"]),
                        "condition_name": str(record["condition_name"]),
                        "tee_scope": str(record.get("tee_scope") or "service2_only"),
                        "service1_nodepool": str(record.get("service1_nodepool") or "r22s1std"),
                        "service1_vm_size": str(record.get("service1_vm_size") or "Standard_D8as_v5"),
                        "service1_confidential": bool(record.get("service1_confidential", False)),
                        "service2_nodepool": str(record["service2_nodepool"]),
                        "service2_vm_size": str(record["service2_vm_size"]),
                        "service2_confidential": bool(
                            record.get("service2_confidential", str(record.get("condition_key")) == CONFIDENTIAL_KEY)
                        ),
                        "service2_zone": str(record["service2_zone"]),
                        "source_raw_iterations": str(raw_path),
                    }
                )
                rows.append(row)
    if not rows:
        raise AnalysisError("No raw iteration rows found in completed RQ2.2 summary")
    return rows


def finite_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            values.append(float(value))
    return values


def mean_ci95(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    if len(values) < 2:
        return float(values[0]), 0.0
    arr = np.asarray(values, dtype=float)
    mean = float(np.mean(arr))
    sem = float(np.std(arr, ddof=1) / math.sqrt(len(arr)))
    try:
        from scipy import stats

        margin = float(stats.t.ppf(0.975, len(arr) - 1) * sem)
    except Exception:  # noqa: BLE001 - scipy is optional for this derived artifact.
        margin = 1.96 * sem
    return mean, margin


def numeric_summary(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    values = finite_values(rows, metric)
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "p05": None,
            "p95": None,
            "p99": None,
            "max": None,
            "mean_ci95_margin": None,
        }
    arr = np.asarray(values, dtype=float)
    mean, ci = mean_ci95(values)
    return {
        "n": int(len(values)),
        "mean": mean,
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if len(values) > 1 else 0.0,
        "min": float(np.min(arr)),
        "p05": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(np.max(arr)),
        "mean_ci95_margin": ci,
    }


def condition_summaries(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    metrics = [
        "end_to_end_ms",
        "total_compute_ms",
        "non_compute_overhead_ms",
        "hop_1_compute_ms",
        "hop_1_forward_ms",
        "hop_2_compute_ms",
        "hop_2_forward_ms",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["condition_key"])].append(row)

    summaries: dict[str, dict[str, Any]] = {}
    for key, group in grouped.items():
        latency = numeric_summary(group, "end_to_end_ms")
        summaries[key] = {
            "condition_key": key,
            "condition_name": group[0]["condition_name"],
            "tee_scope": group[0].get("tee_scope") or "service2_only",
            "service1_vm_size": group[0].get("service1_vm_size") or "",
            "service1_nodepool": group[0].get("service1_nodepool") or "",
            "service1_confidential": bool(group[0].get("service1_confidential")),
            "service2_vm_size": group[0]["service2_vm_size"],
            "service2_nodepool": group[0]["service2_nodepool"],
            "service2_confidential": bool(group[0].get("service2_confidential")),
            "service2_zone": group[0]["service2_zone"],
            "iteration_count": len(group),
            "passes_covered": sorted({int(row["paired_pass"]) for row in group}),
            "mean_latency_ms": latency["mean"],
            "median_latency_ms": latency["median"],
            "p95_latency_ms": latency["p95"],
            "p99_latency_ms": latency["p99"],
            "std_latency_ms": latency["std"],
            "mean_latency_ci95_margin_ms": latency["mean_ci95_margin"],
            "throughput_req_per_s": (1000.0 / latency["mean"]) if latency["mean"] else None,
            "metrics": {metric: numeric_summary(group, metric) for metric in metrics},
        }
    return summaries


def pct_delta(new_value: float | None, baseline_value: float | None) -> float | None:
    if new_value is None or baseline_value is None or baseline_value == 0:
        return None
    return ((new_value - baseline_value) / baseline_value) * 100.0


def comparison_summary(summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    standard = summaries.get(STANDARD_KEY)
    confidential = summaries.get(CONFIDENTIAL_KEY)
    if not standard or not confidential:
        return {"available": False, "reason": "standard or confidential summary missing"}

    comparison: dict[str, Any] = {
        "available": True,
        "baseline": STANDARD_KEY,
        "variant": CONFIDENTIAL_KEY,
        "mean_latency_delta_ms": confidential["mean_latency_ms"] - standard["mean_latency_ms"],
        "mean_latency_delta_pct": pct_delta(confidential["mean_latency_ms"], standard["mean_latency_ms"]),
        "median_latency_delta_ms": confidential["median_latency_ms"] - standard["median_latency_ms"],
        "median_latency_delta_pct": pct_delta(confidential["median_latency_ms"], standard["median_latency_ms"]),
        "p95_latency_delta_ms": confidential["p95_latency_ms"] - standard["p95_latency_ms"],
        "p95_latency_delta_pct": pct_delta(confidential["p95_latency_ms"], standard["p95_latency_ms"]),
        "throughput_delta_req_per_s": confidential["throughput_req_per_s"] - standard["throughput_req_per_s"],
        "throughput_delta_pct": pct_delta(confidential["throughput_req_per_s"], standard["throughput_req_per_s"]),
    }
    for metric in [
        "total_compute_ms",
        "non_compute_overhead_ms",
        "hop_1_compute_ms",
        "hop_1_forward_ms",
        "hop_2_compute_ms",
        "hop_2_forward_ms",
    ]:
        std_mean = standard["metrics"][metric]["mean"]
        conf_mean = confidential["metrics"][metric]["mean"]
        comparison[f"{metric}_mean_delta"] = conf_mean - std_mean
        comparison[f"{metric}_mean_delta_pct"] = pct_delta(conf_mean, std_mean)
    return comparison


def statistical_tests(rows: list[dict[str, Any]]) -> dict[str, Any]:
    standard_values = finite_values([row for row in rows if row["condition_key"] == STANDARD_KEY], "end_to_end_ms")
    confidential_values = finite_values([row for row in rows if row["condition_key"] == CONFIDENTIAL_KEY], "end_to_end_ms")
    if not standard_values or not confidential_values:
        return {"available": False}
    std_arr = np.asarray(standard_values, dtype=float)
    conf_arr = np.asarray(confidential_values, dtype=float)
    pooled_std = math.sqrt(
        ((len(std_arr) - 1) * float(np.var(std_arr, ddof=1)) + (len(conf_arr) - 1) * float(np.var(conf_arr, ddof=1)))
        / (len(std_arr) + len(conf_arr) - 2)
    )
    payload: dict[str, Any] = {
        "available": True,
        "cohens_d_confidential_vs_standard": (
            (float(np.mean(conf_arr)) - float(np.mean(std_arr))) / pooled_std if pooled_std else None
        ),
    }
    try:
        from scipy import stats

        t_result = stats.ttest_ind(conf_arr, std_arr, equal_var=False)
        u_result = stats.mannwhitneyu(conf_arr, std_arr, alternative="two-sided")
        payload.update(
            {
                "welch_t_statistic": float(t_result.statistic),
                "welch_t_pvalue": float(t_result.pvalue),
                "mann_whitney_u_statistic": float(u_result.statistic),
                "mann_whitney_u_pvalue": float(u_result.pvalue),
            }
        )
    except Exception as exc:  # noqa: BLE001 - scipy is optional for derived summary.
        payload["test_warning"] = f"scipy statistical tests unavailable: {exc}"
    return payload


def paired_pass_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    execution_order: dict[int, list[str]] = defaultdict(list)
    for row in rows:
        pass_id = int(row["paired_pass"])
        key = str(row["condition_key"])
        grouped[(pass_id, key)].append(row)
        if key not in execution_order[pass_id]:
            execution_order[pass_id].append(key)

    deltas: list[dict[str, Any]] = []
    for pass_id in sorted({key[0] for key in grouped}):
        std_rows = grouped.get((pass_id, STANDARD_KEY), [])
        conf_rows = grouped.get((pass_id, CONFIDENTIAL_KEY), [])
        if not std_rows or not conf_rows:
            continue
        std_latency = numeric_summary(std_rows, "end_to_end_ms")
        conf_latency = numeric_summary(conf_rows, "end_to_end_ms")
        std_compute = numeric_summary(std_rows, "total_compute_ms")
        conf_compute = numeric_summary(conf_rows, "total_compute_ms")
        std_overhead = numeric_summary(std_rows, "non_compute_overhead_ms")
        conf_overhead = numeric_summary(conf_rows, "non_compute_overhead_ms")
        deltas.append(
            {
                "paired_pass": pass_id,
                "execution_order": "->".join(execution_order[pass_id]),
                "standard_mean_ms": std_latency["mean"],
                "confidential_mean_ms": conf_latency["mean"],
                "delta_mean_ms": conf_latency["mean"] - std_latency["mean"],
                "delta_mean_pct": pct_delta(conf_latency["mean"], std_latency["mean"]),
                "standard_median_ms": std_latency["median"],
                "confidential_median_ms": conf_latency["median"],
                "delta_median_ms": conf_latency["median"] - std_latency["median"],
                "standard_p95_ms": std_latency["p95"],
                "confidential_p95_ms": conf_latency["p95"],
                "delta_p95_ms": conf_latency["p95"] - std_latency["p95"],
                "standard_total_compute_mean_ms": std_compute["mean"],
                "confidential_total_compute_mean_ms": conf_compute["mean"],
                "delta_total_compute_mean_ms": conf_compute["mean"] - std_compute["mean"],
                "standard_non_compute_overhead_mean_ms": std_overhead["mean"],
                "confidential_non_compute_overhead_mean_ms": conf_overhead["mean"],
                "delta_non_compute_overhead_mean_ms": conf_overhead["mean"] - std_overhead["mean"],
            }
        )
    return deltas


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def flatten_condition_summary(summary: dict[str, Any]) -> dict[str, Any]:
    row = {
        key: value
        for key, value in summary.items()
        if key not in {"metrics", "passes_covered"}
    }
    row["passes_covered"] = ",".join(str(item) for item in summary["passes_covered"])
    for metric, payload in summary["metrics"].items():
        row[f"{metric}_mean"] = payload["mean"]
        row[f"{metric}_median"] = payload["median"]
        row[f"{metric}_p95"] = payload["p95"]
        row[f"{metric}_std"] = payload["std"]
    return row


def format_float(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return f"{float(value):.{digits}f}"
    return str(value)


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    condition_summaries_payload = summary["conditions"]
    comparison = summary["comparison"]
    confidential_summary = condition_summaries_payload.get(CONFIDENTIAL_KEY) or {}
    tee_scope = confidential_summary.get("tee_scope") or "service2_only"
    if tee_scope == "full_2svc":
        variant_label = "full TEE"
        variant_description = "both service1 and service2 on standard AMD VMs vs both services on AMD SEV-SNP"
        guardrail = "Both service1 and service2 move to AMD SEV-SNP confidential nodes in the confidential condition."
    else:
        variant_label = "confidential service2"
        variant_description = "service2 standard vs service2 AMD SEV-SNP"
        guardrail = "Service1 stayed on the standard AMD pool; the measured variable is service2 standard vs service2 AMD SEV-SNP."
    lines = [
        "# RQ2.2 Confidential Analysis",
        "",
        f"Artifact: `{summary['artifact_dir']}`",
        f"Generated: `{summary['generated_at']}`",
        f"TEE scope: `{tee_scope}`",
        "",
        "## Condition Summary",
        "",
        "| Condition | Service1 VM | Service2 VM | n | Mean ms | Median ms | p95 ms | Throughput req/s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in [STANDARD_KEY, CONFIDENTIAL_KEY]:
        cond = condition_summaries_payload.get(key)
        if not cond:
            continue
        lines.append(
            "| "
            + " | ".join(
                    [
                        key,
                        cond.get("service1_vm_size") or "n/a",
                        cond["service2_vm_size"],
                        str(cond["iteration_count"]),
                    format_float(cond["mean_latency_ms"]),
                    format_float(cond["median_latency_ms"]),
                    format_float(cond["p95_latency_ms"]),
                    format_float(cond["throughput_req_per_s"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Confidential Delta",
            "",
            f"- Mean latency delta: `{format_float(comparison.get('mean_latency_delta_ms'))} ms` "
            f"({format_float(comparison.get('mean_latency_delta_pct'))}%).",
            f"- Median latency delta: `{format_float(comparison.get('median_latency_delta_ms'))} ms` "
            f"({format_float(comparison.get('median_latency_delta_pct'))}%).",
            f"- p95 latency delta: `{format_float(comparison.get('p95_latency_delta_ms'))} ms` "
            f"({format_float(comparison.get('p95_latency_delta_pct'))}%).",
            f"- Throughput delta: `{format_float(comparison.get('throughput_delta_req_per_s'))} req/s` "
            f"({format_float(comparison.get('throughput_delta_pct'))}%).",
            "",
            "## Paired Pass Deltas",
            "",
            "| Pass | Order | Std mean ms | TEE mean ms | Delta ms | Delta % |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["paired_pass_deltas"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["paired_pass"]),
                    row["execution_order"],
                    format_float(row["standard_mean_ms"]),
                    format_float(row["confidential_mean_ms"]),
                    format_float(row["delta_mean_ms"]),
                    format_float(row["delta_mean_pct"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            f"- {guardrail}",
            f"- The measured variable is {variant_description}.",
            "- Both conditions used the same pushed image digest and managed AKS Istio mTLS/AuthZ semantics.",
            "- Throughput is computed as sequential client request rate: `1000 / mean_latency_ms`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_plots(output_dir: Path, rows: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[str]:
    plot_paths: list[str] = []
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001 - derived plots should not block tables.
        (output_dir / "plot_warning.txt").write_text(f"Plot generation skipped: {exc}\n", encoding="utf-8")
        return plot_paths

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    tee_scope = ""
    for row in rows:
        if row.get("condition_key") == CONFIDENTIAL_KEY:
            tee_scope = str(row.get("tee_scope") or "")
            break
    label_map = {
        STANDARD_KEY: "Standard",
        CONFIDENTIAL_KEY: "Full TEE" if tee_scope == "full_2svc" else "TEE service2",
    }
    data = [
        finite_values([row for row in rows if row["condition_key"] == key], "end_to_end_ms")
        for key in [STANDARD_KEY, CONFIDENTIAL_KEY]
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, labels=[label_map[STANDARD_KEY], label_map[CONFIDENTIAL_KEY]], patch_artist=True)
    ax.set_ylabel("End-to-end latency (ms)")
    ax.set_title("RQ2.2 Latency: Standard vs " + label_map[CONFIDENTIAL_KEY])
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = plots_dir / "latency_boxplot.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    plot_paths.append(str(out))

    fig, ax = plt.subplots(figsize=(8, 5))
    x = [row["paired_pass"] for row in deltas]
    y = [row["delta_mean_pct"] for row in deltas]
    ax.axhline(0, color="black", linewidth=0.8)
    ax.plot(x, y, marker="o")
    ax.set_xlabel("Paired pass")
    ax.set_ylabel(f"{label_map[CONFIDENTIAL_KEY]} mean latency delta (%)")
    ax.set_title("RQ2.2 Paired-Pass Confidential Delta")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = plots_dir / "paired_pass_delta_pct.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    plot_paths.append(str(out))

    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.35
    passes = [row["paired_pass"] for row in deltas]
    std_means = [row["standard_mean_ms"] for row in deltas]
    conf_means = [row["confidential_mean_ms"] for row in deltas]
    positions = np.arange(len(passes))
    ax.bar(positions - width / 2, std_means, width, label="Standard")
    ax.bar(positions + width / 2, conf_means, width, label=label_map[CONFIDENTIAL_KEY])
    ax.set_xticks(positions)
    ax.set_xticklabels([str(item) for item in passes])
    ax.set_xlabel("Paired pass")
    ax.set_ylabel("Mean latency (ms)")
    ax.set_title("RQ2.2 Mean Latency by Paired Pass")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = plots_dir / "paired_pass_means.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    plot_paths.append(str(out))

    return plot_paths


def analyze(artifact_dir: Path, output_dir: Path) -> dict[str, Any]:
    summary_path = artifact_dir / "rq22_rolling_summary.json"
    if not summary_path.exists():
        raise AnalysisError(f"Missing RQ2.2 rolling summary: {summary_path}")
    run_summary = read_json(summary_path)
    rows = load_rows(run_summary, artifact_dir)
    summaries = condition_summaries(rows)
    comparison = comparison_summary(summaries)
    deltas = paired_pass_deltas(rows)
    tests = statistical_tests(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_fieldnames = [
        "paired_pass",
        "execution_index",
        "condition_key",
        "condition_name",
        "tee_scope",
        "service1_vm_size",
        "service1_nodepool",
        "service1_confidential",
        "service2_vm_size",
        "service2_nodepool",
        "service2_confidential",
        "service2_zone",
        "round",
        "iteration",
        "end_to_end_ms",
        "total_compute_ms",
        "non_compute_overhead_ms",
        "total_activation_bytes",
        "num_hops",
        "hop_1_compute_ms",
        "hop_1_forward_ms",
        "hop_2_compute_ms",
        "hop_2_forward_ms",
        "source_raw_iterations",
    ]
    write_csv(output_dir / "rq22_raw_iterations.csv", rows, raw_fieldnames)
    write_csv(
        output_dir / "rq22_condition_summary.csv",
        [flatten_condition_summary(summaries[key]) for key in sorted(summaries)],
    )
    write_csv(output_dir / "rq22_paired_pass_deltas.csv", deltas)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_dir": str(artifact_dir),
        "source_summary": str(summary_path),
        "status": run_summary.get("status"),
        "image_ref": run_summary.get("effective_image_ref"),
        "execution_plan": run_summary.get("execution_plan"),
        "conditions": summaries,
        "comparison": comparison,
        "paired_pass_deltas": deltas,
        "statistical_tests": tests,
        "requirements": {
            "run_completed": run_summary.get("status") == "completed",
            "standard_runs": summaries.get(STANDARD_KEY, {}).get("iteration_count", 0),
            "confidential_runs": summaries.get(CONFIDENTIAL_KEY, {}).get("iteration_count", 0),
            "paired_pass_count": len(deltas),
        },
        "interpretation": {
            "tee_scope": summaries.get(CONFIDENTIAL_KEY, {}).get("tee_scope"),
            "measured_variable": (
                "both services standard AMD VMs vs both services AMD SEV-SNP confidential VMs"
                if summaries.get(CONFIDENTIAL_KEY, {}).get("tee_scope") == "full_2svc"
                else "service2 standard AMD VM vs service2 AMD SEV-SNP confidential VM"
            ),
            "fixed_segment": (
                None
                if summaries.get(CONFIDENTIAL_KEY, {}).get("tee_scope") == "full_2svc"
                else "service1 remained on Standard_D8as_v5"
            ),
            "baseline": (
                "standard two-service chain"
                if summaries.get(CONFIDENTIAL_KEY, {}).get("tee_scope") == "full_2svc"
                else "standard service2"
            ),
            "variant": "full TEE" if summaries.get(CONFIDENTIAL_KEY, {}).get("tee_scope") == "full_2svc" else "confidential service2",
        },
    }
    (output_dir / "rq22_analysis_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(output_dir / "rq22_analysis_summary.md", payload)
    payload["plots"] = generate_plots(output_dir, rows, deltas)
    (output_dir / "rq22_analysis_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    args = parse_args()
    try:
        artifact_dir = Path(args.artifact_dir).resolve() if args.artifact_dir else latest_artifact(Path(args.results_root).resolve())
        output_dir = Path(args.output_dir).resolve() if args.output_dir else artifact_dir / "analysis"
        payload = analyze(artifact_dir, output_dir)
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote RQ2.2 analysis artifacts to {output_dir}")
    comparison = payload.get("comparison") or {}
    if comparison.get("available"):
        label = (
            "Full-TEE"
            if (payload.get("conditions") or {}).get(CONFIDENTIAL_KEY, {}).get("tee_scope") == "full_2svc"
            else "Confidential service2"
        )
        print(
            f"{label} mean latency delta: "
            f"{format_float(comparison.get('mean_latency_delta_ms'))} ms "
            f"({format_float(comparison.get('mean_latency_delta_pct'))}%)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
