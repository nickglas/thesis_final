# RQ1.1 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_1_20260515_111428/config.yaml`

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
| split_after_layer1 | split | layer1 | n/a |
| split_after_layer2 | split | layer2 | n/a |
| split_after_layer3 | split | layer3 | n/a |
| split_after_layer4 | split | layer4 | n/a |

## Environment Used

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_1_20260515_111428/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T11:14:29.255683 |
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
| governor.detected | schedutil |
| governor.applied | true |
| governor.applied_mode | performance |
| governor.method | sudo |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 1 |
| turbo.detected.turbo_enabled | true |
| turbo.applied | true |
| turbo.applied_value | 0 |
| turbo.method | sudo |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 80.877 | 80.237 | 2.273 | 87.915 | [80.736, 81.018] | 3.640 | 4.7% | n/a | n/a | n/a |
| split_after_layer4 | 1000 | 79.583 | 78.849 | 2.434 | 86.381 | [79.432, 79.734] | 2.346 | 3.0% | n/a | n/a | n/a |
| split_after_layer3 | 1000 | 79.084 | 78.383 | 2.308 | 85.852 | [78.941, 79.227] | 1.847 | 2.4% | n/a | n/a | n/a |
| split_after_layer2 | 1000 | 80.118 | 79.600 | 2.404 | 86.902 | [79.968, 80.267] | 2.880 | 3.7% | n/a | n/a | n/a |
| monolithic | 1000 | 77.238 | 75.294 | 3.587 | 83.478 | [77.015, 77.460] | 0.000 | 0.0% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 77.481 | 75.549 | 3.688 | 83.417 |
| 1 | split_after_layer1 | 200 | 80.270 | 80.128 | 0.880 | 82.032 |
| 1 | split_after_layer2 | 200 | 79.605 | 79.298 | 1.592 | 81.754 |
| 1 | split_after_layer3 | 200 | 78.744 | 78.385 | 1.526 | 80.972 |
| 1 | split_after_layer4 | 200 | 78.852 | 78.393 | 1.917 | 83.224 |
| 2 | monolithic | 200 | 77.183 | 75.291 | 3.500 | 83.272 |
| 2 | split_after_layer1 | 200 | 80.892 | 80.043 | 2.607 | 88.194 |
| 2 | split_after_layer2 | 200 | 80.113 | 79.538 | 2.130 | 86.788 |
| 2 | split_after_layer3 | 200 | 79.491 | 78.698 | 2.489 | 86.003 |
| 2 | split_after_layer4 | 200 | 79.639 | 78.823 | 2.484 | 86.591 |
| 3 | monolithic | 200 | 77.246 | 75.248 | 3.557 | 83.268 |
| 3 | split_after_layer1 | 200 | 81.254 | 80.490 | 2.575 | 88.860 |
| 3 | split_after_layer2 | 200 | 81.380 | 80.630 | 2.498 | 89.192 |
| 3 | split_after_layer3 | 200 | 79.019 | 78.193 | 2.498 | 86.309 |
| 3 | split_after_layer4 | 200 | 79.850 | 79.037 | 2.543 | 86.843 |
| 4 | monolithic | 200 | 77.009 | 75.021 | 3.655 | 83.612 |
| 4 | split_after_layer1 | 200 | 80.976 | 80.290 | 2.308 | 87.930 |
| 4 | split_after_layer2 | 200 | 80.498 | 79.757 | 2.394 | 87.423 |
| 4 | split_after_layer3 | 200 | 79.104 | 78.328 | 2.562 | 86.029 |
| 4 | split_after_layer4 | 200 | 79.911 | 79.083 | 2.640 | 86.322 |
| 5 | monolithic | 200 | 77.269 | 75.387 | 3.554 | 83.700 |
| 5 | split_after_layer1 | 200 | 80.995 | 80.334 | 2.423 | 88.420 |
| 5 | split_after_layer2 | 200 | 78.992 | 78.213 | 2.585 | 86.486 |
| 5 | split_after_layer3 | 200 | 79.063 | 78.328 | 2.262 | 85.525 |
| 5 | split_after_layer4 | 200 | 79.663 | 78.955 | 2.395 | 86.500 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 77.238 | 0.1702 | 0.4727 | 0.0022 |
| split_after_layer1 | 5 | 80.877 | 0.3654 | 0.9837 | 0.0045 |
| split_after_layer2 | 5 | 80.118 | 0.9036 | 2.3873 | 0.0113 |
| split_after_layer3 | 5 | 79.084 | 0.2676 | 0.7471 | 0.0034 |
| split_after_layer4 | 5 | 79.583 | 0.4250 | 1.0587 | 0.0053 |

## Overhead vs monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| split_after_layer1 | 3.640 | 4.7% | 784.0 | 53.811 |
| split_after_layer4 | 2.346 | 3.0% | 98.0 | 2.218 |
| split_after_layer3 | 1.847 | 2.4% | 196.0 | 26.058 |
| split_after_layer2 | 2.880 | 3.7% | 392.0 | 40.853 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 1.212 | large | 250519.0 | 3.66e-83 |
| split_after_layer4 | 0.765 | medium | 254050.0 | 7.04e-81 |
| split_after_layer3 | 0.612 | medium | 259405.0 | 1.78e-77 |
| split_after_layer2 | 0.943 | large | 255328.0 | 4.64e-80 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer3 (79.084 ms)
- **Near-best window:** 5.0% → threshold 83.038 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3 (79.084 ms)
- **Selected reference candidate:** split_after_layer2 (80.118 ms)
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
