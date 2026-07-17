# RQ1.4 fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_4_fully_controlled_20260515_141036/merged_results/config.yaml`

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
| resources.memory_request | 512Mi |
| resources.memory_limit | 512Mi |
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

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_4_fully_controlled_20260515_141036/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T14:11:50.318497 |
| platform | Linux-6.17.0-23-generic-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cpu |
| cpu_count | 16 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/home/nick/Desktop/thesis_final/results/rq1_4_fully_controlled_20260515_141036/partial_results'} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | kind |
| node_count | 1 |
| namespace | rq14 |
| pod_colocation_enforced | true |
| pod_placement.benchmark-client | thesis-rq14-control-plane |
| pod_placement.monolithic-k8s-1svc-svc-1 | thesis-rq14-control-plane |
| pod_placement.chain-2svc-svc-1 | thesis-rq14-control-plane |
| pod_placement.chain-2svc-svc-2 | thesis-rq14-control-plane |
| pod_placement.chain-3svc-svc-1 | thesis-rq14-control-plane |
| pod_placement.chain-3svc-svc-2 | thesis-rq14-control-plane |
| pod_placement.chain-3svc-svc-3 | thesis-rq14-control-plane |
| pod_placement.chain-4svc-svc-1 | thesis-rq14-control-plane |
| pod_placement.chain-4svc-svc-2 | thesis-rq14-control-plane |
| pod_placement.chain-4svc-svc-3 | thesis-rq14-control-plane |
| pod_placement.chain-4svc-svc-4 | thesis-rq14-control-plane |
| pod_placement.chain-5svc-svc-1 | thesis-rq14-control-plane |
| pod_placement.chain-5svc-svc-2 | thesis-rq14-control-plane |
| pod_placement.chain-5svc-svc-3 | thesis-rq14-control-plane |
| pod_placement.chain-5svc-svc-4 | thesis-rq14-control-plane |
| pod_placement.chain-5svc-svc-5 | thesis-rq14-control-plane |

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
| priority.method | direct |
| governor.requested.set_governor | true |
| governor.requested.requested_mode | performance |
| governor.detected | performance |
| governor.applied | false |
| governor.error | OS error writing to /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor' |
| governor.method | failed |
| turbo.requested.disable_turbo | true |
| turbo.detected.interface | cpufreq_boost |
| turbo.detected.boost | 0 |
| turbo.detected.turbo_enabled | false |
| turbo.applied | false |
| turbo.error | OS error writing to /sys/devices/system/cpu/cpufreq/boost: [Errno 30] Read-only file system: '/sys/devices/system/cpu/cpufreq/boost' |
| turbo.method | failed |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 1000 | 81.066 | 79.506 | 4.017 | 88.250 | [80.817, 81.316] | 0.000 | 0.0% | n/a | n/a | n/a |
| chain_2svc | 1000 | 83.387 | 81.803 | 3.525 | 90.189 | [83.169, 83.606] | 2.321 | 2.9% | n/a | n/a | n/a |
| chain_3svc | 1000 | 87.728 | 85.775 | 4.233 | 95.269 | [87.465, 87.991] | 6.662 | 8.2% | n/a | n/a | n/a |
| chain_4svc | 1000 | 90.572 | 88.675 | 3.929 | 97.713 | [90.328, 90.816] | 9.506 | 11.7% | n/a | n/a | n/a |
| chain_5svc | 1000 | 92.535 | 90.456 | 3.965 | 99.491 | [92.289, 92.781] | 11.469 | 14.1% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 81.951 | 81.686 | 1.583 | 83.710 |
| 1 | chain_3svc | 200 | 85.482 | 84.861 | 2.360 | 91.165 |
| 1 | chain_4svc | 200 | 88.994 | 88.100 | 3.218 | 96.220 |
| 1 | chain_5svc | 200 | 91.332 | 90.252 | 3.075 | 98.704 |
| 1 | monolithic_k8s_1svc | 200 | 80.400 | 79.566 | 3.678 | 84.922 |
| 2 | chain_2svc | 200 | 83.423 | 81.397 | 3.960 | 90.232 |
| 2 | chain_3svc | 200 | 89.298 | 87.132 | 4.998 | 97.497 |
| 2 | chain_4svc | 200 | 91.001 | 89.071 | 4.036 | 98.417 |
| 2 | chain_5svc | 200 | 92.672 | 90.347 | 4.155 | 99.459 |
| 2 | monolithic_k8s_1svc | 200 | 82.201 | 80.962 | 4.412 | 89.987 |
| 3 | chain_2svc | 200 | 83.724 | 81.662 | 3.742 | 90.282 |
| 3 | chain_3svc | 200 | 88.355 | 86.386 | 3.988 | 95.290 |
| 3 | chain_4svc | 200 | 90.981 | 88.754 | 4.194 | 97.886 |
| 3 | chain_5svc | 200 | 92.911 | 90.511 | 4.071 | 99.658 |
| 3 | monolithic_k8s_1svc | 200 | 81.139 | 79.380 | 4.309 | 89.850 |
| 4 | chain_2svc | 200 | 83.867 | 81.981 | 3.655 | 90.111 |
| 4 | chain_3svc | 200 | 87.922 | 85.824 | 4.706 | 95.356 |
| 4 | chain_4svc | 200 | 90.934 | 88.728 | 3.942 | 97.309 |
| 4 | chain_5svc | 200 | 92.960 | 90.568 | 4.199 | 99.664 |
| 4 | monolithic_k8s_1svc | 200 | 80.831 | 78.831 | 3.669 | 86.996 |
| 5 | chain_2svc | 200 | 83.971 | 82.285 | 3.752 | 91.139 |
| 5 | chain_3svc | 200 | 87.583 | 85.711 | 3.654 | 93.793 |
| 5 | chain_4svc | 200 | 90.951 | 88.991 | 3.817 | 97.387 |
| 5 | chain_5svc | 200 | 92.801 | 90.547 | 4.016 | 98.939 |
| 5 | monolithic_k8s_1svc | 200 | 80.762 | 78.823 | 3.756 | 87.503 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 83.387 | 0.8288 | 2.0200 | 0.0099 |
| chain_3svc | 5 | 87.728 | 1.4109 | 3.8162 | 0.0161 |
| chain_4svc | 5 | 90.572 | 0.8826 | 2.0073 | 0.0097 |
| chain_5svc | 5 | 92.535 | 0.6820 | 1.6288 | 0.0074 |
| monolithic_k8s_1svc | 5 | 81.066 | 0.6864 | 1.8009 | 0.0085 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 2.321 | 2.9% | 980.0 | 6.215 |
| chain_3svc | 6.662 | 8.2% | 1568.0 | 9.435 |
| chain_4svc | 9.506 | 11.7% | 1960.0 | 12.088 |
| chain_5svc | 11.469 | 14.1% | 2058.0 | 13.633 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4


_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 0.614 | medium | 260417.0 | 7.66e-77 |
| chain_3svc | 1.614 | large | 129415.0 | 4.02e-181 |
| chain_4svc | 2.392 | large | 41429.0 | 3.23e-276 |
| chain_5svc | 2.874 | large | 20756.0 | 1.75e-301 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
