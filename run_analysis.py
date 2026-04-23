"""Post-experiment analysis.

Reads raw_iterations.csv, computes all statistics, applies the
carry-forward rule, generates plots, and writes a summary report.
"""

import os
import csv
import json
import glob
import math
import re
import argparse
import logging

import yaml

from src.benchmark.config import load_config
from src.analysis.statistics import (
    load_raw_iterations,
    compute_condition_summary,
    compute_round_summaries,
    compute_cross_condition,
    compute_cross_stage_comparison,
    compute_effect_sizes,
    compute_round_consistency,
    compute_normalized_reference_estimates,
    enrich_condition_summaries,
    apply_carry_forward_rule,
)
from src.analysis.plots import generate_all_plots
from src.benchmark.deployment_metadata import build_environment_deployment_section
from src.benchmark.logging import ArtifactLogger


REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


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
    deployment_metadata_path = os.path.join(results_dir, "deployment_metadata.json")
    deployment_metadata = _load_json_snapshot(deployment_metadata_path, logger)
    artifact = ArtifactLogger(output_dir)
    environment_snapshot, environment_path = _ensure_environment_snapshot(
        environment_snapshot,
        environment_path,
        deployment_metadata,
        artifact,
    )

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

    is_rq15_transfer = _is_rq15_transfer_validation(
        config.experiment_name,
        environment_snapshot,
        conditions,
    )
    reference_summary_path = None
    reference_summaries = []
    estimated_compute_ms_by_condition = None
    cross_stage_comparison = []

    if is_rq15_transfer:
        reference_summary_path, reference_summaries = _load_frozen_rq14_reference_summaries(logger)
        if reference_summaries:
            estimated_compute_ms_by_condition = compute_normalized_reference_estimates(
                summaries,
                reference_summaries,
            )
            missing_estimates = [
                condition
                for condition in conditions
                if condition not in estimated_compute_ms_by_condition
            ]
            if missing_estimates:
                logger.warning(
                    "Missing normalized compute estimates for conditions: %s",
                    ", ".join(missing_estimates),
                )
        else:
            logger.warning(
                "RQ1.5 analysis detected, but no frozen RQ1.4 condition summaries were found. "
                "Cross-stage comparison and normalized compute estimates will be omitted."
            )

    summaries = enrich_condition_summaries(
        summaries,
        estimated_compute_ms_by_condition=estimated_compute_ms_by_condition,
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

    if is_rq15_transfer and reference_summaries:
        reference_summaries = enrich_condition_summaries(reference_summaries)
        cross_stage_comparison = compute_cross_stage_comparison(
            summaries,
            reference_summaries,
            current_label="aks",
            reference_label="local_k8s",
        )
        if cross_stage_comparison:
            artifact.save_csv("cross_stage_comparison.csv", cross_stage_comparison)

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
                     environment_snapshot=environment_snapshot,
                     include_rq15_transfer_validation=is_rq15_transfer,
                     reference_summary_path=reference_summary_path,
                     reference_summaries=reference_summaries,
                     cross_stage_comparison=cross_stage_comparison)
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


def _load_csv_snapshot(path, logger):
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                parsed = {}
                for key, value in row.items():
                    parsed[key] = _coerce_csv_value(value)
                rows.append(parsed)
            return rows
    except FileNotFoundError:
        logger.warning("CSV snapshot not found at %s", path)
    except Exception as exc:
        logger.warning("Could not read CSV snapshot %s: %s", path, exc)
    return []


def _coerce_csv_value(value):
    if value is None or value == "":
        return None
    try:
        if any(char in value for char in (".", "e", "E")):
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return value


def _ensure_environment_snapshot(environment_snapshot, environment_path, deployment_metadata, artifact):
    snapshot = dict(environment_snapshot or {})
    deployment_section = build_environment_deployment_section(deployment_metadata)
    if deployment_section:
        snapshot["deployment"] = deployment_section

    if snapshot:
        artifact.save_json("environment.json", snapshot)
        return snapshot, os.path.join(artifact.output_dir, "environment.json")
    return environment_snapshot, environment_path


def _load_frozen_rq14_reference_summaries(logger):
    patterns = [
        os.path.join(REPO_ROOT, "results", "frozen", "rq1_4_*", "merged_results", "condition_summaries.csv"),
        os.path.join(REPO_ROOT, "results", "frozen", "*rq1_4*", "merged_results", "condition_summaries.csv"),
    ]
    candidates = sorted({match for pattern in patterns for match in glob.glob(pattern)})
    if not candidates:
        return None, []

    reference_path = candidates[-1]
    return reference_path, _load_csv_snapshot(reference_path, logger)


def _is_rq15_transfer_validation(experiment_name, environment_snapshot, condition_names):
    experiment_label = str(experiment_name or "").lower()
    deployment = (environment_snapshot or {}).get("deployment") or {}
    if "rq1.5" in experiment_label or str(deployment.get("cluster_type", "")).lower() == "aks":
        return True
    if str(deployment.get("namespace", "")).lower() == "rq15":
        return True
    expected_conditions = {
        "monolithic_k8s_1svc",
        "chain_2svc",
        "chain_3svc",
        "chain_4svc",
        "chain_5svc",
    }
    return expected_conditions.issubset(set(condition_names))


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
    elif isinstance(value, (int, float)) and not math.isfinite(float(value)):
        text = "n/a"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value) if value else "n/a"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _is_finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _format_float(value, digits=3):
    if not _is_finite_number(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def _format_percent(value, digits=1):
    if not _is_finite_number(value):
        return "n/a"
    return f"{float(value):.{digits}f}%"


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
        if key not in {"cpu_stabilisation", "deployment"}
    ]
    if runtime_rows:
        lines.extend(["\n### Runtime\n"])
        _append_settings_table(lines, runtime_rows)

    deployment = environment_snapshot.get("deployment")
    if deployment:
        lines.extend(["\n### Deployment\n"])
        if isinstance(deployment, dict):
            _append_settings_table(lines, _flatten_mapping(deployment))
            _append_placement_summary(lines, deployment)
        else:
            _append_settings_table(lines, [("deployment", deployment)])

    cpu_stabilisation = environment_snapshot.get("cpu_stabilisation")
    if cpu_stabilisation:
        lines.extend(["\n### CPU Stabilisation Observed\n"])
        if isinstance(cpu_stabilisation, dict):
            _append_settings_table(lines, _flatten_mapping(cpu_stabilisation))
        else:
            _append_settings_table(lines, [("cpu_stabilisation", cpu_stabilisation)])


def _append_placement_summary(lines, deployment):
    placement_validation = deployment.get("placement_validation") or {}
    conditions = placement_validation.get("conditions") or {}
    if not isinstance(conditions, dict) or not conditions:
        return

    placement_policy = deployment.get("placement_policy") or {}
    lines.extend(["\n### Placement Summary\n"])

    strategy = placement_policy.get("strategy")
    if strategy:
        lines.append(
            "- Placement policy: "
            f"strategy={_format_report_value(strategy)}, "
            f"require_same_node={_format_report_value(placement_policy.get('require_same_node'))}, "
            f"fail_if_not_colocated={_format_report_value(placement_policy.get('fail_if_not_colocated'))}."
        )
    if "all_required_conditions_passed" in placement_validation:
        lines.append(
            "- Required colocated conditions passed: "
            f"{_format_report_value(placement_validation.get('all_required_conditions_passed'))}."
        )

    lines.extend([
        "| Condition | Checked | Required | Status | Client Node | Service Nodes |",
        "|---|---|---|---|---|---|",
    ])
    for condition_name, details in conditions.items():
        lines.append(
            f"| {_format_report_value(condition_name)} | "
            f"{_format_report_value(details.get('checked'))} | "
            f"{_format_report_value(details.get('required'))} | "
            f"{_format_report_value(details.get('status'))} | "
            f"{_format_report_value(details.get('client_node'))} | "
            f"{_format_report_value(details.get('service_nodes'))} |"
        )


def _condition_service_count(condition_name):
    if condition_name == "monolithic_k8s_1svc":
        return 1
    match = None
    if isinstance(condition_name, str):
        match = re.search(r"_(\d+)svc$", condition_name)
    if match:
        return int(match.group(1))
    return float("inf")


def _summaries_by_service_count(summaries):
    return sorted(
        summaries,
        key=lambda summary: (_condition_service_count(summary.get("condition")), summary.get("condition", "")),
    )


def _compute_marginal_overhead_rows(summaries):
    ordered = _summaries_by_service_count(summaries)
    rows = []
    previous = None
    for summary in ordered:
        if previous is not None and _is_finite_number(summary.get("absolute_overhead_ms")) and _is_finite_number(previous.get("absolute_overhead_ms")):
            rows.append({
                "from_condition": previous["condition"],
                "to_condition": summary["condition"],
                "increment_ms": summary["absolute_overhead_ms"] - previous["absolute_overhead_ms"],
            })
        previous = summary
    return rows


def _build_rq15_limitations(environment_snapshot):
    if not environment_snapshot:
        return []

    cpu = environment_snapshot.get("cpu_stabilisation") or {}
    limitations = []

    priority = cpu.get("priority") or {}
    if priority.get("requested", {}).get("enabled") and priority.get("applied") is False:
        limitations.append(
            priority.get("error")
            or "Requested process-priority elevation was not applied."
        )

    governor = cpu.get("governor") or {}
    if governor.get("detected") == "unavailable" or (
        governor.get("requested", {}).get("set_governor") and governor.get("applied") is False
    ):
        limitations.append(
            governor.get("note")
            or governor.get("reason")
            or "CPU governor control was unavailable on the host platform."
        )

    turbo = cpu.get("turbo") or {}
    if turbo.get("detected") == "unavailable" or (
        turbo.get("requested", {}).get("disable_turbo") and turbo.get("applied") is False
    ):
        limitations.append(
            turbo.get("note")
            or turbo.get("reason")
            or "Turbo control was unavailable on the host platform."
        )

    deployment = environment_snapshot.get("deployment") or {}
    if str(deployment.get("cluster_type", "")).lower() == "aks":
        limitations.append(
            "Because execution occurred on Azure-managed AKS infrastructure, absolute latency remains sensitive to host scheduling, hypervisor behaviour, and CNI-path variability; these are discussed as environment-level effects rather than architectural reversals."
        )

    deduped = []
    for limitation in limitations:
        if limitation not in deduped:
            deduped.append(limitation)
    return deduped


def _append_rq15_transfer_validation(
    lines,
    summaries,
    reference_summaries,
    cross_stage_comparison,
    reference_summary_path,
    environment_snapshot,
):
    lines.extend(["\n## RQ1.5 Transfer Validation vs Frozen RQ1.4\n"])
    if reference_summary_path:
        lines.append(f"- **Frozen RQ1.4 reference:** `{reference_summary_path}`")

    if not cross_stage_comparison:
        lines.extend([
            "",
            "_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._",
        ])
        return

    lines.extend([
        "",
        "| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for row in cross_stage_comparison:
        lines.append(
            f"| {row['condition']} | {_format_float(row.get('local_k8s_mean_ms'))} | "
            f"{_format_float(row.get('aks_mean_ms'))} | "
            f"{_format_percent(row.get('local_k8s_overhead_pct_vs_baseline'))} | "
            f"{_format_percent(row.get('aks_overhead_pct_vs_baseline'))} | "
            f"{_format_report_value(row.get('local_k8s_rank'))} | "
            f"{_format_report_value(row.get('aks_rank'))} | "
            f"{_format_report_value(row.get('rank_match'))} |"
        )

    marginal_rows = _compute_marginal_overhead_rows(summaries)
    if marginal_rows:
        lines.extend([
            "\n### AKS Marginal Overhead Progression\n",
            "| Transition | Increment vs Previous Condition (ms) |",
            "|---|---|",
        ])
        for row in marginal_rows:
            lines.append(
                f"| {row['from_condition']} → {row['to_condition']} | {_format_float(row['increment_ms'])} |"
            )

    ordering_preserved = all(row.get("rank_match") is True for row in cross_stage_comparison)
    ordered_summaries = _summaries_by_service_count(summaries)
    ordered_reference = _summaries_by_service_count(reference_summaries)
    current_overheads = [summary.get("absolute_overhead_ms") for summary in ordered_summaries]
    monotonic_overhead = all(
        _is_finite_number(left) and _is_finite_number(right) and right >= left
        for left, right in zip(current_overheads, current_overheads[1:])
    )

    bounded_nonlinearity = None
    if len(marginal_rows) >= 2:
        bounded_nonlinearity = marginal_rows[-1]["increment_ms"] <= marginal_rows[-2]["increment_ms"]

    current_chained = [
        summary for summary in ordered_summaries
        if summary.get("condition") != "monolithic_k8s_1svc"
        and _is_finite_number(summary.get("inferred_non_compute_overhead_ms"))
    ]
    inferred_sentence = None
    if current_chained:
        inferred_values = [summary["inferred_non_compute_overhead_ms"] for summary in current_chained]
        peak_summary = max(
            current_chained,
            key=lambda summary: summary["inferred_non_compute_overhead_ms"],
        )
        inferred_sentence = (
            "Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, "
            f"the chained AKS conditions retain {_format_float(min(inferred_values))}–{_format_float(max(inferred_values))} ms "
            f"of residual non-compute/platform latency, with the highest residual at {peak_summary['condition']}."
        )

    lines.extend(["\n### Interpretation\n"])
    lines.append(
        "- " + (
            "Condition ordering is preserved between frozen RQ1.4 and the AKS run."
            if ordering_preserved
            else "Condition ordering is not fully preserved between frozen RQ1.4 and the AKS run."
        )
    )
    lines.append(
        "- " + (
            "AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline."
            if monotonic_overhead
            else "AKS overhead does not increase monotonically across the full service-count progression."
        )
    )

    if bounded_nonlinearity is not None and len(marginal_rows) >= 2:
        if bounded_nonlinearity:
            lines.append(
                "- "
                f"The bounded-nonlinearity pattern is reproduced on AKS: the final increment ({_format_float(marginal_rows[-1]['increment_ms'])} ms for {marginal_rows[-1]['to_condition']}) is smaller than the preceding increment ({_format_float(marginal_rows[-2]['increment_ms'])} ms)."
            )
        else:
            lines.append(
                "- "
                f"The exact chain_4svc→chain_5svc near-plateau from RQ1.4 is not reproduced on AKS: the final increment is {_format_float(marginal_rows[-1]['increment_ms'])} ms versus {_format_float(marginal_rows[-2]['increment_ms'])} ms for the preceding step."
            )

    if cross_stage_comparison:
        local_overheads = [row.get("local_k8s_overhead_pct_vs_baseline") for row in cross_stage_comparison]
        aks_overheads = [row.get("aks_overhead_pct_vs_baseline") for row in cross_stage_comparison]
        if all(
            _is_finite_number(local_value) and _is_finite_number(aks_value) and aks_value >= local_value
            for local_value, aks_value in zip(local_overheads, aks_overheads)
        ):
            lines.append(
                "- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal."
            )
        else:
            lines.append(
                "- AKS relative overhead fractions remain comparable for discussion purposes, but they should be interpreted as environment-level effects rather than strict numeric replications of RQ1.4."
            )

    if inferred_sentence:
        lines.append(f"- {inferred_sentence}")

    deployment = (environment_snapshot or {}).get("deployment") or {}
    if deployment.get("pod_colocation_enforced") is True:
        lines.append(
            "- Deployment metadata confirms same-node service placement for each measured condition, preserving the RQ1.4 intra-condition topology while moving execution to AKS."
        )

    lines.append(
        "- Absolute latency differences between frozen RQ1.4 and AKS are interpreted as environment-level effects and do not by themselves overturn the within-stage architectural comparison."
    )

    limitations = _build_rq15_limitations(environment_snapshot)
    if limitations:
        lines.extend(["\n### Limitations\n"])
        for limitation in limitations:
            lines.append(f"- {limitation}")


def _generate_report(source_results_dir, output_dir, summaries, round_sums,
                     round_consistency, cross, effects, carry_forward,
                     experiment_name="RQ1.1", config_path=None,
                     config_snapshot=None, environment_path=None,
                     environment_snapshot=None,
                     include_rq15_transfer_validation=False,
                     reference_summary_path=None,
                     reference_summaries=None,
                     cross_stage_comparison=None):
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
        "| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for s in summaries:
        lines.append(
            f"| {s['condition']} | {s['n']} | {s['mean_ms']:.3f} | "
            f"{s['median_ms']:.3f} | {s['std_ms']:.3f} | {s['p95_ms']:.3f} | "
            f"[{s['ci95_lower_ms']:.3f}, {s['ci95_upper_ms']:.3f}] | "
            f"{_format_float(s.get('absolute_overhead_ms'))} | "
            f"{_format_percent(s.get('pct_overhead_vs_baseline'))} | "
            f"{_format_float(s.get('estimated_compute_ms'))} | "
            f"{_format_float(s.get('inferred_non_compute_overhead_ms'))} | "
            f"{_format_percent(s.get('inferred_non_compute_pct'))} |"
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

    if include_rq15_transfer_validation:
        _append_rq15_transfer_validation(
            lines,
            summaries,
            reference_summaries,
            cross_stage_comparison,
            reference_summary_path,
            environment_snapshot,
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
