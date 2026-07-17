"""Visualization for RQ1.x results.

Generates:
  - Latency box plot
  - Latency violin plot
  - Overhead vs activation-transfer burden scatter
  - Per-iteration stationarity time-series
"""

import os
import csv
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from typing import Dict, List, Any


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _load_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            for key in row:
                if key in ("round", "iteration", "num_hops") or key.endswith("_bytes"):
                    try:
                        row[key] = int(float(row[key]))
                    except (ValueError, TypeError):
                        pass
                elif key != "condition":
                    try:
                        row[key] = float(row[key])
                    except (ValueError, TypeError):
                        pass
            rows.append(row)
    return rows


def _condition_label(name: str) -> str:
    return name.replace("split_after_", "").replace("_", " ")


# ------------------------------------------------------------------
# Plots
# ------------------------------------------------------------------

def plot_latency_boxplot(rows: List[Dict], output_path: str):
    conditions = []
    seen = set()
    for r in rows:
        c = r["condition"]
        if c not in seen:
            conditions.append(c)
            seen.add(c)

    data = [[r["end_to_end_ms"] for r in rows if r["condition"] == c]
            for c in conditions]
    labels = [_condition_label(c) for c in conditions]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(data, labels=labels, patch_artist=True)
    ax.set_ylabel("End-to-end latency (ms)")
    ax.set_title("Latency by Condition")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_latency_violin(rows: List[Dict], output_path: str):
    conditions = []
    seen = set()
    for r in rows:
        c = r["condition"]
        if c not in seen:
            conditions.append(c)
            seen.add(c)

    data = [[r["end_to_end_ms"] for r in rows if r["condition"] == c]
            for c in conditions]
    labels = [_condition_label(c) for c in conditions]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.violinplot(data, showmeans=True, showmedians=True)
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_ylabel("End-to-end latency (ms)")
    ax.set_title("Latency Distribution by Condition")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_overhead_vs_activation(cross_condition: List[Dict], output_path: str):
    if not cross_condition:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    for cc in cross_condition:
        label = _condition_label(cc["condition"])
        act_kb = float(cc["activation_bytes"]) / 1024
        overhead = float(cc["overhead_ms"])
        ax.scatter(act_kb, overhead, s=100, zorder=5)
        ax.annotate(label, (act_kb, overhead),
                    textcoords="offset points", xytext=(8, 4))

    ax.set_xlabel("Activation transfer (KB)")
    ax.set_ylabel("Overhead vs monolithic (ms)")
    ax.set_title("Overhead vs Activation-Transfer Burden")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_stationarity(rows: List[Dict], output_path: str):
    conditions = []
    seen = set()
    for r in rows:
        c = r["condition"]
        if c not in seen:
            conditions.append(c)
            seen.add(c)

    n_conds = len(conditions)
    fig, axes = plt.subplots(n_conds, 1, figsize=(12, 3 * n_conds), sharex=False)
    if n_conds == 1:
        axes = [axes]

    for ax, cond in zip(axes, conditions):
        cond_rows = sorted(
            [r for r in rows if r["condition"] == cond],
            key=lambda r: (r["round"], r["iteration"]),
        )
        latencies = [r["end_to_end_ms"] for r in cond_rows]
        ax.plot(latencies, linewidth=0.5, alpha=0.7)
        ax.set_ylabel("Latency (ms)")
        ax.set_title(_condition_label(cond))
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Iteration (global)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def generate_all_plots(results_dir: str, output_dir: str = None):
    if output_dir is None:
        output_dir = results_dir

    raw_path = os.path.join(results_dir, "raw_iterations.csv")
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    rows = _load_csv(raw_path)

    plot_latency_boxplot(rows, os.path.join(plots_dir, "latency_boxplot.png"))
    plot_latency_violin(rows, os.path.join(plots_dir, "latency_violin.png"))
    plot_stationarity(rows, os.path.join(plots_dir, "stationarity.png"))

    # Overhead-vs-activation requires cross_condition.csv
    cc_path = os.path.join(output_dir, "cross_condition.csv")
    if os.path.exists(cc_path):
        cross_condition = _load_csv(cc_path)
        plot_overhead_vs_activation(
            cross_condition,
            os.path.join(plots_dir, "overhead_vs_activation.png"),
        )
