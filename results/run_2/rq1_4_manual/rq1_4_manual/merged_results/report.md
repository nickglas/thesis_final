# RQ1.4 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/app/results/rq1_4_manual/merged_results/config.yaml`

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
| resources.memory_request | 1Gi |
| resources.memory_limit | 1Gi |
| client_resources.cpu_request | 1 |
| client_resources.cpu_limit | 1 |
| client_resources.memory_request | 1Gi |
| client_resources.memory_limit | 1Gi |

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
| monolithic_k8s_1svc | chain | n/a | n/a |
| chain_2svc | chain | n/a | layer2 |
| chain_3svc | chain | n/a | layer1, layer3 |
| chain_4svc | chain | n/a | layer1, layer2, layer3 |
| chain_5svc | chain | n/a | layer1, layer2, layer3, layer4 |

## Environment Used

- **Environment snapshot:** `/app/results/rq1_4_manual/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T17:52:16.649896 |
| platform | Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'reason': 'Full simultaneous 1Gi-per-pod deployment exceeded single-node kind allocatable memory; conditions were run one at a time with unchanged service/client resource requests.', 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/app/results/rq1_4_manual/partial_results'} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | kubernetes |
| namespace | rq14 |
| pod_colocation_enforced | false |

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
| monolithic_k8s_1svc | 1000 | 33.671 | 33.434 | 1.109 | 35.493 | [33.602, 33.740] | 0.000 | 0.0% | n/a | n/a | n/a |
| chain_2svc | 1000 | 35.148 | 34.893 | 1.219 | 37.060 | [35.072, 35.224] | 1.477 | 4.4% | n/a | n/a | n/a |
| chain_3svc | 1000 | 36.485 | 36.229 | 1.106 | 38.336 | [36.417, 36.554] | 2.814 | 8.4% | n/a | n/a | n/a |
| chain_4svc | 1000 | 37.945 | 37.507 | 1.528 | 40.466 | [37.850, 38.040] | 4.274 | 12.7% | n/a | n/a | n/a |
| chain_5svc | 1000 | 39.106 | 38.670 | 1.764 | 41.852 | [38.997, 39.216] | 5.435 | 16.1% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 34.888 | 34.743 | 0.820 | 36.534 |
| 1 | chain_3svc | 200 | 36.225 | 36.104 | 0.686 | 37.537 |
| 1 | chain_4svc | 200 | 37.687 | 37.439 | 1.054 | 39.136 |
| 1 | chain_5svc | 200 | 38.573 | 38.411 | 0.960 | 40.541 |
| 1 | monolithic_k8s_1svc | 200 | 34.381 | 34.221 | 1.429 | 36.118 |
| 2 | chain_2svc | 200 | 35.193 | 34.950 | 1.191 | 36.865 |
| 2 | chain_3svc | 200 | 36.652 | 36.395 | 1.067 | 38.476 |
| 2 | chain_4svc | 200 | 37.905 | 37.394 | 1.594 | 40.556 |
| 2 | chain_5svc | 200 | 39.009 | 38.905 | 1.217 | 41.316 |
| 2 | monolithic_k8s_1svc | 200 | 33.769 | 33.510 | 1.264 | 35.667 |
| 3 | chain_2svc | 200 | 35.633 | 35.150 | 1.776 | 38.331 |
| 3 | chain_3svc | 200 | 36.695 | 36.181 | 1.649 | 39.804 |
| 3 | chain_4svc | 200 | 39.274 | 38.834 | 2.077 | 42.928 |
| 3 | chain_5svc | 200 | 39.374 | 38.951 | 1.878 | 42.456 |
| 3 | monolithic_k8s_1svc | 200 | 33.356 | 33.220 | 0.809 | 34.985 |
| 4 | chain_2svc | 200 | 34.934 | 34.908 | 0.752 | 36.146 |
| 4 | chain_3svc | 200 | 36.535 | 36.210 | 1.104 | 38.697 |
| 4 | chain_4svc | 200 | 37.413 | 37.128 | 0.946 | 39.005 |
| 4 | chain_5svc | 200 | 39.094 | 38.550 | 2.178 | 44.018 |
| 4 | monolithic_k8s_1svc | 200 | 33.565 | 33.396 | 0.786 | 35.079 |
| 5 | chain_2svc | 200 | 35.092 | 34.869 | 1.139 | 36.508 |
| 5 | chain_3svc | 200 | 36.320 | 36.255 | 0.653 | 37.389 |
| 5 | chain_4svc | 200 | 37.444 | 37.266 | 0.689 | 38.877 |
| 5 | chain_5svc | 200 | 39.481 | 38.996 | 2.109 | 44.007 |
| 5 | monolithic_k8s_1svc | 200 | 33.284 | 33.211 | 0.698 | 34.813 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 35.148 | 0.2974 | 0.7446 | 0.0085 |
| chain_3svc | 5 | 36.485 | 0.2057 | 0.4700 | 0.0056 |
| chain_4svc | 5 | 37.945 | 0.7695 | 1.8608 | 0.0203 |
| chain_5svc | 5 | 39.106 | 0.3555 | 0.9077 | 0.0091 |
| monolithic_k8s_1svc | 5 | 33.671 | 0.4397 | 1.0966 | 0.0131 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 1.477 | 4.4% | 980.0 | 1.953 |
| chain_3svc | 2.814 | 8.4% | 1568.0 | 3.032 |
| chain_4svc | 4.274 | 12.7% | 1960.0 | 3.983 |
| chain_5svc | 5.435 | 16.1% | 2058.0 | 4.834 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4


_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 1.267 | large | 116713.0 | 1.32e-193 |
| chain_3svc | 2.541 | large | 23754.0 | 9.46e-298 |
| chain_4svc | 3.202 | large | 9874.0 | 0.00e+00 |
| chain_5svc | 3.688 | large | 6902.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
