# RQ1.4b kind multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `/app/results/rq1_4b_20260507_181706/config.yaml`

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

- **Environment snapshot:** `/app/results/rq1_4b_20260507_181706/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T18:17:06.752736 |
| platform | Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 16 |
| git_commit | unknown |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | kubernetes |
| node_count | 1 |
| namespace | rq14b |
| pod_colocation_enforced | false |
| pod_placement.benchmark-client | thesis-rq14b-worker5 |

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
| chain_2svc | 1000 | 35.950 | 35.543 | 1.554 | 38.957 | [35.853, 36.046] | 1.986 | 5.8% | n/a | n/a | n/a |
| chain_5svc | 1000 | 41.227 | 40.835 | 1.911 | 44.809 | [41.108, 41.345] | 7.263 | 21.4% | n/a | n/a | n/a |
| chain_4svc | 1000 | 39.582 | 39.226 | 1.494 | 42.415 | [39.490, 39.675] | 5.618 | 16.5% | n/a | n/a | n/a |
| chain_3svc | 1000 | 37.913 | 37.693 | 1.331 | 40.328 | [37.830, 37.995] | 3.949 | 11.6% | n/a | n/a | n/a |
| monolithic_k8s_1svc | 1000 | 33.964 | 33.692 | 1.020 | 36.087 | [33.901, 34.027] | 0.000 | 0.0% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 36.313 | 35.991 | 1.412 | 39.224 |
| 1 | chain_3svc | 200 | 38.362 | 38.187 | 1.315 | 40.663 |
| 1 | chain_4svc | 200 | 40.165 | 39.879 | 1.642 | 42.960 |
| 1 | chain_5svc | 200 | 41.771 | 41.161 | 2.285 | 46.077 |
| 1 | monolithic_k8s_1svc | 200 | 34.566 | 34.155 | 1.355 | 37.092 |
| 2 | chain_2svc | 200 | 36.884 | 36.098 | 2.290 | 42.038 |
| 2 | chain_3svc | 200 | 37.964 | 37.686 | 1.452 | 40.480 |
| 2 | chain_4svc | 200 | 39.568 | 39.325 | 1.310 | 41.800 |
| 2 | chain_5svc | 200 | 41.589 | 41.629 | 1.540 | 44.074 |
| 2 | monolithic_k8s_1svc | 200 | 33.834 | 33.518 | 1.006 | 35.434 |
| 3 | chain_2svc | 200 | 35.453 | 35.326 | 0.792 | 37.230 |
| 3 | chain_3svc | 200 | 37.513 | 37.194 | 1.180 | 39.450 |
| 3 | chain_4svc | 200 | 39.000 | 38.827 | 0.942 | 40.759 |
| 3 | chain_5svc | 200 | 41.440 | 41.057 | 1.876 | 44.965 |
| 3 | monolithic_k8s_1svc | 200 | 33.687 | 33.473 | 0.751 | 35.050 |
| 4 | chain_2svc | 200 | 35.559 | 35.335 | 0.905 | 37.370 |
| 4 | chain_3svc | 200 | 38.039 | 37.773 | 1.347 | 40.497 |
| 4 | chain_4svc | 200 | 39.968 | 39.678 | 1.851 | 43.800 |
| 4 | chain_5svc | 200 | 40.426 | 40.230 | 1.354 | 42.648 |
| 4 | monolithic_k8s_1svc | 200 | 33.665 | 33.503 | 0.741 | 34.781 |
| 5 | chain_2svc | 200 | 35.541 | 35.361 | 1.361 | 36.778 |
| 5 | chain_3svc | 200 | 37.687 | 37.614 | 1.190 | 39.630 |
| 5 | chain_4svc | 200 | 39.209 | 38.875 | 1.231 | 41.216 |
| 5 | chain_5svc | 200 | 40.907 | 40.430 | 2.042 | 45.505 |
| 5 | monolithic_k8s_1svc | 200 | 34.068 | 33.871 | 0.842 | 35.787 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 35.950 | 0.6268 | 1.4313 | 0.0174 |
| chain_3svc | 5 | 37.913 | 0.3284 | 0.8493 | 0.0087 |
| chain_4svc | 5 | 39.582 | 0.4918 | 1.1654 | 0.0124 |
| chain_5svc | 5 | 41.227 | 0.5517 | 1.3454 | 0.0134 |
| monolithic_k8s_1svc | 5 | 33.964 | 0.3728 | 0.9007 | 0.0110 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 1.986 | 5.8% | 980.0 | 2.321 |
| chain_5svc | 7.263 | 21.4% | 2058.0 | 5.966 |
| chain_4svc | 5.618 | 16.5% | 1960.0 | 4.882 |
| chain_3svc | 3.949 | 11.6% | 1568.0 | 3.667 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4


_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 1.511 | large | 82542.0 | 2.82e-229 |
| chain_5svc | 4.741 | large | 1047.0 | 0.00e+00 |
| chain_4svc | 4.391 | large | 3693.0 | 0.00e+00 |
| chain_3svc | 3.330 | large | 15026.0 | 1.10e-308 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
