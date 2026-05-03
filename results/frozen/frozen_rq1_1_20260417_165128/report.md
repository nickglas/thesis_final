# RQ1.1 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `results/rq1_1_20260417_165128/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.1 fully controlled |
| description | Strictly controlled single-core benchmark for thesis defensibility |

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
| split_after_layer1 | split | layer1 |
| split_after_layer2 | split | layer2 |
| split_after_layer3 | split | layer3 |
| split_after_layer4 | split | layer4 |

## Environment Used

- **Environment snapshot:** `results/rq1_1_20260417_165128/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-04-17T16:51:28.567036 |
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
| governor.detected | schedutil |
| governor.applied | true |
| governor.applied_mode | performance |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 1 |
| turbo.detected.turbo_enabled | true |
| turbo.applied | true |
| turbo.applied_value | 0 |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 79.652 | 78.771 | 2.285 | 86.464 | [79.510, 79.794] |
| split_after_layer4 | 1000 | 77.258 | 76.085 | 2.647 | 83.934 | [77.094, 77.422] |
| split_after_layer3 | 1000 | 78.500 | 77.559 | 2.742 | 85.470 | [78.330, 78.670] |
| split_after_layer2 | 1000 | 78.629 | 77.653 | 2.734 | 85.269 | [78.460, 78.799] |
| monolithic | 1000 | 76.120 | 74.042 | 3.893 | 82.360 | [75.879, 76.362] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 76.028 | 73.496 | 3.539 | 81.003 |
| 1 | split_after_layer1 | 200 | 78.476 | 78.483 | 0.464 | 79.102 |
| 1 | split_after_layer2 | 200 | 78.268 | 77.673 | 2.149 | 85.207 |
| 1 | split_after_layer3 | 200 | 77.432 | 76.775 | 2.275 | 84.496 |
| 1 | split_after_layer4 | 200 | 76.596 | 75.909 | 2.247 | 83.540 |
| 2 | monolithic | 200 | 76.454 | 74.535 | 3.408 | 82.386 |
| 2 | split_after_layer1 | 200 | 80.543 | 80.568 | 0.604 | 81.386 |
| 2 | split_after_layer2 | 200 | 79.312 | 78.481 | 2.925 | 84.969 |
| 2 | split_after_layer3 | 200 | 78.939 | 77.986 | 2.683 | 87.350 |
| 2 | split_after_layer4 | 200 | 78.225 | 77.760 | 2.001 | 85.277 |
| 3 | monolithic | 200 | 77.665 | 75.502 | 4.634 | 86.041 |
| 3 | split_after_layer1 | 200 | 79.796 | 78.734 | 2.873 | 86.820 |
| 3 | split_after_layer2 | 200 | 78.736 | 77.610 | 2.783 | 85.451 |
| 3 | split_after_layer3 | 200 | 78.659 | 77.671 | 2.836 | 85.542 |
| 3 | split_after_layer4 | 200 | 77.079 | 75.879 | 2.898 | 83.761 |
| 4 | monolithic | 200 | 75.204 | 72.577 | 3.644 | 80.243 |
| 4 | split_after_layer1 | 200 | 79.721 | 78.712 | 2.755 | 86.611 |
| 4 | split_after_layer2 | 200 | 77.955 | 76.803 | 2.855 | 84.942 |
| 4 | split_after_layer3 | 200 | 78.782 | 77.635 | 2.810 | 85.580 |
| 4 | split_after_layer4 | 200 | 77.219 | 76.042 | 2.859 | 83.911 |
| 5 | monolithic | 200 | 75.250 | 72.655 | 3.615 | 80.265 |
| 5 | split_after_layer1 | 200 | 79.725 | 78.690 | 2.751 | 86.652 |
| 5 | split_after_layer2 | 200 | 78.874 | 77.795 | 2.705 | 85.460 |
| 5 | split_after_layer3 | 200 | 78.689 | 77.530 | 2.820 | 85.585 |
| 5 | split_after_layer4 | 200 | 77.172 | 76.026 | 2.850 | 84.148 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 76.120 | 1.0130 | 2.4614 | 0.0133 |
| split_after_layer1 | 5 | 79.652 | 0.7427 | 2.0662 | 0.0093 |
| split_after_layer2 | 5 | 78.629 | 0.5296 | 1.3567 | 0.0067 |
| split_after_layer3 | 5 | 78.500 | 0.6071 | 1.5074 | 0.0077 |
| split_after_layer4 | 5 | 77.258 | 0.5948 | 1.6297 | 0.0077 |

## Overhead vs Monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary Crossing (ms) |
|---|---|---|---|---|
| split_after_layer1 | 3.532 | 4.6% | 784.0 | 53.031 |
| split_after_layer4 | 1.138 | 1.5% | 98.0 | 2.132 |
| split_after_layer3 | 2.380 | 3.1% | 196.0 | 25.726 |
| split_after_layer2 | 2.509 | 3.3% | 392.0 | 39.961 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 1.107 | large | 281857.0 | 5.06e-64 |
| split_after_layer4 | 0.342 | small | 323112.0 | 1.04e-42 |
| split_after_layer3 | 0.707 | medium | 304600.0 | 9.99e-52 |
| split_after_layer2 | 0.746 | medium | 299734.0 | 3.03e-54 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer4 (77.258 ms)
- **Near-best window:** 5.0% → threshold 81.121 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3 (78.500 ms)
- **Selected reference candidate:** split_after_layer2 (78.629 ms)
- **Rejected:** split_after_layer1, split_after_layer4
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
