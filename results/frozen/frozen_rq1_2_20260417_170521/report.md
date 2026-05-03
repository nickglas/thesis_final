# RQ1.2 fine-grained refinement Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_2_20260417_170521/config.yaml`

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

| Condition | Type | Split After |
|---|---|---|
| monolithic | monolithic | n/a |
| split_after_layer2 | split | layer2 |
| split_after_layer3_block0 | split | layer3.0 |
| split_after_layer3 | split | layer3 |

## Environment Used

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_2_20260417_170521/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-04-17T17:05:21.020946 |
| platform | Linux-6.17.0-20-generic-x86_64-with-glibc2.39 |
| processor | x86_64 |
| python_version | 3.12.3 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | 0df2ac36e4b8b803cfd8e75952cabcbe63355975 |

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
| governor.requested.set_governor | true |
| governor.requested.requested_mode | performance |
| governor.detected | performance |
| governor.applied | true |
| governor.applied_mode | performance |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 0 |
| turbo.detected.turbo_enabled | false |
| turbo.applied | true |
| turbo.applied_value | 0 |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| split_after_layer3_block0 | 1000 | 78.691 | 77.999 | 2.715 | 85.942 | [78.523, 78.860] |
| split_after_layer3 | 1000 | 78.853 | 77.836 | 2.677 | 85.722 | [78.687, 79.020] |
| split_after_layer2 | 1000 | 78.689 | 77.615 | 2.669 | 85.482 | [78.523, 78.854] |
| monolithic | 1000 | 76.291 | 73.778 | 3.578 | 81.389 | [76.069, 76.514] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 76.227 | 73.666 | 3.616 | 81.318 |
| 1 | split_after_layer2 | 200 | 78.298 | 77.615 | 2.221 | 85.359 |
| 1 | split_after_layer3 | 200 | 78.346 | 77.662 | 2.222 | 85.513 |
| 1 | split_after_layer3_block0 | 200 | 76.556 | 76.499 | 0.303 | 76.970 |
| 2 | monolithic | 200 | 76.274 | 73.727 | 3.600 | 81.351 |
| 2 | split_after_layer2 | 200 | 78.825 | 77.695 | 2.812 | 85.666 |
| 2 | split_after_layer3 | 200 | 78.993 | 77.888 | 2.775 | 85.725 |
| 2 | split_after_layer3_block0 | 200 | 79.146 | 78.001 | 2.769 | 85.898 |
| 3 | monolithic | 200 | 76.252 | 73.741 | 3.561 | 81.287 |
| 3 | split_after_layer2 | 200 | 79.020 | 77.844 | 2.660 | 85.338 |
| 3 | split_after_layer3 | 200 | 79.012 | 77.892 | 2.769 | 85.674 |
| 3 | split_after_layer3_block0 | 200 | 79.164 | 78.032 | 2.801 | 86.038 |
| 4 | monolithic | 200 | 76.329 | 73.806 | 3.567 | 81.378 |
| 4 | split_after_layer2 | 200 | 78.591 | 77.446 | 2.779 | 85.394 |
| 4 | split_after_layer3 | 200 | 79.025 | 77.935 | 2.743 | 85.798 |
| 4 | split_after_layer3_block0 | 200 | 79.360 | 78.180 | 2.824 | 86.058 |
| 5 | monolithic | 200 | 76.376 | 73.836 | 3.579 | 81.438 |
| 5 | split_after_layer2 | 200 | 78.709 | 77.589 | 2.795 | 85.432 |
| 5 | split_after_layer3 | 200 | 78.891 | 77.730 | 2.796 | 85.613 |
| 5 | split_after_layer3_block0 | 200 | 79.231 | 78.097 | 2.768 | 86.074 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 76.291 | 0.0603 | 0.1486 | 0.0008 |
| split_after_layer2 | 5 | 78.689 | 0.2696 | 0.7217 | 0.0034 |
| split_after_layer3 | 5 | 78.853 | 0.2887 | 0.6794 | 0.0037 |
| split_after_layer3_block0 | 5 | 78.691 | 1.1967 | 2.8043 | 0.0152 |

## Overhead vs Monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary Crossing (ms) |
|---|---|---|---|---|
| split_after_layer3_block0 | 2.400 | 3.1% | 196.0 | 33.135 |
| split_after_layer3 | 2.562 | 3.4% | 196.0 | 25.718 |
| split_after_layer2 | 2.397 | 3.1% | 392.0 | 39.937 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer3_block0 | 0.756 | medium | 300807.0 | 1.10e-53 |
| split_after_layer3 | 0.811 | large | 295044.0 | 9.93e-57 |
| split_after_layer2 | 0.760 | medium | 293986.0 | 2.68e-57 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer2 (78.689 ms)
- **Near-best window:** 5.0% → threshold 82.623 ms
- **Near-best candidates:** split_after_layer3_block0, split_after_layer3, split_after_layer2
- **Degenerate candidates:** None
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer2 (78.689 ms)
- **Selected reference candidate:** split_after_layer3_block0 (78.691 ms)
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
