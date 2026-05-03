# RQ1.4 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results_exports/rq1_4_fully_controlled_20260421_125049/merged_results/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.4 fully controlled |
| description | Single-threaded Kubernetes chain benchmark with maximum reproducibility controls |

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

### Kubernetes

| Setting | Value |
|---|---|
| namespace | rq14 |
| service_name_template | {condition}-svc-{index} |
| grpc_port | 50051 |
| max_message_bytes | 16777216 |
| readiness_timeout | 120.0 |
| image | thesis-inference:latest |
| image_pull_policy | IfNotPresent |
| resources.cpu_request | 1 |
| resources.cpu_limit | 1 |
| resources.memory_request | 512Mi |
| resources.memory_limit | 512Mi |
| client_resources.cpu_request | 1 |
| client_resources.cpu_limit | 1 |
| client_resources.memory_request | 1Gi |
| client_resources.memory_limit | 1Gi |

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
| monolithic_k8s_1svc | chain | n/a | n/a |
| chain_2svc | chain | n/a | layer2 |
| chain_3svc | chain | n/a | layer1, layer3 |
| chain_4svc | chain | n/a | layer1, layer2, layer3 |
| chain_5svc | chain | n/a | layer1, layer2, layer3, layer4 |

## Environment Used

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results_exports/rq1_4_fully_controlled_20260421_125049/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-04-21T12:53:50.673680 |
| platform | Linux-6.17.0-22-generic-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/home/nick/Desktop/thesis_final/results_exports/rq1_4_fully_controlled_20260421_125049/partial_results'} |

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
| governor.applied | false |
| governor.error | OS error writing to /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor' |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 0 |
| turbo.detected.turbo_enabled | false |
| turbo.applied | false |
| turbo.error | OS error writing to /sys/devices/system/cpu/cpufreq/boost: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpufreq/boost' |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 1000 | 81.447 | 79.648 | 4.061 | 89.444 | [81.195, 81.699] |
| chain_2svc | 1000 | 84.189 | 82.880 | 3.294 | 90.538 | [83.985, 84.394] |
| chain_3svc | 1000 | 87.608 | 85.487 | 4.274 | 96.083 | [87.343, 87.874] |
| chain_4svc | 1000 | 92.312 | 90.594 | 4.942 | 101.223 | [92.005, 92.619] |
| chain_5svc | 1000 | 92.624 | 90.312 | 4.318 | 99.398 | [92.356, 92.892] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 84.001 | 83.280 | 2.363 | 89.021 |
| 1 | chain_3svc | 200 | 85.169 | 84.686 | 2.165 | 91.082 |
| 1 | chain_4svc | 200 | 90.554 | 89.455 | 3.455 | 95.843 |
| 1 | chain_5svc | 200 | 91.415 | 90.178 | 3.097 | 98.388 |
| 1 | monolithic_k8s_1svc | 200 | 79.095 | 78.522 | 1.620 | 82.398 |
| 2 | chain_2svc | 200 | 82.356 | 81.601 | 2.719 | 88.678 |
| 2 | chain_3svc | 200 | 88.143 | 86.427 | 4.035 | 95.138 |
| 2 | chain_4svc | 200 | 93.155 | 91.226 | 5.034 | 102.478 |
| 2 | chain_5svc | 200 | 93.121 | 90.289 | 5.086 | 100.062 |
| 2 | monolithic_k8s_1svc | 200 | 81.995 | 79.707 | 4.669 | 90.815 |
| 3 | chain_2svc | 200 | 85.411 | 84.061 | 2.995 | 90.541 |
| 3 | chain_3svc | 200 | 87.909 | 85.698 | 4.428 | 97.145 |
| 3 | chain_4svc | 200 | 94.339 | 92.714 | 5.705 | 105.391 |
| 3 | chain_5svc | 200 | 92.751 | 90.687 | 3.887 | 99.014 |
| 3 | monolithic_k8s_1svc | 200 | 82.135 | 80.343 | 4.419 | 90.178 |
| 4 | chain_2svc | 200 | 85.055 | 83.194 | 3.788 | 91.433 |
| 4 | chain_3svc | 200 | 87.904 | 85.710 | 3.868 | 94.009 |
| 4 | chain_4svc | 200 | 92.718 | 91.229 | 5.094 | 99.944 |
| 4 | chain_5svc | 200 | 92.788 | 90.204 | 4.820 | 99.691 |
| 4 | monolithic_k8s_1svc | 200 | 82.131 | 80.632 | 3.902 | 88.877 |
| 5 | chain_2svc | 200 | 84.124 | 82.149 | 3.535 | 89.762 |
| 5 | chain_3svc | 200 | 88.916 | 86.517 | 5.293 | 99.669 |
| 5 | chain_4svc | 200 | 90.795 | 88.567 | 4.050 | 97.995 |
| 5 | chain_5svc | 200 | 93.043 | 90.214 | 4.225 | 98.720 |
| 5 | monolithic_k8s_1svc | 200 | 81.879 | 80.151 | 4.073 | 90.220 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 84.189 | 1.1876 | 3.0546 | 0.0141 |
| chain_3svc | 5 | 87.608 | 1.4250 | 3.7465 | 0.0163 |
| chain_4svc | 5 | 92.312 | 1.6107 | 3.7851 | 0.0174 |
| chain_5svc | 5 | 92.624 | 0.6942 | 1.7056 | 0.0075 |
| monolithic_k8s_1svc | 5 | 81.447 | 1.3193 | 3.0408 | 0.0162 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 2.742 | 3.4% | 980.0 | 6.285 |
| chain_3svc | 6.161 | 7.6% | 1568.0 | 9.646 |
| chain_4svc | 10.865 | 13.3% | 1960.0 | 12.231 |
| chain_5svc | 11.177 | 13.7% | 2058.0 | 13.893 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 0.742 | medium | 253319.5 | 2.38e-81 |
| chain_3svc | 1.478 | large | 163275.0 | 6.82e-150 |
| chain_4svc | 2.402 | large | 36413.5 | 3.03e-282 |
| chain_5svc | 2.667 | large | 29075.5 | 3.50e-291 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
