# RQ1.4b kind multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_4b_20260515_163322/merged_results/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.4b kind multi-node sensitivity |
| description | kind multi-node sensitivity: every chain hop crosses a node boundary |

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

### Kubernetes

| Setting | Value |
|---|---|
| namespace | rq14b |
| service_name_template | {condition}-svc-{index} |
| grpc_port | 50051 |
| max_message_bytes | 16777216 |
| readiness_timeout | 180.0 |
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
| placement.strategy | multi_node_anti_affinity |
| placement.require_distinct_nodes | true |
| placement.require_dedicated_client_node | true |
| placement.min_nodes | 6 |

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

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_4b_20260515_163322/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T14:35:38.476165 |
| platform | Linux-6.17.0-23-generic-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cpu |
| cpu_count | 16 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/home/nick/Desktop/thesis_final/results/rq1_4b_20260515_163322/partial_results'} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | kubernetes |
| node_count | 1 |
| namespace | rq14b |
| pod_colocation_enforced | false |
| pod_placement.benchmark-client | thesis-rq14b-worker6 |

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
| priority.error | Insufficient privileges for nice=-5 ([Errno 13] Permission denied); running as root was not enough, so CAP_SYS_NICE may be missing in this environment |
| governor.requested.set_governor | true |
| governor.requested.requested_mode | performance |
| governor.detected | schedutil |
| governor.applied | false |
| governor.error | OS error writing to /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor' |
| governor.method | failed |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 1 |
| turbo.detected.turbo_enabled | true |
| turbo.applied | false |
| turbo.error | OS error writing to /sys/devices/system/cpu/cpufreq/boost: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpufreq/boost' |
| turbo.method | failed |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 1000 | 67.491 | 61.917 | 10.999 | 89.446 | [66.809, 68.174] | 0.000 | 0.0% | n/a | n/a | n/a |
| chain_2svc | 1000 | 87.378 | 86.931 | 17.909 | 109.529 | [86.266, 88.489] | 19.887 | 29.5% | n/a | n/a | n/a |
| chain_3svc | 1000 | 120.465 | 121.270 | 20.490 | 142.410 | [119.194, 121.737] | 52.974 | 78.5% | n/a | n/a | n/a |
| chain_4svc | 1000 | 135.639 | 138.964 | 15.942 | 152.193 | [134.650, 136.628] | 68.148 | 101.0% | n/a | n/a | n/a |
| chain_5svc | 1000 | 141.169 | 144.692 | 13.893 | 156.041 | [140.306, 142.031] | 73.677 | 109.2% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 84.159 | 83.638 | 18.404 | 106.462 |
| 1 | chain_3svc | 200 | 121.236 | 120.392 | 18.115 | 142.019 |
| 1 | chain_4svc | 200 | 138.459 | 139.727 | 14.542 | 153.235 |
| 1 | chain_5svc | 200 | 142.944 | 144.754 | 12.427 | 157.018 |
| 1 | monolithic_k8s_1svc | 200 | 62.000 | 61.764 | 1.415 | 64.286 |
| 2 | chain_2svc | 200 | 90.031 | 90.118 | 17.553 | 113.389 |
| 2 | chain_3svc | 200 | 122.712 | 132.400 | 18.995 | 141.299 |
| 2 | chain_4svc | 200 | 131.560 | 131.016 | 13.435 | 150.216 |
| 2 | chain_5svc | 200 | 145.071 | 150.007 | 15.009 | 156.296 |
| 2 | monolithic_k8s_1svc | 200 | 68.553 | 61.944 | 11.653 | 89.376 |
| 3 | chain_2svc | 200 | 85.696 | 83.897 | 17.937 | 109.716 |
| 3 | chain_3svc | 200 | 117.480 | 115.005 | 19.200 | 143.164 |
| 3 | chain_4svc | 200 | 135.424 | 136.286 | 16.308 | 151.598 |
| 3 | chain_5svc | 200 | 142.602 | 145.809 | 10.516 | 154.924 |
| 3 | monolithic_k8s_1svc | 200 | 68.677 | 61.582 | 11.918 | 89.875 |
| 4 | chain_2svc | 200 | 89.721 | 89.730 | 17.263 | 109.520 |
| 4 | chain_3svc | 200 | 129.442 | 138.345 | 16.813 | 143.226 |
| 4 | chain_4svc | 200 | 136.225 | 140.672 | 15.604 | 152.149 |
| 4 | chain_5svc | 200 | 136.368 | 136.511 | 15.359 | 154.587 |
| 4 | monolithic_k8s_1svc | 200 | 69.107 | 61.891 | 12.551 | 92.074 |
| 5 | chain_2svc | 200 | 87.281 | 86.898 | 17.822 | 108.131 |
| 5 | chain_3svc | 200 | 111.455 | 113.606 | 24.294 | 139.871 |
| 5 | chain_4svc | 200 | 136.528 | 144.156 | 18.666 | 152.313 |
| 5 | chain_5svc | 200 | 138.858 | 141.766 | 13.920 | 155.779 |
| 5 | monolithic_k8s_1svc | 200 | 69.119 | 62.329 | 11.482 | 88.941 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 87.378 | 2.5362 | 5.8718 | 0.0290 |
| chain_3svc | 5 | 120.465 | 6.6392 | 17.9867 | 0.0551 |
| chain_4svc | 5 | 135.639 | 2.5381 | 6.8988 | 0.0187 |
| chain_5svc | 5 | 141.169 | 3.4935 | 8.7029 | 0.0247 |
| monolithic_k8s_1svc | 5 | 67.491 | 3.0801 | 7.1194 | 0.0456 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 19.887 | 29.5% | 980.0 | 6.415 |
| chain_3svc | 52.974 | 78.5% | 1568.0 | 10.301 |
| chain_4svc | 68.148 | 101.0% | 1960.0 | 14.063 |
| chain_5svc | 73.677 | 109.2% | 2058.0 | 16.548 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4


_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 1.338 | large | 130369.0 | 3.35e-180 |
| chain_3svc | 3.221 | large | 21760.0 | 3.13e-300 |
| chain_4svc | 4.976 | large | 4620.0 | 0.00e+00 |
| chain_5svc | 5.880 | large | 1658.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
