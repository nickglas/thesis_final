import pytest

from src.analysis.statistics import (
    compute_cross_stage_comparison,
    compute_normalized_reference_estimates,
    enrich_condition_summaries,
)


def test_enrich_condition_summaries_adds_baseline_metrics():
    summaries = [
        {"condition": "monolithic_k8s_1svc", "mean_ms": 50.0, "n": 10},
        {"condition": "chain_2svc", "mean_ms": 60.0, "n": 10},
        {"condition": "chain_3svc", "mean_ms": 65.0, "n": 10},
    ]

    enriched = enrich_condition_summaries(summaries)

    baseline = enriched[0]
    assert baseline["baseline_condition"] == "monolithic_k8s_1svc"
    assert baseline["absolute_overhead_ms"] == 0.0
    assert baseline["pct_overhead_vs_baseline"] == 0.0
    assert baseline["latency_rank"] == 1

    chain_3svc = enriched[2]
    assert chain_3svc["absolute_overhead_ms"] == 15.0
    assert chain_3svc["pct_overhead_vs_baseline"] == 30.0
    assert chain_3svc["latency_rank"] == 3


def test_normalized_reference_estimates_scale_to_current_baseline():
    current = [
        {"condition": "monolithic_k8s_1svc", "mean_ms": 56.0},
        {"condition": "chain_2svc", "mean_ms": 60.0},
    ]
    reference = [
        {"condition": "monolithic_k8s_1svc", "total_compute_ms_mean": 80.0},
        {"condition": "chain_2svc", "total_compute_ms_mean": 88.0},
    ]

    estimates = compute_normalized_reference_estimates(current, reference)

    assert estimates["monolithic_k8s_1svc"] == 56.0
    assert estimates["chain_2svc"] == pytest.approx(61.6)


def test_cross_stage_comparison_preserves_rank_and_overhead_columns():
    current = enrich_condition_summaries(
        [
            {"condition": "monolithic_k8s_1svc", "mean_ms": 56.0},
            {"condition": "chain_2svc", "mean_ms": 60.0},
        ]
    )
    reference = enrich_condition_summaries(
        [
            {"condition": "monolithic_k8s_1svc", "mean_ms": 81.0},
            {"condition": "chain_2svc", "mean_ms": 84.0},
        ]
    )

    comparison = compute_cross_stage_comparison(
        current,
        reference,
        current_label="aks",
        reference_label="local_k8s",
    )

    assert comparison == [
        {
            "condition": "monolithic_k8s_1svc",
            "local_k8s_mean_ms": 81.0,
            "aks_mean_ms": 56.0,
            "local_k8s_overhead_pct_vs_baseline": 0.0,
            "aks_overhead_pct_vs_baseline": 0.0,
            "local_k8s_rank": 1,
            "aks_rank": 1,
            "rank_delta": 0,
            "rank_match": True,
        },
        {
            "condition": "chain_2svc",
            "local_k8s_mean_ms": 84.0,
            "aks_mean_ms": 60.0,
            "local_k8s_overhead_pct_vs_baseline": 3.7037037037037033,
            "aks_overhead_pct_vs_baseline": 7.142857142857142,
            "local_k8s_rank": 2,
            "aks_rank": 2,
            "rank_delta": 0,
            "rank_match": True,
        },
    ]