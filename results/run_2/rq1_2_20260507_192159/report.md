# RQ1.2 fine-grained refinement Experiment Report


## Configuration Used

- **Config snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results/rq1_2_20260507_192159/config.yaml`

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
| split_after_layer2 | split | layer2 | n/a |
| split_after_layer3_block0 | split | layer3.0 | n/a |
| split_after_layer3 | split | layer3 | n/a |

## Environment Used

- **Environment snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results/rq1_2_20260507_192159/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T19:21:59.761897 |
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
| split_after_layer3_block0 | 1000 | 34.411 | 34.090 | 1.366 | 36.610 | [34.326, 34.496] | 1.443 | 4.4% | n/a | n/a | n/a |
| split_after_layer3 | 1000 | 34.004 | 33.842 | 1.018 | 35.366 | [33.941, 34.067] | 1.036 | 3.1% | n/a | n/a | n/a |
| split_after_layer2 | 1000 | 34.117 | 33.913 | 1.128 | 35.829 | [34.047, 34.187] | 1.149 | 3.5% | n/a | n/a | n/a |
| monolithic | 1000 | 32.968 | 32.789 | 1.038 | 34.448 | [32.903, 33.032] | 0.000 | 0.0% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 33.414 | 33.035 | 1.541 | 35.976 |
| 1 | split_after_layer2 | 200 | 34.354 | 34.065 | 1.430 | 36.871 |
| 1 | split_after_layer3 | 200 | 33.837 | 33.645 | 0.972 | 35.010 |
| 1 | split_after_layer3_block0 | 200 | 34.123 | 33.738 | 1.673 | 36.177 |
| 2 | monolithic | 200 | 32.800 | 32.644 | 0.923 | 34.083 |
| 2 | split_after_layer2 | 200 | 33.719 | 33.558 | 0.716 | 34.806 |
| 2 | split_after_layer3 | 200 | 33.825 | 33.695 | 0.677 | 34.964 |
| 2 | split_after_layer3_block0 | 200 | 34.012 | 33.755 | 0.932 | 35.831 |
| 3 | monolithic | 200 | 33.007 | 32.889 | 0.915 | 34.587 |
| 3 | split_after_layer2 | 200 | 34.019 | 33.948 | 0.743 | 35.439 |
| 3 | split_after_layer3 | 200 | 34.273 | 34.161 | 1.029 | 35.318 |
| 3 | split_after_layer3_block0 | 200 | 35.261 | 35.038 | 1.458 | 37.747 |
| 4 | monolithic | 200 | 32.791 | 32.737 | 0.808 | 33.868 |
| 4 | split_after_layer2 | 200 | 34.192 | 34.023 | 0.978 | 35.984 |
| 4 | split_after_layer3 | 200 | 34.245 | 33.979 | 1.119 | 35.917 |
| 4 | split_after_layer3_block0 | 200 | 34.405 | 34.168 | 1.278 | 36.364 |
| 5 | monolithic | 200 | 32.826 | 32.724 | 0.636 | 33.936 |
| 5 | split_after_layer2 | 200 | 34.300 | 33.900 | 1.433 | 36.081 |
| 5 | split_after_layer3 | 200 | 33.839 | 33.609 | 1.125 | 34.900 |
| 5 | split_after_layer3_block0 | 200 | 34.253 | 34.073 | 0.976 | 35.760 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 32.968 | 0.2647 | 0.6231 | 0.0080 |
| split_after_layer2 | 5 | 34.117 | 0.2569 | 0.6355 | 0.0075 |
| split_after_layer3 | 5 | 34.004 | 0.2332 | 0.4483 | 0.0069 |
| split_after_layer3_block0 | 5 | 34.411 | 0.4973 | 1.2486 | 0.0145 |

## Overhead vs monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| split_after_layer3_block0 | 1.443 | 4.4% | 196.0 | 11.873 |
| split_after_layer3 | 1.036 | 3.1% | 196.0 | 8.302 |
| split_after_layer2 | 1.149 | 3.5% | 392.0 | 14.623 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer3_block0 | 1.190 | large | 110992.5 | 2.29e-199 |
| split_after_layer3 | 1.008 | large | 144023.0 | 2.77e-167 |
| split_after_layer2 | 1.061 | large | 136088.5 | 9.89e-175 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer3 (34.004 ms)
- **Near-best window:** 5.0% → threshold 35.704 ms
- **Near-best candidates:** split_after_layer3_block0, split_after_layer3, split_after_layer2
- **Degenerate candidates:** None
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3 (34.004 ms)
- **Selected reference candidate:** split_after_layer2 (34.117 ms)
- **Rejected:** split_after_layer3_block0
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
