# RQ1.5b AKS multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `C:\Users\Nick\Desktop\opus\results_exports\rq1_5_fully_controlled_20260507_203505\merged_results\config.yaml`

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
| image | thesisrq15bacr.azurecr.io/thesis-inference@sha256:35b0d31329665430413c5c4c35fe8e404035b66619948424629b27eb687c5a75 |
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

- **Environment snapshot:** `C:\Users\Nick\Desktop\opus\results_exports\rq1_5_fully_controlled_20260507_203505\merged_results\environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T20:51:00.448404 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| multi_node_validation | {'strategy': 'multi_node_anti_affinity', 'passed': True} |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': 'C:\\Users\\Nick\\Desktop\\opus\\results_exports\\rq1_5_fully_controlled_20260507_203505\\partial_results', 'teardown_between_conditions': True} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | v1.34.6 |
| node_count | 6 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | westeurope |
| cni | unknown |
| namespace | rq15b |
| pod_colocation_enforced | false |
| pod_placement.benchmark-client | aks-rq15bpool-77818884-vmss000003 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15bpool-77818884-vmss000004 |
| pod_placement.chain-2svc-svc-1 | aks-rq15bpool-77818884-vmss000004 |
| pod_placement.chain-2svc-svc-2 | aks-rq15bpool-77818884-vmss000002 |
| pod_placement.chain-3svc-svc-1 | aks-rq15bpool-77818884-vmss000004 |
| pod_placement.chain-3svc-svc-2 | aks-rq15bpool-77818884-vmss000002 |
| pod_placement.chain-3svc-svc-3 | aks-rq15bpool-77818884-vmss000005 |
| pod_placement.chain-4svc-svc-1 | aks-rq15bpool-77818884-vmss000004 |
| pod_placement.chain-4svc-svc-2 | aks-rq15bpool-77818884-vmss000005 |
| pod_placement.chain-4svc-svc-3 | aks-rq15bpool-77818884-vmss000002 |
| pod_placement.chain-4svc-svc-4 | aks-rq15bpool-77818884-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15bpool-77818884-vmss000004 |
| pod_placement.chain-5svc-svc-2 | aks-rq15bpool-77818884-vmss000002 |
| pod_placement.chain-5svc-svc-3 | aks-rq15bpool-77818884-vmss000005 |
| pod_placement.chain-5svc-svc-4 | aks-rq15bpool-77818884-vmss000000 |
| pod_placement.chain-5svc-svc-5 | aks-rq15bpool-77818884-vmss000001 |
| container_image_digest | sha256:35b0d31329665430413c5c4c35fe8e404035b66619948424629b27eb687c5a75 |
| acr_registry | thesisrq15bacr.azurecr.io |
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
| priority.error | Insufficient privileges for nice(-5); running at default nice=0 |
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
| monolithic_k8s_1svc | 1000 | 62.221 | 62.145 | 3.321 | 67.446 | [62.015, 62.427] | 0.000 | 0.0% | 62.221 | 0.000 | 0.0% |
| chain_2svc | 1000 | 74.692 | 74.380 | 3.050 | 80.337 | [74.503, 74.882] | 12.471 | 20.0% | 62.221 | 12.471 | 16.7% |
| chain_3svc | 1000 | 75.970 | 75.799 | 3.126 | 80.879 | [75.776, 76.164] | 13.749 | 22.1% | 62.267 | 13.703 | 18.0% |
| chain_4svc | 1000 | 80.623 | 80.520 | 3.062 | 85.860 | [80.433, 80.813] | 18.402 | 29.6% | 63.959 | 16.664 | 20.7% |
| chain_5svc | 1000 | 83.089 | 82.610 | 3.015 | 88.843 | [82.902, 83.277] | 20.868 | 33.5% | 62.881 | 20.209 | 24.3% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 75.596 | 75.360 | 3.116 | 81.080 |
| 1 | chain_3svc | 200 | 75.463 | 75.172 | 2.998 | 79.711 |
| 1 | chain_4svc | 200 | 80.217 | 80.194 | 2.930 | 85.525 |
| 1 | chain_5svc | 200 | 83.325 | 82.659 | 3.178 | 88.748 |
| 1 | monolithic_k8s_1svc | 200 | 63.339 | 62.944 | 3.292 | 69.126 |
| 2 | chain_2svc | 200 | 74.616 | 74.562 | 2.802 | 79.153 |
| 2 | chain_3svc | 200 | 75.918 | 75.746 | 3.189 | 81.265 |
| 2 | chain_4svc | 200 | 79.953 | 79.849 | 3.450 | 85.653 |
| 2 | chain_5svc | 200 | 82.859 | 82.481 | 2.706 | 88.078 |
| 2 | monolithic_k8s_1svc | 200 | 60.962 | 61.451 | 3.190 | 65.001 |
| 3 | chain_2svc | 200 | 74.970 | 74.484 | 3.371 | 81.855 |
| 3 | chain_3svc | 200 | 75.681 | 75.571 | 2.963 | 80.531 |
| 3 | chain_4svc | 200 | 80.468 | 80.461 | 3.051 | 85.530 |
| 3 | chain_5svc | 200 | 82.780 | 82.402 | 2.769 | 87.907 |
| 3 | monolithic_k8s_1svc | 200 | 61.093 | 60.878 | 3.234 | 65.779 |
| 4 | chain_2svc | 200 | 74.671 | 74.231 | 2.881 | 79.716 |
| 4 | chain_3svc | 200 | 76.637 | 76.351 | 3.092 | 81.480 |
| 4 | chain_4svc | 200 | 81.286 | 81.069 | 2.979 | 86.782 |
| 4 | chain_5svc | 200 | 83.632 | 83.431 | 3.146 | 89.725 |
| 4 | monolithic_k8s_1svc | 200 | 63.582 | 63.530 | 2.708 | 67.805 |
| 5 | chain_2svc | 200 | 73.609 | 73.276 | 2.721 | 78.204 |
| 5 | chain_3svc | 200 | 76.153 | 76.186 | 3.278 | 81.010 |
| 5 | chain_4svc | 200 | 81.192 | 81.157 | 2.646 | 85.693 |
| 5 | chain_5svc | 200 | 82.851 | 82.037 | 3.178 | 89.016 |
| 5 | monolithic_k8s_1svc | 200 | 62.130 | 61.877 | 3.252 | 67.739 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 74.692 | 0.7198 | 1.9862 | 0.0096 |
| chain_3svc | 5 | 75.970 | 0.4535 | 1.1749 | 0.0060 |
| chain_4svc | 5 | 80.623 | 0.5918 | 1.3332 | 0.0073 |
| chain_5svc | 5 | 83.089 | 0.3725 | 0.8516 | 0.0045 |
| monolithic_k8s_1svc | 5 | 62.221 | 1.2215 | 2.6203 | 0.0196 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 12.471 | 20.0% | 980.0 | 7.677 |
| chain_3svc | 13.749 | 22.1% | 1568.0 | 11.736 |
| chain_4svc | 18.402 | 29.6% | 1960.0 | 14.750 |
| chain_5svc | 20.868 | 33.5% | 2058.0 | 17.362 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4

- **Frozen RQ1.4 reference:** `C:\Users\Nick\Desktop\opus\results\frozen\frozen_rq1_4_fully_controlled_20260421_125049\merged_results\condition_summaries.csv`

| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 81.447 | 62.221 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 84.189 | 74.692 | 3.4% | 20.0% | 2 | 2 | true |
| chain_3svc | 87.608 | 75.970 | 7.6% | 22.1% | 3 | 3 | true |
| chain_4svc | 92.312 | 80.623 | 13.3% | 29.6% | 4 | 4 | true |
| chain_5svc | 92.624 | 83.089 | 13.7% | 33.5% | 5 | 5 | true |

### AKS Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 12.471 |
| chain_2svc → chain_3svc | 1.278 |
| chain_3svc → chain_4svc | 4.653 |
| chain_4svc → chain_5svc | 2.466 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.4 and the AKS run.
- AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline.
- The bounded-nonlinearity pattern is reproduced on AKS: the final increment (2.466 ms for chain_5svc) is smaller than the preceding increment (4.653 ms).
- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal.
- Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, the chained AKS conditions retain 12.471–20.209 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
- Absolute latency differences between frozen RQ1.4 and AKS are interpreted as environment-level effects and do not by themselves overturn the within-stage architectural comparison.

### Limitations

- Insufficient privileges for nice(-5); running at default nice=0
- cpufreq sysfs not exposed (expected on WSL2/Hyper-V or non-Linux). CPU frequency is managed by the host OS.
- Neither intel_pstate/no_turbo nor cpufreq/boost sysfs entries are exposed. Turbo behaviour is controlled by the host OS.
- Because execution occurred on Azure-managed AKS infrastructure, absolute latency remains sensitive to host scheduling, hypervisor behaviour, and CNI-path variability; these are discussed as environment-level effects rather than architectural reversals.

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 3.911 | large | 3708.0 | 0.00e+00 |
| chain_3svc | 4.263 | large | 2238.0 | 0.00e+00 |
| chain_4svc | 5.761 | large | 442.0 | 0.00e+00 |
| chain_5svc | 6.579 | large | 101.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
