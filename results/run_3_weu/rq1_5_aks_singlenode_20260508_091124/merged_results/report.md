# RQ1.5 AKS fully controlled Experiment Report


## Configuration Used

- **Config snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_091124/merged_results/config.yaml`

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
| image | thesisrq15acr.azurecr.io/thesis-inference@sha256:c69d32c2d6b2a7f666a935dba8fbbdbfb41feb55d1d16919c765fbff6df1eb82 |
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

- **Environment snapshot:** `/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_091124/merged_results/environment.json`

### Runtime

| Setting | Value |
|---|---|
| timestamp | 2026-05-08T09:26:12.331184 |
| platform | Linux-5.15.0-1110-azure-x86_64-with-glibc2.41 |
| processor |  |
| python_version | 3.10.20 |
| torch_version | 2.11.0+cu130 |
| cpu_count | 8 |
| git_commit | unknown |
| rolling_orchestration | {'enabled': True, 'conditions': ['monolithic_k8s_1svc', 'chain_2svc', 'chain_3svc', 'chain_4svc', 'chain_5svc'], 'partial_results_root': '/mnt/c/Users/Nick/Desktop/opus/results_exports/rq1_5_fully_controlled_20260508_091124/partial_results', 'teardown_between_conditions': True} |

### Deployment

| Setting | Value |
|---|---|
| type | kubernetes |
| cluster_type | aks |
| cluster_version | 1.34 |
| node_count | 1 |
| node_instance_type | Standard_D8s_v3 |
| azure_region | westeurope |
| cni | kubenet |
| namespace | rq15 |
| pod_colocation_enforced | true |
| pod_placement.benchmark-client | aks-rq15pool-22994392-vmss000000 |
| pod_placement.monolithic-k8s-1svc-svc-1 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-2svc-svc-1 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-2svc-svc-2 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-3svc-svc-1 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-3svc-svc-2 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-3svc-svc-3 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-4svc-svc-1 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-4svc-svc-2 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-4svc-svc-3 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-4svc-svc-4 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-5svc-svc-1 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-5svc-svc-2 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-5svc-svc-3 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-5svc-svc-4 | aks-rq15pool-22994392-vmss000000 |
| pod_placement.chain-5svc-svc-5 | aks-rq15pool-22994392-vmss000000 |
| container_image_digest | sha256:c69d32c2d6b2a7f666a935dba8fbbdbfb41feb55d1d16919c765fbff6df1eb82 |
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
| monolithic_k8s_1svc | 1000 | 52.045 | 51.827 | 1.772 | 54.766 | [51.935, 52.155] | 0.000 | 0.0% | 52.045 | 0.000 | 0.0% |
| chain_2svc | 1000 | 57.365 | 56.977 | 2.267 | 60.527 | [57.224, 57.505] | 5.319 | 10.2% | 52.045 | 5.319 | 9.3% |
| chain_3svc | 1000 | 60.840 | 60.535 | 2.244 | 64.258 | [60.701, 60.980] | 8.795 | 16.9% | 52.084 | 8.756 | 14.4% |
| chain_4svc | 1000 | 63.808 | 63.583 | 2.200 | 67.649 | [63.672, 63.945] | 11.763 | 22.6% | 53.499 | 10.309 | 16.2% |
| chain_5svc | 1000 | 65.380 | 65.075 | 2.282 | 68.542 | [65.238, 65.521] | 13.334 | 25.6% | 52.597 | 12.782 | 19.6% |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | chain_2svc | 200 | 57.274 | 56.779 | 2.836 | 60.282 |
| 1 | chain_3svc | 200 | 62.408 | 62.201 | 1.682 | 64.736 |
| 1 | chain_4svc | 200 | 62.758 | 62.193 | 2.151 | 66.120 |
| 1 | chain_5svc | 200 | 64.939 | 64.640 | 2.513 | 67.951 |
| 1 | monolithic_k8s_1svc | 200 | 52.075 | 51.733 | 1.580 | 54.505 |
| 2 | chain_2svc | 200 | 56.881 | 56.459 | 2.144 | 60.706 |
| 2 | chain_3svc | 200 | 60.434 | 60.163 | 2.248 | 63.999 |
| 2 | chain_4svc | 200 | 64.165 | 64.039 | 1.932 | 67.718 |
| 2 | chain_5svc | 200 | 65.749 | 65.492 | 2.388 | 68.655 |
| 2 | monolithic_k8s_1svc | 200 | 52.374 | 52.180 | 1.611 | 54.970 |
| 3 | chain_2svc | 200 | 57.861 | 57.526 | 1.821 | 60.507 |
| 3 | chain_3svc | 200 | 60.099 | 59.818 | 1.982 | 63.705 |
| 3 | chain_4svc | 200 | 63.691 | 63.327 | 2.264 | 67.487 |
| 3 | chain_5svc | 200 | 66.061 | 65.801 | 2.050 | 68.766 |
| 3 | monolithic_k8s_1svc | 200 | 50.946 | 50.717 | 1.271 | 53.168 |
| 4 | chain_2svc | 200 | 57.565 | 57.144 | 2.506 | 60.740 |
| 4 | chain_3svc | 200 | 60.720 | 60.527 | 1.999 | 63.408 |
| 4 | chain_4svc | 200 | 63.694 | 63.553 | 1.923 | 66.984 |
| 4 | chain_5svc | 200 | 64.413 | 64.247 | 1.648 | 67.017 |
| 4 | monolithic_k8s_1svc | 200 | 52.135 | 51.870 | 1.988 | 54.625 |
| 5 | chain_2svc | 200 | 57.242 | 56.916 | 1.736 | 60.289 |
| 5 | chain_3svc | 200 | 60.542 | 60.047 | 2.487 | 64.386 |
| 5 | chain_4svc | 200 | 64.733 | 64.333 | 2.235 | 68.326 |
| 5 | chain_5svc | 200 | 65.736 | 65.404 | 2.314 | 69.268 |
| 5 | monolithic_k8s_1svc | 200 | 52.697 | 52.480 | 1.829 | 55.677 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| chain_2svc | 5 | 57.365 | 0.3689 | 0.9806 | 0.0064 |
| chain_3svc | 5 | 60.840 | 0.9049 | 2.3089 | 0.0149 |
| chain_4svc | 5 | 63.808 | 0.7267 | 1.9748 | 0.0114 |
| chain_5svc | 5 | 65.380 | 0.6809 | 1.6472 | 0.0104 |
| monolithic_k8s_1svc | 5 | 52.045 | 0.6615 | 1.7510 | 0.0127 |

## Overhead vs monolithic_k8s_1svc

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary / Non-Compute (ms) |
|---|---|---|---|---|
| chain_2svc | 5.319 | 10.2% | 980.0 | 5.217 |
| chain_3svc | 8.795 | 16.9% | 1568.0 | 7.843 |
| chain_4svc | 11.763 | 22.6% | 1960.0 | 9.937 |
| chain_5svc | 13.334 | 25.6% | 2058.0 | 11.354 |

## RQ1.5 Transfer Validation vs Frozen RQ1.4

- **Frozen RQ1.4 reference:** `/mnt/c/Users/Nick/Desktop/opus/results/frozen/frozen_rq1_4_fully_controlled_20260421_125049/merged_results/condition_summaries.csv`

| Condition | Local K8s Mean (ms) | AKS Mean (ms) | Local Overhead (%) | AKS Overhead (%) | Local Rank | AKS Rank | Rank Match |
|---|---|---|---|---|---|---|---|
| monolithic_k8s_1svc | 81.447 | 52.045 | 0.0% | 0.0% | 1 | 1 | true |
| chain_2svc | 84.189 | 57.365 | 3.4% | 10.2% | 2 | 2 | true |
| chain_3svc | 87.608 | 60.840 | 7.6% | 16.9% | 3 | 3 | true |
| chain_4svc | 92.312 | 63.808 | 13.3% | 22.6% | 4 | 4 | true |
| chain_5svc | 92.624 | 65.380 | 13.7% | 25.6% | 5 | 5 | true |

### AKS Marginal Overhead Progression

| Transition | Increment vs Previous Condition (ms) |
|---|---|
| monolithic_k8s_1svc → chain_2svc | 5.319 |
| chain_2svc → chain_3svc | 3.476 |
| chain_3svc → chain_4svc | 2.968 |
| chain_4svc → chain_5svc | 1.571 |

### Interpretation

- Condition ordering is preserved between frozen RQ1.4 and the AKS run.
- AKS overhead remains monotonic with service count when normalized against the AKS monolithic baseline.
- The bounded-nonlinearity pattern is reproduced on AKS: the final increment (1.571 ms for chain_5svc) is smaller than the preceding increment (2.968 ms).
- AKS relative overhead fractions remain directionally aligned with RQ1.4 but are larger in magnitude, which is consistent with added cloud-platform overhead rather than an architectural reversal.
- Using the frozen RQ1.4 total-compute means rescaled to the AKS monolithic baseline as a heuristic compute reference, the chained AKS conditions retain 5.319–12.782 ms of residual non-compute/platform latency, with the highest residual at chain_5svc.
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
| chain_2svc | 2.614 | large | 17141.0 | 5.13e-306 |
| chain_3svc | 4.349 | large | 4661.0 | 0.00e+00 |
| chain_4svc | 5.888 | large | 2122.0 | 0.00e+00 |
| chain_5svc | 6.526 | large | 1187.0 | 0.00e+00 |

## Carry-Forward Selection

- **Status:** Not applicable
- **Reason:** Carry-forward is only defined for the two-service split-selection experiments (RQ1.1/RQ1.2). RQ1.4 uses a predefined Kubernetes chain configuration set, so no carry-forward decision is applied.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** Not applicable for this experiment; the configuration set is predefined rather than selected by a carry-forward stage.
