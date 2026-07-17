# RQ1.5b AKS multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_5b_multinode_20260515_152628/merged_results/config.yaml`

### Experiment

| Setting | Value |
|---|---|
| name | RQ1.5b AKS multi-node sensitivity |
| description | AKS multi-node sensitivity: every chain hop crosses a node boundary |

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
| namespace | rq15b |
| service_name_template | {condition}-svc-{index} |
| grpc_port | 50051 |
| max_message_bytes | 16777216 |
| readiness_timeout | 180.0 |
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
| placement.strategy | multi_node_anti_affinity |
| placement.require_distinct_nodes | true |
| placement.require_dedicated_client_node | true |
| placement.min_nodes | 6 |
| placement.node_pool | rq15bpool |

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

- **Environment snapshot:** `/home/nick/Desktop/thesis_final/results/rq1_5b_multinode_20260515_152628/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-15T15:36:07.797460 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cpu |
| cpu_count | 8 |
| git_commit | unknown |
| multi_node_validation | {'strategy': 'multi_node_anti_affinity', 'passed': True} |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/home/nick/Desktop/thesis_final/results/rq1_5b_multinode_20260515_152628/partial_results', 'teardown_between_conditions': True} |
| experiment_signature | {'signature': 'rq1_5b_multinode', 'stage': 'RQ1.5b', 'mode': 'multi_node', 'placement_strategy': 'multi_node_anti_affinity', 'namespace': 'rq15b', 'host_export_dir': '/home/nick/Desktop/thesis_final/results/rq1_5b_multinode_20260515_152628'} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | 1.34 |
| node_count | 6 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | swedencentral |
| cni | kubenet |
| namespace | rq15b |
| pod_colocation_enforced | false |
| pod_placement.benchmark-client | aks-rq15bpool-31407731-vmss000002 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15bpool-31407731-vmss000004 |
| pod_placement.chain-2svc-svc-1 | aks-rq15bpool-31407731-vmss000004 |
| pod_placement.chain-2svc-svc-2 | aks-rq15bpool-31407731-vmss000005 |
| pod_placement.chain-3svc-svc-1 | aks-rq15bpool-31407731-vmss000004 |
| pod_placement.chain-3svc-svc-2 | aks-rq15bpool-31407731-vmss000005 |
| pod_placement.chain-3svc-svc-3 | aks-rq15bpool-31407731-vmss000000 |
| pod_placement.chain-4svc-svc-1 | aks-rq15bpool-31407731-vmss000004 |
| pod_placement.chain-4svc-svc-2 | aks-rq15bpool-31407731-vmss000000 |
| pod_placement.chain-4svc-svc-3 | aks-rq15bpool-31407731-vmss000005 |
| pod_placement.chain-4svc-svc-4 | aks-rq15bpool-31407731-vmss000003 |
| pod_placement.chain-5svc-svc-1 | aks-rq15bpool-31407731-vmss000004 |
| pod_placement.chain-5svc-svc-2 | aks-rq15bpool-31407731-vmss000003 |
| pod_placement.chain-5svc-svc-3 | aks-rq15bpool-31407731-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15bpool-31407731-vmss000005 |
| pod_placement.chain-5svc-svc-5 | aks-rq15bpool-31407731-vmss000001 |
| container_image_digest | sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b |
| acr_registry | thesisrq15acr.azurecr.io |
| mesh.enabled | false |
| mesh.implementation | n/a |
| mesh.revision | n/a |
| mesh.service_namespace | rq15b |
| mesh.client_namespace | rq15b |
| mesh.peer_authentication.observed | n/a |
| mesh.control_plane_pods | n/a |
| namespaces.service.name | rq15b |
| namespaces.service.labels.experiment | rq15b |
| namespaces.service.labels.kubernetes.io/metadata.name | rq15b |
| namespaces.service.annotations.kubectl.kubernetes.io/last-applied-configuration | {"apiVersion":"v1","kind":"Namespace","metadata":{"annotations":{},"labels":{"experiment":"rq15b"},"name":"rq15b"}}<br> |
| namespaces.client.name | rq15b |
| namespaces.client.labels.experiment | rq15b |
| namespaces.client.labels.kubernetes.io/metadata.name | rq15b |
| namespaces.client.annotations.kubectl.kubernetes.io/last-applied-configuration | {"apiVersion":"v1","kind":"Namespace","metadata":{"annotations":{},"labels":{"experiment":"rq15b"},"name":"rq15b"}}<br> |

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
| monolithic_k8s_1svc | 1000 | 73.108 | 72.403 | 3.707 | 79.598 | [72.878, 73.338] | 0.000 | 0.0% | n/a | n/a | n/a |
| chain_2svc | 1000 | 76.470 | 75.653 | 3.435 | 82.696 | [76.257, 76.683] | 3.362 | 4.6% | n/a | n/a | n/a |
| chain_3svc | 1000 | 77.541 | 76.848 | 2.786 | 83.041 | [77.368, 77.713] | 4.433 | 6.1% | n/a | n/a | n/a |
| chain_4svc | 1000 | 82.103 | 81.660 | 2.355 | 86.394 | [81.956, 82.249] | 8.995 | 12.3% | n/a | n/a | n/a |
| chain_5svc | 1000 | 84.605 | 84.131 | 2.497 | 89.186 | [84.450, 84.760] | 11.497 | 15.7% | n/a | n/a | n/a |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 75.618 | 74.874 | 2.988 | 80.960 |
| 1 | chain_3svc | 200 | 77.980 | 76.889 | 2.962 | 84.173 |
| 1 | chain_4svc | 200 | 81.874 | 81.287 | 2.804 | 87.652 |
| 1 | chain_5svc | 200 | 84.916 | 84.560 | 2.372 | 89.113 |
| 1 | monolithic_k8s_1svc | 200 | 73.936 | 73.144 | 3.941 | 80.860 |
| 2 | chain_2svc | 200 | 76.800 | 76.017 | 3.261 | 83.030 |
| 2 | chain_3svc | 200 | 77.152 | 76.426 | 3.046 | 81.994 |
| 2 | chain_4svc | 200 | 81.761 | 81.257 | 2.161 | 85.422 |
| 2 | chain_5svc | 200 | 84.328 | 83.790 | 2.667 | 89.331 |
| 2 | monolithic_k8s_1svc | 200 | 73.274 | 72.445 | 3.997 | 80.233 |
| 3 | chain_2svc | 200 | 75.600 | 74.842 | 2.753 | 81.334 |
| 3 | chain_3svc | 200 | 77.056 | 76.649 | 2.232 | 80.656 |
| 3 | chain_4svc | 200 | 82.726 | 82.129 | 2.507 | 87.565 |
| 3 | chain_5svc | 200 | 84.264 | 83.888 | 1.993 | 88.036 |
| 3 | monolithic_k8s_1svc | 200 | 73.326 | 72.954 | 3.823 | 79.290 |
| 4 | chain_2svc | 200 | 77.937 | 76.583 | 4.557 | 86.467 |
| 4 | chain_3svc | 200 | 77.978 | 77.244 | 3.158 | 85.091 |
| 4 | chain_4svc | 200 | 82.020 | 81.706 | 1.878 | 85.607 |
| 4 | chain_5svc | 200 | 84.891 | 84.482 | 2.740 | 89.273 |
| 4 | monolithic_k8s_1svc | 200 | 72.576 | 72.070 | 2.992 | 78.215 |
| 5 | chain_2svc | 200 | 76.397 | 75.968 | 2.751 | 81.078 |
| 5 | chain_3svc | 200 | 77.537 | 77.078 | 2.275 | 82.323 |
| 5 | chain_4svc | 200 | 82.132 | 81.747 | 2.221 | 86.398 |
| 5 | chain_5svc | 200 | 84.626 | 84.089 | 2.591 | 90.113 |
| 5 | monolithic_k8s_1svc | 200 | 72.428 | 71.595 | 3.521 | 79.212 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 76.470 | 0.9679 | 2.3363 | 0.0127 |
| chain_3svc | 5 | 77.541 | 0.4388 | 0.9236 | 0.0057 |
| chain_4svc | 5 | 82.103 | 0.3757 | 0.9645 | 0.0046 |
| chain_5svc | 5 | 84.605 | 0.3047 | 0.6512 | 0.0036 |
| monolithic_k8s_1svc | 5 | 73.108 | 0.6134 | 1.5076 | 0.0084 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 3.362 | 4.6% | 980.0 | 6.084 |
| chain_3svc | 4.433 | 6.1% | 1568.0 | 8.983 |
| chain_4svc | 8.995 | 12.3% | 1960.0 | 11.537 |
| chain_5svc | 11.497 | 15.7% | 2058.0 | 14.176 |

## RQ1.5b Multi-Node Sensitivity vs Frozen RQ1.5 Single-Node AKS


_Cross-stage comparison unavailable because no frozen RQ1.5 summary artifact was found._

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 0.941 | large | 219281.0 | 8.79e-105 |
| chain_3svc | 1.352 | large | 147496.0 | 4.48e-164 |
| chain_4svc | 2.896 | large | 28739.0 | 1.35e-291 |
| chain_5svc | 3.638 | large | 13918.0 | 4.37e-310 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
