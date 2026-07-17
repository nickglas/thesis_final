import csv
import json
from pathlib import Path

import scripts.analyze_rq22_confidential as rq22_analysis


def write_raw_iterations(path: Path, latencies: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "round",
        "condition",
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
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, latency in enumerate(latencies, start=1):
            writer.writerow(
                {
                    "round": 1,
                    "condition": path.parent.parent.name,
                    "iteration": index,
                    "end_to_end_ms": latency,
                    "total_compute_ms": latency - 2.0,
                    "non_compute_overhead_ms": 2.0,
                    "total_activation_bytes": 128,
                    "num_hops": 2,
                    "hop_1_compute_ms": 20.0,
                    "hop_1_forward_ms": 1.0,
                    "hop_2_compute_ms": latency - 23.0,
                    "hop_2_forward_ms": latency - 2.0,
                }
            )


def completed_record(
    benchmark_dir: Path,
    *,
    condition_key: str,
    condition_name: str,
    service2_nodepool: str,
    service2_vm_size: str,
) -> dict[str, object]:
    return {
        "pass": 1,
        "execution_index": 1 if condition_key == "standard" else 2,
        "condition_key": condition_key,
        "condition_name": condition_name,
        "service2_nodepool": service2_nodepool,
        "service2_vm_size": service2_vm_size,
        "service2_zone": "1",
        "benchmark_dir": str(benchmark_dir),
        "manifest_dir": str(benchmark_dir.parent / "manifests"),
    }


def test_rq22_analyzer_aggregates_condition_and_paired_delta(tmp_path: Path, monkeypatch):
    artifact = tmp_path / "rq2_2_confidential_test"
    standard_benchmark = artifact / "conditions" / "pass01_standard" / "benchmark"
    confidential_benchmark = artifact / "conditions" / "pass01_confidential" / "benchmark"
    write_raw_iterations(standard_benchmark / "raw_iterations.csv", [10.0, 12.0])
    write_raw_iterations(confidential_benchmark / "raw_iterations.csv", [12.0, 14.0])

    summary = {
        "status": "completed",
        "effective_image_ref": "acr.azurecr.io/thesis-inference@sha256:test",
        "execution_plan": {
            "paired_passes": 1,
            "order": "standard-first",
            "passes": [{"pass": 1, "order": ["standard", "confidential"]}],
        },
        "completed": [
            completed_record(
                standard_benchmark,
                condition_key="standard",
                condition_name="chain_2svc_mtls_standard",
                service2_nodepool="r22s2std",
                service2_vm_size="Standard_D8as_v5",
            ),
            completed_record(
                confidential_benchmark,
                condition_key="confidential",
                condition_name="chain_2svc_mtls_confidential_service2",
                service2_nodepool="r22s2cvm",
                service2_vm_size="Standard_DC8as_v5",
            ),
        ],
    }
    artifact.mkdir(parents=True, exist_ok=True)
    (artifact / "rq22_rolling_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    monkeypatch.setattr(rq22_analysis, "generate_plots", lambda *_args: [])

    payload = rq22_analysis.analyze(artifact, artifact / "analysis")

    assert payload["requirements"]["standard_runs"] == 2
    assert payload["requirements"]["confidential_runs"] == 2
    assert payload["comparison"]["mean_latency_delta_ms"] == 2.0
    assert payload["comparison"]["mean_latency_delta_pct"] == 100.0 * 2.0 / 11.0
    assert payload["paired_pass_deltas"][0]["execution_order"] == "standard->confidential"
    assert payload["paired_pass_deltas"][0]["delta_mean_ms"] == 2.0
    assert (artifact / "analysis" / "rq22_raw_iterations.csv").exists()
    assert (artifact / "analysis" / "rq22_analysis_summary.md").exists()
