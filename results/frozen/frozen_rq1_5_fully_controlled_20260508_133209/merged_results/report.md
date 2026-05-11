# RQ1.5 AKS fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `results/frozen/frozen_rq1_5_fully_controlled_20260508_133209/merged_results\config.yaml`

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
| image | thesisrq15acr.azurecr.io/thesis-inference@sha256:1f002f8a8f816a1ca5c8ee05c3a1d2429822eb0de7405e7f3781621cd7406bed |
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

- **Environment snapshot:** `results/frozen/frozen_rq1_5_fully_controlled_20260508_133209/merged_results\environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-08T13:47:02.232944 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_133209/partial_results', 'teardown_between_conditions': True} |
| experiment_signature | {'signature': 'rq1_5_fully_controlled', 'stage': 'RQ1.5', 'mode': 'single_node', 'placement_strategy': 'none', 'namespace': 'rq15', 'host_export_dir': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_133209'} |

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
| pod_placement.benchmark-client | aks-rq15pool-29881638-vmss000000 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-2svc-svc-1 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-2svc-svc-2 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-3svc-svc-1 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-3svc-svc-2 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-3svc-svc-3 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-4svc-svc-1 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-4svc-svc-2 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-4svc-svc-3 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-4svc-svc-4 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-5svc-svc-2 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-5svc-svc-3 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15pool-29881638-vmss000000 |
| pod_placement.chain-5svc-svc-5 | aks-rq15pool-29881638-vmss000000 |
| container_image_digest | sha256:1f002f8a8f816a1ca5c8ee05c3a1d2429822eb0de7405e7f3781621cd7406bed |
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
| monolithic_k8s_1svc | 1000 | 57.963 | 57.759 | 2.824 | 62.568 | [57.788, 58.138] | 0.000 | 0.0% | 57.963 | -0.000 | -0.0% |
| chain_2svc | 1000 | 63.367 | 62.981 | 2.470 | 67.795 | [63.214, 63.520] | 5.404 | 9.3% | 57.963 | 5.404 | 8.5% |
| chain_3svc | 1000 | 66.543 | 66.096 | 2.953 | 71.406 | [66.360, 66.727] | 8.580 | 14.8% | 58.006 | 8.537 | 12.8% |
| chain_4svc | 1000 | 70.698 | 70.234 | 3.302 | 76.335 | [70.493, 70.903] | 12.735 | 22.0% | 59.582 | 11.116 | 15.7% |
| chain_5svc | 1000 | 71.480 | 70.968 | 3.142 | 76.815 | [71.285, 71.675] | 13.517 | 23.3% | 58.578 | 12.902 | 18.1% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 62.834 | 62.629 | 2.488 | 67.489 |
| 1 | chain_3svc | 200 | 65.933 | 65.368 | 2.703 | 71.102 |
| 1 | chain_4svc | 200 | 70.877 | 70.240 | 3.461 | 76.437 |
| 1 | chain_5svc | 200 | 70.629 | 70.299 | 2.630 | 76.136 |
| 1 | monolithic_k8s_1svc | 200 | 56.966 | 56.640 | 2.461 | 60.887 |
| 2 | chain_2svc | 200 | 63.004 | 62.669 | 2.501 | 67.010 |
| 2 | chain_3svc | 200 | 66.670 | 66.254 | 2.726 | 71.025 |
| 2 | chain_4svc | 200 | 69.060 | 68.496 | 2.740 | 73.532 |
| 2 | chain_5svc | 200 | 70.774 | 70.436 | 2.607 | 74.774 |
| 2 | monolithic_k8s_1svc | 200 | 56.916 | 56.674 | 2.738 | 61.651 |
| 3 | chain_2svc | 200 | 64.032 | 63.540 | 2.322 | 68.044 |
| 3 | chain_3svc | 200 | 66.135 | 65.377 | 3.555 | 72.071 |
| 3 | chain_4svc | 200 | 70.710 | 70.007 | 3.441 | 77.867 |
| 3 | chain_5svc | 200 | 71.556 | 70.986 | 3.140 | 75.734 |
| 3 | monolithic_k8s_1svc | 200 | 59.110 | 59.124 | 2.888 | 63.645 |
| 4 | chain_2svc | 200 | 63.356 | 63.092 | 2.543 | 67.787 |
| 4 | chain_3svc | 200 | 67.155 | 66.923 | 2.751 | 70.767 |
| 4 | chain_4svc | 200 | 70.945 | 70.335 | 3.240 | 76.355 |
| 4 | chain_5svc | 200 | 71.319 | 70.679 | 2.969 | 76.335 |
| 4 | monolithic_k8s_1svc | 200 | 57.181 | 57.128 | 2.161 | 60.711 |
| 5 | chain_2svc | 200 | 63.610 | 63.206 | 2.322 | 67.833 |
| 5 | chain_3svc | 200 | 66.824 | 66.332 | 2.797 | 71.138 |
| 5 | chain_4svc | 200 | 71.898 | 71.555 | 2.947 | 77.100 |
| 5 | chain_5svc | 200 | 73.121 | 72.558 | 3.634 | 79.229 |
| 5 | monolithic_k8s_1svc | 200 | 59.641 | 59.198 | 2.572 | 63.575 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 63.367 | 0.4787 | 1.1978 | 0.0076 |
| chain_3svc | 5 | 66.543 | 0.5018 | 1.2214 | 0.0075 |
| chain_4svc | 5 | 70.698 | 1.0266 | 2.8378 | 0.0145 |
| chain_5svc | 5 | 71.480 | 0.9935 | 2.4923 | 0.0139 |
| monolithic_k8s_1svc | 5 | 57.963 | 1.3069 | 2.7250 | 0.0225 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 5.404 | 9.3% | 980.0 | 5.527 |
| chain_3svc | 8.580 | 14.8% | 1568.0 | 8.433 |
| chain_4svc | 12.735 | 22.0% | 1960.0 | 10.832 |
| chain_5svc | 13.517 | 23.3% | 2058.0 | 12.346 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4

- **Frozen RQ1.4 reference:** `C:\Users\Nick\Desktop\opus\results\frozen\frozen_rq1_4_fully_controlled_20260421_125049\merged_results\condition_summaries.csv`

| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 81.447 | 57.963 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 84.189 | 63.367 | 3.4% | 9.3% | 2 | 2 | true |
| chain_3svc | 87.608 | 66.543 | 7.6% | 14.8% | 3 | 3 | true |
| chain_4svc | 92.312 | 70.698 | 13.3% | 22.0% | 4 | 4 | true |
| chain_5svc | 92.624 | 71.480 | 13.7% | 23.3% | 5 | 5 | true |

### AKS Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 5.404 |
| chain_2svc → chain_3svc | 3.176 |
| chain_3svc → chain_4svc | 4.155 |
| chain_4svc → chain_5svc | 0.782 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.4 and the AKS run.
- AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline.
- The bounded-nonlinearity pattern is reproduced on AKS: the final increment (0.782 ms for chain_5svc) is smaller than the preceding increment (4.155 ms).
- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal.
- Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, the chained AKS conditions retain 5.404–12.902 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
- Deployment metadata confirms same-node service placement for each measured condition, preserving the RQ1.4 intra-condition topology while moving execution to AKS.
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
| chain_2svc | 2.037 | large | 59770.0 | 9.86e-255 |
| chain_3svc | 2.970 | large | 15945.0 | 1.60e-307 |
| chain_4svc | 4.145 | large | 4666.0 | 0.00e+00 |
| chain_5svc | 4.525 | large | 3967.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
