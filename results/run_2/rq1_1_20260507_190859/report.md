# RQ1.1 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results/rq1_1_20260507_190859/config.yaml`

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
| max_extra_iterations | 0 |

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

- **Environment snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results/rq1_1_20260507_190859/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T19:08:59.497527 |
| platform | Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| processor | x86_64 |
| python_version | 3.10.12 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | 1508e9bbe9acebffff4b93dd0c68cc5538ac0d60 |

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
| priority.applied | false |
| priority.applied_nice | 0 |
| priority.error | Insufficient privileges for nice(-5); running at default nice=0 |
| governor.requested.set_governor | true |
| governor.requested.requested_mode | performance |
| governor.detected | unavailable |
| governor.note | cpufreq sysfs not exposed (expected on WSL2/Hyper-V or non-Linux). CPU frequency is managed by the host OS. |
| governor.applied | false |
| governor.error | Governor sysfs not available; cannot set governor |
| turbo.requested.disable_turbo | true |
| turbo.detected | unavailable |
| turbo.note | Neither intel_pstate/no_turbo nor cpufreq/boost sysfs entries are exposed. Turbo behaviour is controlled by the host OS. |
| turbo.applied | false |
| turbo.error | Turbo boost sysfs not available; cannot disable |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 34.299 | 34.085 | 1.038 | 35.780 | [34.234, 34.363] | 1.411 | 4.3% | n/a | n/a | n/a |
| split_after_layer4 | 1000 | 34.180 | 33.874 | 1.212 | 36.228 | [34.105, 34.256] | 1.293 | 3.9% | n/a | n/a | n/a |
| split_after_layer3 | 1000 | 34.321 | 34.035 | 1.341 | 36.296 | [34.238, 34.404] | 1.434 | 4.4% | n/a | n/a | n/a |
| split_after_layer2 | 1000 | 34.025 | 33.876 | 0.976 | 35.202 | [33.965, 34.086] | 1.138 | 3.5% | n/a | n/a | n/a |
| monolithic | 1000 | 32.888 | 32.727 | 1.006 | 34.459 | [32.825, 32.950] | 0.000 | 0.0% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 32.595 | 32.457 | 0.904 | 33.569 |
| 1 | split_after_layer1 | 200 | 34.998 | 34.711 | 1.374 | 37.655 |
| 1 | split_after_layer2 | 200 | 34.017 | 33.888 | 0.844 | 35.346 |
| 1 | split_after_layer3 | 200 | 34.194 | 34.116 | 0.865 | 35.200 |
| 1 | split_after_layer4 | 200 | 34.959 | 34.526 | 1.597 | 37.697 |
| 2 | monolithic | 200 | 32.621 | 32.503 | 0.838 | 33.728 |
| 2 | split_after_layer1 | 200 | 34.051 | 33.979 | 0.644 | 35.121 |
| 2 | split_after_layer2 | 200 | 34.048 | 33.949 | 0.768 | 35.106 |
| 2 | split_after_layer3 | 200 | 34.123 | 33.927 | 0.800 | 35.316 |
| 2 | split_after_layer4 | 200 | 33.766 | 33.658 | 0.746 | 35.007 |
| 3 | monolithic | 200 | 33.359 | 33.083 | 1.306 | 35.283 |
| 3 | split_after_layer1 | 200 | 34.050 | 33.869 | 1.018 | 35.146 |
| 3 | split_after_layer2 | 200 | 33.980 | 33.792 | 1.049 | 34.993 |
| 3 | split_after_layer3 | 200 | 33.863 | 33.714 | 0.917 | 35.116 |
| 3 | split_after_layer4 | 200 | 33.874 | 33.672 | 1.036 | 35.332 |
| 4 | monolithic | 200 | 32.902 | 32.822 | 0.815 | 33.933 |
| 4 | split_after_layer1 | 200 | 34.101 | 34.015 | 0.642 | 35.034 |
| 4 | split_after_layer2 | 200 | 33.959 | 33.816 | 0.879 | 35.198 |
| 4 | split_after_layer3 | 200 | 35.398 | 34.968 | 2.180 | 38.840 |
| 4 | split_after_layer4 | 200 | 34.185 | 33.886 | 1.239 | 35.567 |
| 5 | monolithic | 200 | 32.961 | 32.807 | 0.896 | 34.478 |
| 5 | split_after_layer1 | 200 | 34.295 | 34.069 | 1.000 | 35.413 |
| 5 | split_after_layer2 | 200 | 34.123 | 33.941 | 1.260 | 35.363 |
| 5 | split_after_layer3 | 200 | 34.028 | 33.929 | 0.724 | 35.324 |
| 5 | split_after_layer4 | 200 | 34.118 | 34.018 | 0.881 | 35.390 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 32.888 | 0.3103 | 0.7646 | 0.0094 |
| split_after_layer1 | 5 | 34.299 | 0.4036 | 0.9485 | 0.0118 |
| split_after_layer2 | 5 | 34.025 | 0.0643 | 0.1639 | 0.0019 |
| split_after_layer3 | 5 | 34.321 | 0.6146 | 1.5348 | 0.0179 |
| split_after_layer4 | 5 | 34.180 | 0.4681 | 1.1937 | 0.0137 |

## Overhead vs monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| split_after_layer1 | 1.411 | 4.3% | 784.0 | 21.098 |
| split_after_layer4 | 1.293 | 3.9% | 98.0 | 0.912 |
| split_after_layer3 | 1.434 | 4.4% | 196.0 | 8.503 |
| split_after_layer2 | 1.138 | 3.5% | 392.0 | 14.551 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 1.381 | large | 86059.0 | 1.83e-225 |
| split_after_layer4 | 1.161 | large | 120674.0 | 1.14e-189 |
| split_after_layer3 | 1.209 | large | 98579.0 | 3.71e-212 |
| split_after_layer2 | 1.148 | large | 116012.0 | 2.62e-194 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer2 (34.025 ms)
- **Near-best window:** 5.0% → threshold 35.727 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer2 (34.025 ms)
- **Selected reference candidate:** split_after_layer1 (34.299 ms)
- **Rejected:** split_after_layer4, split_after_layer3
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
