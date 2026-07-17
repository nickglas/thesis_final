# RQ1.2 fine-grained refinement Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_2_20260515_112636/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.2 fine-grained refinement |
| description | Block-level refinement within the late-stage coarse region (layer2–layer3) carried forward from RQ1.1. Tests whether splitting within layer3 at a finer architectural boundary reveals latency differences not visible at coarse stage boundaries, while controlling for identical activation sizes. |

### Model

| Setting | Value |
|---|---|
| name | resnet18 |
| pretrained | true |
| device | cpu |
| input_shape | 1, 3, 224, 224 |
| precision | fp32 |

### Benchmark

| Setting | Value |
|---|---|
| rounds | 5 |
| warmup_iterations | 50 |
| measured_iterations | 200 |
| cooldown_seconds | 5 |
| seed | 42 |

### Grpc

| Setting | Value |
|---|---|
| host | 127.0.0.1 |
| port | 50051 |
| max_message_bytes | 16777216 |

### Carry Forward

| Setting | Value |
|---|---|
| near_best_window_pct | 5.0 |
| degeneracy_threshold_pct | 10.0 |

### Parity

| Setting | Value |
|---|---|
| atol | 1e-05 |
| num_inputs | 5 |

### Warmup Calibration

| Setting | Value |
|---|---|
| window | 10 |
| cv_threshold | 0.02 |
| max_extra_iterations | -1 |

### Cpu Stabilisation

| Setting | Value |
|---|---|
| threading.pytorch_intra_op | 1 |
| threading.pytorch_inter_op | 1 |
| threading.omp_num_threads | 1 |
| threading.mkl_num_threads | 1 |
| threading.openblas_num_threads | 1 |
| affinity.enabled | true |
| affinity.num_cores | 1 |
| affinity.avoid_smt | true |
| affinity.explicit_cpus | n/a |
| priority.enabled | true |
| priority.nice_value | -5 |
| governor.set_governor | true |
| governor.requested_mode | performance |
| turbo.disable_turbo | true |

### Conditions

| Condition | Type | Split After | Chain Split Points |
|---|---|---|---|
| monolithic | monolithic | n/a | n/a |
| split_after_layer2 | split | layer2 | n/a |
| split_after_layer3_block0 | split | layer3.0 | n/a |
| split_after_layer3 | split | layer3 | n/a |

## Environment Used

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_2_20260515_112636/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T11:26:36.342033 |
| platform | Linux-6.17.0-23-generic-x86_64-with-glibc2.39 |
| processor | x86_64 |
| python_version | 3.12.3 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | 6b152f6e377d71747641c351acc99b3c44b2ceec |

### CPU Stabilisation Observed

| Setting | Value |
|---|---|
| threading.requested.pytorch_intra_op | 1 |
| threading.requested.pytorch_inter_op | 1 |
| threading.requested.omp_num_threads | 1 |
| threading.requested.mkl_num_threads | 1 |
| threading.requested.openblas_num_threads | 1 |
| threading.applied.pytorch_intra_op | 1 |
| threading.applied.pytorch_inter_op | 1 |
| threading.applied.omp_num_threads | 1 |
| threading.applied.mkl_num_threads | 1 |
| threading.applied.openblas_num_threads | 1 |
| affinity.requested.enabled | true |
| affinity.requested.num_cores | 1 |
| affinity.requested.avoid_smt | true |
| affinity.requested.explicit_cpus | n/a |
| affinity.detected.physical_cores_available | 0, 2, 4, 6, 8, 10, 12, 14 |
| affinity.detected.total_cpus | 16 |
| affinity.applied | true |
| affinity.applied_cores | 0 |
| affinity.method | auto-detected physical cores (SMT excluded), first 1 |
| priority.requested.enabled | true |
| priority.requested.nice_value | -5 |
| priority.detected.current_nice | 0 |
| priority.applied | true |
| priority.applied_nice | -5 |
| priority.method | sudo |
| governor.requested.set_governor | true |
| governor.requested.requested_mode | performance |
| governor.detected | performance |
| governor.applied | true |
| governor.applied_mode | performance |
| governor.method | sudo |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 0 |
| turbo.detected.turbo_enabled | false |
| turbo.applied | true |
| turbo.applied_value | 0 |
| turbo.method | sudo |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| split_after_layer3_block0 | 1000 | 80.157 | 79.379 | 2.564 | 87.368 | [79.998, 80.316] | 2.592 | 3.3% | n/a | n/a | n/a |
| split_after_layer3 | 1000 | 80.392 | 79.687 | 2.475 | 87.203 | [80.238, 80.545] | 2.826 | 3.6% | n/a | n/a | n/a |
| split_after_layer2 | 1000 | 80.348 | 79.570 | 2.510 | 87.332 | [80.192, 80.504] | 2.783 | 3.6% | n/a | n/a | n/a |
| monolithic | 1000 | 77.565 | 75.641 | 3.663 | 84.035 | [77.338, 77.792] | 0.000 | 0.0% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 77.433 | 75.448 | 3.614 | 83.691 |
| 1 | split_after_layer2 | 200 | 79.882 | 79.432 | 1.704 | 83.935 |
| 1 | split_after_layer3 | 200 | 79.938 | 79.536 | 1.657 | 83.239 |
| 1 | split_after_layer3_block0 | 200 | 79.224 | 78.989 | 1.223 | 80.365 |
| 2 | monolithic | 200 | 77.405 | 75.509 | 3.543 | 83.927 |
| 2 | split_after_layer2 | 200 | 80.237 | 79.321 | 2.769 | 87.493 |
| 2 | split_after_layer3 | 200 | 80.619 | 79.890 | 2.450 | 87.678 |
| 2 | split_after_layer3_block0 | 200 | 80.151 | 79.269 | 2.708 | 87.083 |
| 3 | monolithic | 200 | 77.663 | 75.667 | 3.745 | 84.316 |
| 3 | split_after_layer2 | 200 | 80.333 | 79.620 | 2.451 | 87.273 |
| 3 | split_after_layer3 | 200 | 80.430 | 79.686 | 2.434 | 87.244 |
| 3 | split_after_layer3_block0 | 200 | 80.684 | 79.706 | 2.875 | 88.391 |
| 4 | monolithic | 200 | 77.647 | 75.792 | 3.716 | 83.911 |
| 4 | split_after_layer2 | 200 | 80.389 | 79.501 | 2.615 | 87.805 |
| 4 | split_after_layer3 | 200 | 80.430 | 79.729 | 2.361 | 87.212 |
| 4 | split_after_layer3_block0 | 200 | 80.243 | 79.339 | 2.663 | 87.463 |
| 5 | monolithic | 200 | 77.678 | 75.703 | 3.719 | 84.162 |
| 5 | split_after_layer2 | 200 | 80.900 | 79.942 | 2.769 | 87.594 |
| 5 | split_after_layer3 | 200 | 80.540 | 79.612 | 3.197 | 87.839 |
| 5 | split_after_layer3_block0 | 200 | 80.483 | 79.603 | 2.750 | 87.943 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 77.565 | 0.1342 | 0.2733 | 0.0017 |
| split_after_layer2 | 5 | 80.348 | 0.3660 | 1.0177 | 0.0046 |
| split_after_layer3 | 5 | 80.392 | 0.2658 | 0.6811 | 0.0033 |
| split_after_layer3_block0 | 5 | 80.157 | 0.5616 | 1.4600 | 0.0070 |

## Overhead vs monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| split_after_layer3_block0 | 2.592 | 3.3% | 196.0 | 33.971 |
| split_after_layer3 | 2.826 | 3.6% | 196.0 | 26.164 |
| split_after_layer2 | 2.783 | 3.6% | 392.0 | 40.863 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer3_block0 | 0.820 | large | 251069.0 | 8.34e-83 |
| split_after_layer3 | 0.904 | large | 250832.0 | 5.85e-83 |
| split_after_layer2 | 0.886 | large | 249002.0 | 3.73e-84 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer3_block0 (80.157 ms)
- **Near-best window:** 5.0% → threshold 84.165 ms
- **Near-best candidates:** split_after_layer3_block0, split_after_layer3, split_after_layer2
- **Degenerate candidates:** None
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3_block0 (80.157 ms)
- **Selected reference candidate:** split_after_layer2 (80.348 ms)
- **Rejected:** split_after_layer3
- **Fallback used:** False

## Carry-Forward Rule (as implemented)

1. Identify `raw_fastest`: split with lowest mean end-to-end latency.
2. Near-best window: all splits within 5.0% of `raw_fastest` mean.
3. Degeneracy filter: exclude candidates where the minor compute side contributes < 10.0% of total split compute (`service_a` + `service_b`).
4. If non-degenerate near-best candidates exist: select `selected_main` by (`mean_ms`, `activation_bytes`), with `selected_reference` as runner-up.
5. If ALL near-best candidates are degenerate: `selected_main = None`, `selected_reference = raw_fastest` (reference only, not promoted).
6. Tie-break: prefer lower `activation_bytes_mean`.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** The selection rule is predeclared and fully explicit. No hidden fallback promotes degenerate candidates to `selected_main`.
