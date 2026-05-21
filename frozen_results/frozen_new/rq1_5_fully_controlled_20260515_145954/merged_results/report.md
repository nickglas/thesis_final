# RQ1.5 AKS fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_5_fully_controlled_20260515_145954/merged_results/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.5 AKS fully controlled |
| description | AKS transfer validation of RQ1.4 — single-threaded, Guaranteed QoS, pod colocation enforced |

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
| namespace | rq15 |
| service_name_template | {condition}-svc-{index} |
| grpc_port | 50051 |
| max_message_bytes | 16777216 |
| readiness_timeout | 120.0 |
| image | thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b |
| image_pull_policy | Always |
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
| governor.set_governor | false |
| governor.requested_mode | performance |
| turbo.disable_turbo | false |

### Conditions

| Condition | Type | Split After | Chain Split Points |
|---|---|---|---|
| monolithic_k8s_1svc | chain | n/a | n/a |
| chain_2svc | chain | n/a | layer2 |
| chain_3svc | chain | n/a | layer1, layer3 |
| chain_4svc | chain | n/a | layer1, layer2, layer3 |
| chain_5svc | chain | n/a | layer1, layer2, layer3, layer4 |

## Environment Used

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_5_fully_controlled_20260515_145954/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T15:07:15.156934 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cpu |
| cpu_count | 8 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/home/nick/Desktop/thesis_final/results/rq1_5_fully_controlled_20260515_145954/partial_results', 'teardown_between_conditions': True} |
| experiment_signature | {'signature': 'rq1_5_fully_controlled', 'stage': 'RQ1.5', 'mode': 'single_node', 'placement_strategy': 'none', 'namespace': 'rq15', 'host_export_dir': '/home/nick/Desktop/thesis_final/results/rq1_5_fully_controlled_20260515_145954'} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | 1.34 |
| node_count | 1 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | swedencentral |
| cni | kubenet |
| namespace | rq15 |
| pod_colocation_enforced | true |
| pod_placement.benchmark-client | aks-rq15pool-42653082-vmss000000 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-2svc-svc-1 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-2svc-svc-2 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-3svc-svc-1 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-3svc-svc-2 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-3svc-svc-3 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-4svc-svc-1 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-4svc-svc-2 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-4svc-svc-3 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-4svc-svc-4 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-5svc-svc-2 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-5svc-svc-3 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15pool-42653082-vmss000000 |
| pod_placement.chain-5svc-svc-5 | aks-rq15pool-42653082-vmss000000 |
| container_image_digest | sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b |
| acr_registry | thesisrq15acr.azurecr.io |
| mesh.enabled | false |
| mesh.implementation | n/a |
| mesh.revision | n/a |
| mesh.service_namespace | rq15 |
| mesh.client_namespace | rq15 |
| mesh.peer_authentication.observed | n/a |
| mesh.control_plane_pods | n/a |
| namespaces.service.name | rq15 |
| namespaces.service.labels.experiment | rq15 |
| namespaces.service.labels.kubernetes.io/metadata.name | rq15 |
| namespaces.service.annotations.kubectl.kubernetes.io/last-applied-configuration | {"apiVersion":"v1","kind":"Namespace","metadata":{"annotations":{},"labels":{"experiment":"rq15"},"name":"rq15"}}<br> |
| namespaces.client.name | rq15 |
| namespaces.client.labels.experiment | rq15 |
| namespaces.client.labels.kubernetes.io/metadata.name | rq15 |
| namespaces.client.annotations.kubectl.kubernetes.io/last-applied-configuration | {"apiVersion":"v1","kind":"Namespace","metadata":{"annotations":{},"labels":{"experiment":"rq15"},"name":"rq15"}}<br> |

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
| affinity.detected.physical_cores_available | 0, 2, 4, 6 |
| affinity.detected.total_cpus | 8 |
| affinity.applied | true |
| affinity.applied_cores | 0 |
| affinity.method | auto-detected physical cores (SMT excluded), first 1 |
| priority.requested.enabled | true |
| priority.requested.nice_value | -5 |
| priority.detected.current_nice | 0 |
| priority.applied | false |
| priority.applied_nice | 0 |
| priority.error | Insufficient privileges for nice=-5 ([Errno 13] Permission denied); running as root was not enough, so CAP_SYS_NICE may be missing in this environment |
| governor.requested.set_governor | false |
| governor.requested.requested_mode | performance |
| governor.detected | unavailable |
| governor.note | cpufreq sysfs not exposed (expected on WSL2/Hyper-V or non-Linux). CPU frequency is managed by the host OS. |
| governor.applied | false |
| governor.reason | Not requested and sysfs unavailable |
| turbo.requested.disable_turbo | false |
| turbo.detected | unavailable |
| turbo.note | Neither intel_pstate/no_turbo nor cpufreq/boost sysfs entries are exposed. Turbo behaviour is controlled by the host OS. |
| turbo.applied | false |
| turbo.reason | Not requested and sysfs unavailable |
| aslr.detected | 2 |
| aslr.note | Detection only; disabling requires root and has negligible impact on wall-clock inference latency. |
## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI | Overhead (ms) | Overhead (%) | Est. Compute (ms) | Inferred Non-Compute (ms) | Inferred Non-Compute (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 1000 | 70.802 | 70.224 | 2.659 | 75.151 | [70.637, 70.967] | 0.000 | 0.0% | n/a | n/a | n/a |
| chain_2svc | 1000 | 73.437 | 73.124 | 1.831 | 76.602 | [73.323, 73.551] | 2.635 | 3.7% | n/a | n/a | n/a |
| chain_3svc | 1000 | 75.410 | 75.043 | 1.971 | 78.301 | [75.288, 75.532] | 4.608 | 6.5% | n/a | n/a | n/a |
| chain_4svc | 1000 | 78.294 | 77.923 | 2.190 | 81.698 | [78.158, 78.430] | 7.492 | 10.6% | n/a | n/a | n/a |
| chain_5svc | 1000 | 80.519 | 80.078 | 2.158 | 84.635 | [80.385, 80.653] | 9.717 | 13.7% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 73.509 | 73.207 | 1.770 | 76.822 |
| 1 | chain_3svc | 200 | 75.667 | 75.261 | 1.999 | 79.181 |
| 1 | chain_4svc | 200 | 78.188 | 77.805 | 2.064 | 81.565 |
| 1 | chain_5svc | 200 | 80.276 | 79.523 | 2.620 | 85.924 |
| 1 | monolithic_k8s_1svc | 200 | 72.103 | 70.849 | 4.078 | 80.010 |
| 2 | chain_2svc | 200 | 73.279 | 73.082 | 1.530 | 76.170 |
| 2 | chain_3svc | 200 | 75.149 | 74.957 | 1.318 | 78.088 |
| 2 | chain_4svc | 200 | 78.004 | 77.835 | 1.444 | 80.604 |
| 2 | chain_5svc | 200 | 80.133 | 79.761 | 2.124 | 83.876 |
| 2 | monolithic_k8s_1svc | 200 | 71.133 | 70.793 | 2.469 | 74.843 |
| 3 | chain_2svc | 200 | 73.301 | 72.998 | 1.755 | 75.684 |
| 3 | chain_3svc | 200 | 75.478 | 75.114 | 2.010 | 77.881 |
| 3 | chain_4svc | 200 | 78.368 | 78.183 | 1.803 | 81.165 |
| 3 | chain_5svc | 200 | 81.299 | 81.083 | 1.788 | 84.731 |
| 3 | monolithic_k8s_1svc | 200 | 70.138 | 69.895 | 1.523 | 73.450 |
| 4 | chain_2svc | 200 | 73.597 | 73.243 | 2.149 | 76.821 |
| 4 | chain_3svc | 200 | 75.372 | 75.057 | 2.055 | 78.272 |
| 4 | chain_4svc | 200 | 78.467 | 77.899 | 2.769 | 82.383 |
| 4 | chain_5svc | 200 | 80.706 | 80.184 | 2.130 | 84.952 |
| 4 | monolithic_k8s_1svc | 200 | 70.230 | 69.938 | 1.819 | 72.780 |
| 5 | chain_2svc | 200 | 73.499 | 73.206 | 1.891 | 76.844 |
| 5 | chain_3svc | 200 | 75.384 | 74.816 | 2.317 | 79.548 |
| 5 | chain_4svc | 200 | 78.445 | 78.082 | 2.581 | 82.350 |
| 5 | chain_5svc | 200 | 80.183 | 79.898 | 1.817 | 83.656 |
| 5 | monolithic_k8s_1svc | 200 | 70.408 | 70.008 | 2.100 | 73.793 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 73.437 | 0.1398 | 0.3183 | 0.0019 |
| chain_3svc | 5 | 75.410 | 0.1879 | 0.5187 | 0.0025 |
| chain_4svc | 5 | 78.294 | 0.1960 | 0.4629 | 0.0025 |
| chain_5svc | 5 | 80.519 | 0.4911 | 1.1659 | 0.0061 |
| monolithic_k8s_1svc | 5 | 70.802 | 0.8255 | 1.9646 | 0.0117 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 2.635 | 3.7% | 980.0 | 4.489 |
| chain_3svc | 4.608 | 6.5% | 1568.0 | 7.073 |
| chain_4svc | 7.492 | 10.6% | 1960.0 | 9.138 |
| chain_5svc | 9.717 | 13.7% | 2058.0 | 10.490 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4


_Cross-stage comparison unavailable because no frozen RQ1.4 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 1.154 | large | 129345.0 | 3.44e-181 |
| chain_3svc | 1.969 | large | 55069.0 | 3.72e-260 |
| chain_4svc | 3.075 | large | 22004.0 | 6.30e-300 |
| chain_5svc | 4.012 | large | 14333.0 | 1.47e-309 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
