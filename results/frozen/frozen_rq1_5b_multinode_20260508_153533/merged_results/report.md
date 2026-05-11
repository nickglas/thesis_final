# RQ1.5b AKS multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `results/frozen/frozen_rq1_5b_multinode_20260508_153533/merged_results\config.yaml`

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
| image | thesisrq15bacr.azurecr.io/thesis-inference@sha256:c5d44bd08783fc78177c2fc4b5d9209d08258309f9d907fcb02cd1315e0fe1de |
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

- **Environment snapshot:** `results/frozen/frozen_rq1_5b_multinode_20260508_153533/merged_results\environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-08T15:51:49.851504 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| multi_node_validation | {'strategy': 'multi_node_anti_affinity', 'passed': True} |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5b_multinode_20260508_153533/partial_results', 'teardown_between_conditions': True} |
| experiment_signature | {'signature': 'rq1_5b_multinode', 'stage': 'RQ1.5b', 'mode': 'multi_node', 'placement_strategy': 'multi_node_anti_affinity', 'namespace': 'rq15b', 'host_export_dir': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5b_multinode_20260508_153533'} |

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
| pod_placement.benchmark-client | aks-rq15bpool-31232045-vmss000000 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15bpool-31232045-vmss000001 |
| pod_placement.chain-2svc-svc-1 | aks-rq15bpool-31232045-vmss000001 |
| pod_placement.chain-2svc-svc-2 | aks-rq15bpool-31232045-vmss000003 |
| pod_placement.chain-3svc-svc-1 | aks-rq15bpool-31232045-vmss000001 |
| pod_placement.chain-3svc-svc-2 | aks-rq15bpool-31232045-vmss000003 |
| pod_placement.chain-3svc-svc-3 | aks-rq15bpool-31232045-vmss000005 |
| pod_placement.chain-4svc-svc-1 | aks-rq15bpool-31232045-vmss000001 |
| pod_placement.chain-4svc-svc-2 | aks-rq15bpool-31232045-vmss000005 |
| pod_placement.chain-4svc-svc-3 | aks-rq15bpool-31232045-vmss000003 |
| pod_placement.chain-4svc-svc-4 | aks-rq15bpool-31232045-vmss000004 |
| pod_placement.chain-5svc-svc-1 | aks-rq15bpool-31232045-vmss000001 |
| pod_placement.chain-5svc-svc-2 | aks-rq15bpool-31232045-vmss000005 |
| pod_placement.chain-5svc-svc-3 | aks-rq15bpool-31232045-vmss000004 |
| pod_placement.chain-5svc-svc-4 | aks-rq15bpool-31232045-vmss000003 |
| pod_placement.chain-5svc-svc-5 | aks-rq15bpool-31232045-vmss000002 |
| container_image_digest | sha256:c5d44bd08783fc78177c2fc4b5d9209d08258309f9d907fcb02cd1315e0fe1de |
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
| monolithic_k8s_1svc | 1000 | 70.118 | 69.807 | 2.277 | 73.249 | [69.977, 70.259] | 0.000 | 0.0% | 70.118 | 0.000 | 0.0% |
| chain_2svc | 1000 | 73.408 | 72.949 | 1.952 | 76.959 | [73.287, 73.529] | 3.290 | 4.7% | 73.967 | -0.559 | -0.8% |
| chain_3svc | 1000 | 75.593 | 75.289 | 1.450 | 77.996 | [75.503, 75.683] | 5.475 | 7.8% | 74.313 | 1.279 | 1.7% |
| chain_4svc | 1000 | 79.342 | 78.981 | 1.730 | 82.521 | [79.235, 79.449] | 9.224 | 13.2% | 76.559 | 2.784 | 3.5% |
| chain_5svc | 1000 | 81.172 | 80.826 | 1.656 | 84.156 | [81.069, 81.275] | 11.054 | 15.8% | 75.621 | 5.551 | 6.8% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 73.379 | 73.021 | 1.734 | 75.674 |
| 1 | chain_3svc | 200 | 75.241 | 75.042 | 1.393 | 77.276 |
| 1 | chain_4svc | 200 | 79.566 | 79.261 | 1.548 | 82.489 |
| 1 | chain_5svc | 200 | 81.527 | 80.996 | 2.010 | 84.783 |
| 1 | monolithic_k8s_1svc | 200 | 69.339 | 69.033 | 1.728 | 72.013 |
| 2 | chain_2svc | 200 | 73.032 | 72.696 | 1.538 | 76.052 |
| 2 | chain_3svc | 200 | 75.186 | 74.932 | 1.168 | 77.407 |
| 2 | chain_4svc | 200 | 79.160 | 78.676 | 1.992 | 83.082 |
| 2 | chain_5svc | 200 | 81.190 | 80.802 | 1.594 | 83.791 |
| 2 | monolithic_k8s_1svc | 200 | 69.973 | 69.738 | 1.777 | 72.922 |
| 3 | chain_2svc | 200 | 72.562 | 72.281 | 1.424 | 74.569 |
| 3 | chain_3svc | 200 | 75.832 | 75.410 | 1.683 | 79.329 |
| 3 | chain_4svc | 200 | 79.220 | 78.548 | 2.032 | 83.166 |
| 3 | chain_5svc | 200 | 81.198 | 80.822 | 1.748 | 84.149 |
| 3 | monolithic_k8s_1svc | 200 | 70.252 | 70.044 | 1.771 | 73.249 |
| 4 | chain_2svc | 200 | 73.543 | 72.925 | 2.286 | 77.824 |
| 4 | chain_3svc | 200 | 75.767 | 75.522 | 1.412 | 78.038 |
| 4 | chain_4svc | 200 | 79.375 | 79.144 | 1.623 | 81.784 |
| 4 | chain_5svc | 200 | 81.156 | 80.822 | 1.431 | 84.157 |
| 4 | monolithic_k8s_1svc | 200 | 70.695 | 69.901 | 3.630 | 74.561 |
| 5 | chain_2svc | 200 | 74.524 | 74.198 | 2.091 | 78.106 |
| 5 | chain_3svc | 200 | 75.937 | 75.713 | 1.387 | 78.287 |
| 5 | chain_4svc | 200 | 79.388 | 79.192 | 1.337 | 82.143 |
| 5 | chain_5svc | 200 | 80.789 | 80.548 | 1.342 | 83.476 |
| 5 | monolithic_k8s_1svc | 200 | 70.331 | 70.070 | 1.590 | 73.220 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 73.408 | 0.7281 | 1.9613 | 0.0099 |
| chain_3svc | 5 | 75.593 | 0.3520 | 0.7515 | 0.0047 |
| chain_4svc | 5 | 79.342 | 0.1593 | 0.4062 | 0.0020 |
| chain_5svc | 5 | 81.172 | 0.2617 | 0.7378 | 0.0032 |
| monolithic_k8s_1svc | 5 | 70.118 | 0.5062 | 1.3566 | 0.0072 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 3.290 | 4.7% | 980.0 | 5.421 |
| chain_3svc | 5.475 | 7.8% | 1568.0 | 8.162 |
| chain_4svc | 9.224 | 13.2% | 1960.0 | 10.814 |
| chain_5svc | 11.054 | 15.8% | 2058.0 | 12.804 |

## RQ1.5b Multi-Node Sensitivity vs Frozen RQ1.5 Single-Node AKS

- **Frozen RQ1.5 single-node reference:** `C:\Users\Nick\Desktop\opus\results\frozen\frozen_rq1_5_fully_controlled_20260508_133209\merged_results\condition_summaries.csv`

| Condition | Single-node Mean (ms) | Multi-node Mean (ms) | Single-node Overhead (%) | Multi-node Overhead (%) | Single-node Rank | Multi-node Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 57.963 | 70.118 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 63.367 | 73.408 | 9.3% | 4.7% | 2 | 2 | true |
| chain_3svc | 66.543 | 75.593 | 14.8% | 7.8% | 3 | 3 | true |
| chain_4svc | 70.698 | 79.342 | 22.0% | 13.2% | 4 | 4 | true |
| chain_5svc | 71.480 | 81.172 | 23.3% | 15.8% | 5 | 5 | true |

### AKS multi-node Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 3.290 |
| chain_2svc → chain_3svc | 2.185 |
| chain_3svc → chain_4svc | 3.750 |
| chain_4svc → chain_5svc | 1.830 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.5 and the AKS multi-node run.
- AKS multi-node overhead remains monotonic with service count when normalized against the AKS multi-node monolithic baseline.
- The bounded-nonlinearity pattern is reproduced on AKS multi-node: the final increment (1.830 ms for chain_5svc) is smaller than the preceding increment (3.750 ms).
- AKS multi-node relative overhead fractions remain comparable for discussion purposes, but they should be interpreted as environment-level effects rather than strict numeric replications of RQ1.5.
- Using the frozen RQ1.5 total-compute means rescaled to the AKS multi-node monolithic baseline as a heuristic compute reference, the chained AKS multi-node conditions retain -0.559–5.551 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
- Deployment metadata confirms every chain segment ran on a distinct cluster node and the benchmark client ran on a sixth dedicated node, so every gRPC hop crossed the Azure VNet.
- Absolute latency differences between frozen RQ1.5 and AKS multi-node are interpreted as environment-level effects and do not by themselves overturn the within-stage architectural comparison.

### Limitations

- Insufficient privileges for nice(-5); running at default nice=0
- cpufreq sysfs not exposed (expected on WSL2/Hyper-V or non-Linux). CPU frequency is managed by the host OS.
- Neither intel_pstate/no_turbo nor cpufreq/boost sysfs entries are exposed. Turbo behaviour is controlled by the host OS.
- Because execution occurred on Azure-managed AKS infrastructure, absolute latency remains sensitive to host scheduling, hypervisor behaviour, and CNI-path variability; these are discussed as environment-level effects rather than architectural reversals.

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| chain_2svc | 1.551 | large | 85557.0 | 5.25e-226 |
| chain_3svc | 2.868 | large | 16485.0 | 7.66e-307 |
| chain_4svc | 4.562 | large | 4233.0 | 0.00e+00 |
| chain_5svc | 5.554 | large | 3066.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
