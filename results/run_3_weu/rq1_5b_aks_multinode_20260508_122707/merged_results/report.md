# RQ1.5b AKS multi-node sensitivity Experiment Report


## Configuration Used

- **Config snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_122707/merged_results/config.yaml`

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
| image | thesisrq15bacr.azurecr.io/thesis-inference@sha256:ab124e921bd17d9883bb1cce41fdef003868c65c9b7c05cd17cfaf22b61acf35 |
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

- **Environment snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_122707/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-08T12:44:44.893762 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| multi_node_validation | {'strategy': 'multi_node_anti_affinity', 'passed': True} |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_122707/partial_results', 'teardown_between_conditions': True} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | 1.34 |
| node_count | 6 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | westeurope |
| cni | kubenet |
| namespace | rq15b |
| pod_colocation_enforced | false |
| pod_placement.benchmark-client | aks-rq15bpool-32050207-vmss000004 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15bpool-32050207-vmss000003 |
| pod_placement.chain-2svc-svc-1 | aks-rq15bpool-32050207-vmss000003 |
| pod_placement.chain-2svc-svc-2 | aks-rq15bpool-32050207-vmss000001 |
| pod_placement.chain-3svc-svc-1 | aks-rq15bpool-32050207-vmss000003 |
| pod_placement.chain-3svc-svc-2 | aks-rq15bpool-32050207-vmss000001 |
| pod_placement.chain-3svc-svc-3 | aks-rq15bpool-32050207-vmss000005 |
| pod_placement.chain-4svc-svc-1 | aks-rq15bpool-32050207-vmss000003 |
| pod_placement.chain-4svc-svc-2 | aks-rq15bpool-32050207-vmss000005 |
| pod_placement.chain-4svc-svc-3 | aks-rq15bpool-32050207-vmss000001 |
| pod_placement.chain-4svc-svc-4 | aks-rq15bpool-32050207-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15bpool-32050207-vmss000003 |
| pod_placement.chain-5svc-svc-2 | aks-rq15bpool-32050207-vmss000001 |
| pod_placement.chain-5svc-svc-3 | aks-rq15bpool-32050207-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15bpool-32050207-vmss000005 |
| pod_placement.chain-5svc-svc-5 | aks-rq15bpool-32050207-vmss000002 |
| container_image_digest | sha256:ab124e921bd17d9883bb1cce41fdef003868c65c9b7c05cd17cfaf22b61acf35 |
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
| monolithic_k8s_1svc | 1000 | 77.326 | 75.362 | 5.414 | 88.731 | [76.990, 77.662] | 0.000 | 0.0% | 77.326 | 0.000 | 0.0% |
| chain_2svc | 1000 | 81.708 | 80.789 | 4.524 | 90.440 | [81.427, 81.989] | 4.382 | 5.7% | 77.326 | 4.382 | 5.4% |
| chain_3svc | 1000 | 92.314 | 91.947 | 5.164 | 102.051 | [91.994, 92.635] | 14.988 | 19.4% | 77.384 | 14.930 | 16.2% |
| chain_4svc | 1000 | 101.248 | 100.984 | 6.153 | 111.509 | [100.866, 101.630] | 23.922 | 30.9% | 79.486 | 21.762 | 21.5% |
| chain_5svc | 1000 | 101.956 | 101.997 | 5.935 | 111.395 | [101.587, 102.324] | 24.630 | 31.9% | 78.146 | 23.810 | 23.4% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 81.654 | 80.758 | 4.717 | 90.352 |
| 1 | chain_3svc | 200 | 92.074 | 91.887 | 4.916 | 100.325 |
| 1 | chain_4svc | 200 | 102.010 | 101.940 | 5.920 | 111.529 |
| 1 | chain_5svc | 200 | 101.803 | 101.782 | 5.878 | 110.705 |
| 1 | monolithic_k8s_1svc | 200 | 77.292 | 75.442 | 5.106 | 88.671 |
| 2 | chain_2svc | 200 | 81.062 | 80.374 | 3.819 | 88.035 |
| 2 | chain_3svc | 200 | 91.959 | 91.247 | 5.363 | 101.494 |
| 2 | chain_4svc | 200 | 102.807 | 102.427 | 5.831 | 113.678 |
| 2 | chain_5svc | 200 | 102.359 | 102.227 | 6.037 | 112.264 |
| 2 | monolithic_k8s_1svc | 200 | 77.321 | 75.571 | 5.954 | 87.018 |
| 3 | chain_2svc | 200 | 81.587 | 80.402 | 4.954 | 89.436 |
| 3 | chain_3svc | 200 | 93.441 | 92.539 | 4.876 | 103.702 |
| 3 | chain_4svc | 200 | 100.680 | 99.967 | 6.543 | 112.310 |
| 3 | chain_5svc | 200 | 102.707 | 102.662 | 5.859 | 111.860 |
| 3 | monolithic_k8s_1svc | 200 | 77.831 | 76.055 | 5.300 | 89.160 |
| 4 | chain_2svc | 200 | 80.980 | 80.189 | 3.784 | 87.879 |
| 4 | chain_3svc | 200 | 92.024 | 91.925 | 5.747 | 102.472 |
| 4 | chain_4svc | 200 | 100.035 | 100.021 | 6.594 | 110.036 |
| 4 | chain_5svc | 200 | 100.700 | 100.938 | 5.776 | 111.174 |
| 4 | monolithic_k8s_1svc | 200 | 77.668 | 75.320 | 5.421 | 88.779 |
| 5 | chain_2svc | 200 | 83.257 | 82.235 | 4.864 | 92.102 |
| 5 | chain_3svc | 200 | 92.073 | 91.586 | 4.748 | 100.002 |
| 5 | chain_4svc | 200 | 100.709 | 100.151 | 5.438 | 110.188 |
| 5 | chain_5svc | 200 | 102.209 | 102.311 | 5.978 | 111.192 |
| 5 | monolithic_k8s_1svc | 200 | 76.518 | 74.322 | 5.208 | 87.825 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 81.708 | 0.9171 | 2.2771 | 0.0112 |
| chain_3svc | 5 | 92.314 | 0.6315 | 1.4817 | 0.0068 |
| chain_4svc | 5 | 101.248 | 1.1288 | 2.7725 | 0.0111 |
| chain_5svc | 5 | 101.956 | 0.7734 | 2.0076 | 0.0076 |
| monolithic_k8s_1svc | 5 | 77.326 | 0.5066 | 1.3133 | 0.0066 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 4.382 | 5.7% | 980.0 | 9.291 |
| chain_3svc | 14.988 | 19.4% | 1568.0 | 14.435 |
| chain_4svc | 23.922 | 30.9% | 1960.0 | 18.326 |
| chain_5svc | 24.630 | 31.9% | 2058.0 | 21.423 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4

- **Frozen RQ1.4 reference:** `/mnt/c/Users/Nick/Desktop/opus/results/frozen/frozen_rq1_4_fully_controlled_20260421_125049/merged_results/condition_summaries.csv`

| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 81.447 | 77.326 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 84.189 | 81.708 | 3.4% | 5.7% | 2 | 2 | true |
| chain_3svc | 87.608 | 92.314 | 7.6% | 19.4% | 3 | 3 | true |
| chain_4svc | 92.312 | 101.248 | 13.3% | 30.9% | 4 | 4 | true |
| chain_5svc | 92.624 | 101.956 | 13.7% | 31.9% | 5 | 5 | true |

### AKS Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 4.382 |
| chain_2svc → chain_3svc | 10.606 |
| chain_3svc → chain_4svc | 8.934 |
| chain_4svc → chain_5svc | 0.708 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.4 and the AKS run.
- AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline.
- The bounded-nonlinearity pattern is reproduced on AKS: the final increment (0.708 ms for chain_5svc) is smaller than the preceding increment (8.934 ms).
- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal.
- Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, the chained AKS conditions retain 4.382–23.810 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
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
| chain_2svc | 0.878 | large | 230837.0 | 1.73e-96 |
| chain_3svc | 2.833 | large | 32392.0 | 3.99e-287 |
| chain_4svc | 4.128 | large | 5027.0 | 0.00e+00 |
| chain_5svc | 4.336 | large | 4056.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
