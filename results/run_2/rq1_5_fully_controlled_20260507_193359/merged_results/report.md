# RQ1.5 AKS fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `C:\Users\Nick\Desktop\opus\results_exports\rq1_5_fully_controlled_20260507_193359\merged_results\config.yaml`

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
| image | thesisrq15acr.azurecr.io/thesis-inference@sha256:ead3879015f39d6fe1e2522ced558a94986ca80b6d77f9fcf159b968f7cc4e13 |
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

- **Environment snapshot:** `C:\Users\Nick\Desktop\opus\results_exports\rq1_5_fully_controlled_20260507_193359\merged_results\environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-07T19:55:10.390036 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': 'C:\\Users\\Nick\\Desktop\\opus\\results_exports\\rq1_5_fully_controlled_20260507_193359\\partial_results', 'teardown_between_conditions': True} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | v1.34.6 |
| node_count | 1 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | westeurope |
| cni | unknown |
| namespace | rq15 |
| pod_colocation_enforced | true |
| pod_placement.benchmark-client | aks-rq15pool-11522835-vmss000000 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-2svc-svc-1 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-2svc-svc-2 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-3svc-svc-1 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-3svc-svc-2 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-3svc-svc-3 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-4svc-svc-1 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-4svc-svc-2 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-4svc-svc-3 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-4svc-svc-4 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-5svc-svc-2 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-5svc-svc-3 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15pool-11522835-vmss000000 |
| pod_placement.chain-5svc-svc-5 | aks-rq15pool-11522835-vmss000000 |
| container_image_digest | sha256:ead3879015f39d6fe1e2522ced558a94986ca80b6d77f9fcf159b968f7cc4e13 |
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
| monolithic_k8s_1svc | 1000 | 64.203 | 63.188 | 3.892 | 71.560 | [63.961, 64.444] | 0.000 | 0.0% | 64.203 | 0.000 | 0.0% |
| chain_2svc | 1000 | 71.671 | 71.046 | 4.074 | 79.902 | [71.418, 71.924] | 7.468 | 11.6% | 64.203 | 7.468 | 10.4% |
| chain_3svc | 1000 | 75.919 | 75.128 | 4.554 | 83.971 | [75.637, 76.202] | 11.717 | 18.2% | 64.251 | 11.669 | 15.4% |
| chain_4svc | 1000 | 79.226 | 78.538 | 4.325 | 87.410 | [78.958, 79.495] | 15.024 | 23.4% | 65.996 | 13.230 | 16.7% |
| chain_5svc | 1000 | 82.665 | 81.764 | 4.954 | 92.026 | [82.357, 82.972] | 18.462 | 28.8% | 64.883 | 17.781 | 21.5% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 70.183 | 69.426 | 3.527 | 77.876 |
| 1 | chain_3svc | 200 | 75.363 | 75.091 | 4.061 | 83.344 |
| 1 | chain_4svc | 200 | 78.093 | 77.331 | 4.036 | 85.953 |
| 1 | chain_5svc | 200 | 82.680 | 81.731 | 4.485 | 90.403 |
| 1 | monolithic_k8s_1svc | 200 | 66.304 | 64.753 | 5.424 | 76.350 |
| 2 | chain_2svc | 200 | 73.300 | 72.295 | 4.561 | 81.710 |
| 2 | chain_3svc | 200 | 76.859 | 75.790 | 5.461 | 86.474 |
| 2 | chain_4svc | 200 | 78.967 | 78.283 | 4.232 | 87.521 |
| 2 | chain_5svc | 200 | 82.798 | 81.634 | 5.588 | 94.106 |
| 2 | monolithic_k8s_1svc | 200 | 65.076 | 63.975 | 3.620 | 71.375 |
| 3 | chain_2svc | 200 | 72.635 | 71.698 | 3.926 | 80.862 |
| 3 | chain_3svc | 200 | 75.621 | 75.128 | 3.885 | 82.201 |
| 3 | chain_4svc | 200 | 79.052 | 78.635 | 3.825 | 85.451 |
| 3 | chain_5svc | 200 | 84.222 | 83.544 | 4.780 | 92.830 |
| 3 | monolithic_k8s_1svc | 200 | 64.346 | 63.448 | 3.324 | 71.298 |
| 4 | chain_2svc | 200 | 71.082 | 70.298 | 4.087 | 77.585 |
| 4 | chain_3svc | 200 | 76.145 | 74.965 | 4.606 | 84.073 |
| 4 | chain_4svc | 200 | 79.571 | 78.784 | 4.160 | 86.662 |
| 4 | chain_5svc | 200 | 80.891 | 79.772 | 4.494 | 89.305 |
| 4 | monolithic_k8s_1svc | 200 | 62.444 | 62.059 | 2.092 | 65.451 |
| 5 | chain_2svc | 200 | 71.156 | 70.715 | 3.392 | 78.151 |
| 5 | chain_3svc | 200 | 75.609 | 74.653 | 4.479 | 83.693 |
| 5 | chain_4svc | 200 | 80.449 | 79.353 | 4.978 | 89.716 |
| 5 | chain_5svc | 200 | 82.733 | 82.128 | 4.818 | 91.161 |
| 5 | monolithic_k8s_1svc | 200 | 62.843 | 62.211 | 2.809 | 68.211 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 71.671 | 1.2660 | 3.1173 | 0.0177 |
| chain_3svc | 5 | 75.919 | 0.5976 | 1.4956 | 0.0079 |
| chain_4svc | 5 | 79.226 | 0.8653 | 2.3557 | 0.0109 |
| chain_5svc | 5 | 82.665 | 1.1826 | 3.3311 | 0.0143 |
| monolithic_k8s_1svc | 5 | 64.203 | 1.5923 | 3.8599 | 0.0248 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 7.468 | 11.6% | 980.0 | 6.560 |
| chain_3svc | 11.717 | 18.2% | 1568.0 | 9.901 |
| chain_4svc | 15.024 | 23.4% | 1960.0 | 12.204 |
| chain_5svc | 18.462 | 28.8% | 2058.0 | 14.241 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4

- **Frozen RQ1.4 reference:** `C:\Users\Nick\Desktop\opus\results\frozen\frozen_rq1_4_fully_controlled_20260421_125049\merged_results\condition_summaries.csv`

| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 81.447 | 64.203 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 84.189 | 71.671 | 3.4% | 11.6% | 2 | 2 | true |
| chain_3svc | 87.608 | 75.919 | 7.6% | 18.2% | 3 | 3 | true |
| chain_4svc | 92.312 | 79.226 | 13.3% | 23.4% | 4 | 4 | true |
| chain_5svc | 92.624 | 82.665 | 13.7% | 28.8% | 5 | 5 | true |

### AKS Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 7.468 |
| chain_2svc → chain_3svc | 4.248 |
| chain_3svc → chain_4svc | 3.307 |
| chain_4svc → chain_5svc | 3.438 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.4 and the AKS run.
- AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline.
- The exact chain_4svc→chain_5svc near-plateau from RQ1.4 is not reproduced on AKS: the final increment is 3.438 ms versus 3.307 ms for the preceding step.
- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal.
- Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, the chained AKS conditions retain 7.468–17.781 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
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
| chain_2svc | 1.875 | large | 73261.0 | 1.73e-239 |
| chain_3svc | 2.766 | large | 26757.0 | 4.92e-294 |
| chain_4svc | 3.652 | large | 12362.0 | 0.00e+00 |
| chain_5svc | 4.144 | large | 6852.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
