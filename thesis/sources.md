# Thesis Source Map

This file tracks the bibliography sources that are currently cited in the thesis `.tex`
files, what each source is used for in the argument, and where it appears.

Scope notes:

- This is a cited-source index, not a full dump of everything present in `references.bib`.
- `Used in` lists the thesis sections that rely on the source. `Intro` means the source is
  used in the introduction outside the numbered RQ sections.
- `Appendix demo` marks template/example citations in `appendix/showcase.tex`; those are not
  part of the thesis argument.

## Core Partitioning And Model-Structure Sources

| Key                         | Source                                                                                                                       | Used in                                  | Purpose in thesis                                                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dnnsplit`                  | DNNSplit: Latency and Cost-Efficient Split Point Identification for Multi-Tier DNN Partitioning                              | Intro, RQ1.1, RQ1.2, RQ1.3, RQ1.4, RQ1.5 | Core reference for treating split selection as a latency/cost optimisation problem rather than an arbitrary architectural choice.                        |
| `deeperthings`              | DeeperThings: Fully Distributed CNN Inference on Resource-Constrained Edge Devices                                           | Intro, RQ1.1, RQ1.2, RQ1.3, RQ1.4, RQ1.5 | Used to support the claim that early feature maps are expensive to transmit and later splits can create compute imbalance.                               |
| `survey_partitioning`       | A Survey on Deep Neural Network Partition over Cloud, Edge and End Devices                                                   | Intro, RQ1.1, RQ1.2, RQ1.3, RQ1.4, RQ1.5 | Broad survey source used to frame partitioning as a joint problem over transfer cost, compute distribution, and deployment constraints.                  |
| `ga_partitioning`           | Partitioning DNNs for Optimizing Distributed Inference Performance on Cooperative Edge Devices: A Genetic Algorithm Approach | Intro, RQ1.1                             | Supports the claim that the best boundary is context-dependent and should be evaluated against latency, bandwidth, and capability constraints.           |
| `fine_grained_partitioning` | Fine-Grained Elastic Partitioning for Distributed DNN Towards Mobile Web AR Services in the 5G Era                           | Intro, RQ1.1, RQ1.2, RQ1.3               | Used to justify finer-grained boundary placement and the idea that communication and computation should be considered jointly.                           |
| `delay_aware_inference`     | Delay-Aware DNN Inference Throughput Maximization in Edge Computing via Jointly Exploring Partitioning and Parallelism       | Intro, RQ1.1                             | Supports the point that latency and throughput are sensitive to where and how the model is partitioned in heterogeneous settings.                        |
| `hierarchical_partitioning` | HiDP: Hierarchical DNN Partitioning for Distributed Inference on Heterogeneous Edge Platforms                                | RQ1.1, RQ1.2, RQ1.4                      | Used to support staged and hierarchical partition refinement rather than one-shot global split selection.                                                |
| `pareto_split`              | Where to Split? A Pareto-Front Analysis of DNN Partitioning for Edge Inference                                               | RQ1.1, RQ1.2, RQ1.3, RQ1.4, RQ1.5        | Supports trade-off reasoning, especially the idea that block-level execution time can vary even when activation sizes are similar.                       |
| `split_object_detectors`    | Split Computing for Complex Object Detectors: Challenges and Preliminary Results                                             | RQ1.1, RQ1.3                             | Used to support the argument that split computing involves a tension between bandwidth cost and computational asymmetry across the boundary.             |
| `neurosurgeon`              | Neurosurgeon: Collaborative Intelligence Between the Cloud and Mobile Edge                                                   | RQ1.2, RQ1.3, RQ1.4, RQ1.5               | Foundational split-computing reference used for layer-level partitioning, sensitivity to intermediate activation size, and communication-cost reasoning. |
| `jointdnn`                  | JointDNN: An Efficient Training and Inference Engine for Intelligent Mobile Cloud Computing Services                         | RQ1.3, RQ1.4, RQ1.5                      | Used to support graph-style split modelling where communication cost depends on intermediate tensor size at each candidate boundary.                     |
| `bottlenet_pp`              | BottleNet++: An End-to-End Approach for Feature Compression in Device-Edge Co-Inference Systems                              | RQ1.3                                    | Supports the claim that early split points create large intermediate representations and can require compression to be viable.                           |
| `dads`                      | Dynamic Adaptive DNN Surgery for Inference Acceleration on the Edge                                                          | RQ1.3, RQ1.4, RQ1.5                      | Used to support the claim that optimal boundaries depend on both compute placement and network context, not just tensor size.                            |
| `bottlefit`                 | BottleFit: Learning Compressed Representations in Deep Neural Networks for Effective and Efficient Split Computing           | RQ1.2, RQ1.3                             | Used to support the point that split position affects processing cost as well as representation size or compression.                                     |
| `edge_intelligence`         | Edge Intelligence: Paving the Last Mile of Artificial Intelligence with Edge Computing                                       | RQ1.3                                    | Provides broader device-edge-cloud context for treating split location as a determinant of both communication overhead and compute allocation.           |
| `resnet`                    | Deep Residual Learning for Image Recognition                                                                                 | RQ1.3                                    | Used to ground the internal timing explanation in the actual stage/block structure of ResNet-18.                                                         |
| `split_computing_survey`    | Split Computing and Early Exiting for Deep Learning Applications: Survey and Research Challenges                             | RQ1.4                                    | Used to frame multi-boundary split design as a joint problem over transfer volume, compute balance, and deployment constraints.                          |

## Deployment, Kubernetes, And Cloud-Overhead Sources

| Key                    | Source                                                                                                                                     | Used in | Purpose in thesis                                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `k8s_genai_inference`  | Evaluating Kubernetes Performance for GenAI Inference                                                                                      | RQ1.4   | Supports the claim that deployment context can add fixed orchestration or coordination cost beyond model computation alone.                  |
| `rpc_overhead_hotos25` | Rethinking RPC Communication for Microservices-based Applications                                                                          | RQ1.5   | Used to explain why RPC calls add layered protocol, parsing, and serialization overhead in distributed services.                             |
| `notnets_apsys24`      | NotNets: Accelerating Microservices by Bypassing the Network                                                                               | RQ1.5   | Supports the claim that network-stack traversal, copies, and communication layers affect microservice latency.                               |
| `managed_k8s_perf`     | A Performance Evaluation of Containers Running on Managed Kubernetes Services                                                              | RQ1.5   | Used to justify that managed Kubernetes platforms can shift absolute performance through provider-specific behavior.                         |
| `virtualization_costs` | Virtualization Costs: Benchmarking Containers and Virtual Machines Against Bare-Metal                                                      | RQ1.5   | Supports the argument that virtualization and containerization can change absolute latency even when the application is unchanged.           |
| `cni_k8s_ic2e21`       | A Comprehensive Performance Evaluation of Different Kubernetes CNI Plugins for Edge-based and Containerized Publish/Subscribe Applications | RQ1.5   | Used to support the point that the networking path and CNI choice can affect measured latency.                                               |
| `noise_in_clouds`      | Noise in the Clouds: Influence of Network Performance Variability on Application Scalability                                               | RQ1.5   | Supports the claim that cloud noise and infrastructure variability can distort absolute measurements.                                        |
| `benchmarking_sc15`    | Scientific Benchmarking of Parallel Computing Systems: Twelve Ways to Tell the Masses When Reporting Performance Results                   | RQ1.5   | Used to justify cautious interpretation of cross-environment transfer: preserve trends and ordering, not exact identical millisecond values. |

## Security, Service-Mesh, And Confidential-Execution Sources

| Key                                    | Source                                                                                               | Used in | Purpose in thesis                                                                                                                                        |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ashraf2025policy_workflow`            | A Policy-Driven Approach for Securing Microservices Workflow in Kubernetes Cluster                   | RQ2.1   | Used to justify evaluating mTLS together with policy-driven authorization rather than encryption alone.                                                  |
| `meshinsight_socc23`                   | Dissecting Overheads of Service Mesh Sidecars                                                        | RQ2.1   | Main service-mesh overhead source for sidecar costs such as IPC, kernel crossings, socket operations, and protocol handling.                             |
| `bremlerbarr2025mtls`                  | Performance Comparison of Service Mesh Frameworks: the MTLS Test Case                                | RQ2.1   | Used to support the claim that mTLS can materially affect latency and resource use, and that cost is workload-specific.                                  |
| `poudel2025mazu`                       | Mazu: A Zero Trust Architecture for Service Mesh Control Planes                                      | RQ2.1   | Used to bound the security claim by noting that the mesh control plane and CA remain trust-critical components.                                          |
| `amd_sevsnp_whitepaper`                | AMD SEV-SNP: Strengthening VM Isolation with Integrity Protection and More                           | RQ2.2   | Primary mechanism and threat-model reference for what SEV-SNP protects and what remains outside the guarantee.                                           |
| `kaplan2023_hardware_vm`               | Hardware VM Isolation in the Cloud: Enabling Confidential Computing with AMD SEV-SNP Technology      | RQ2.2   | Used to explain SEV-SNP and VM-level isolation in broader cloud-computing terms.                                                                         |
| `microsoft_aks_cvm_2025`               | Use Confidential Virtual Machines (CVM) in Azure Kubernetes Service (AKS)                            | RQ2.2   | Product/documentation source used to justify the AKS confidential VM deployment path evaluated in the experiment.                                        |
| `microsoft_aks_confidential_node_pool` | Confidential VM Node Pools Support on AKS with AMD SEV-SNP Confidential VMs                          | RQ2.2   | Used to support the specific claim that AKS confidential node pools can host the selected workload.                                                      |
| `guanciale2022_confidential_quartet`   | SoK: Confidential Quartet -- Comparison of Platforms for Virtualization-Based Confidential Computing | RQ2.2   | Used to support the argument that virtualization-based confidential-computing systems differ in attacker model, attestation, and residual side channels. |
| `misono2024_cvm_explained`             | Confidential VMs Explained: An Empirical Analysis of AMD SEV-SNP and Intel TDX                       | RQ2.2   | Used for both trust-boundary nuance and workload-dependent confidential-VM overhead expectations.                                                        |
| `istio_tls_configuration`              | Understanding TLS Configuration                                                                      | RQ2.2   | Used to explain that mTLS terminates in the proxy and plaintext still exists inside the local pod or VM boundary.                                        |
| `yan2023_cvm_overheads`                | Performance Overheads of Confidential Virtual Machines                                               | RQ2.2   | Main workload-dependent overhead source for confidential VMs.                                                                                            |
| `akram2021_hpc_tees`                   | Performance Analysis of Scientific Computing Workloads on General Purpose TEEs                       | RQ2.2   | Used to support the general point that TEE overhead depends on workload characteristics such as memory, I/O, and system-call behavior.                   |
| `mo2024_ml_confidential_computing`     | Machine Learning with Confidential Computing: A Systematization of Knowledge                         | RQ2.2   | Used to frame why ML systems adopt confidential computing and why practical systems must balance protection with performance and complexity.             |

## Template Or Demo Citations

| Key         | Source                                        | Used in       | Purpose in thesis                                                                                                 |
| ----------- | --------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ISO25010`  | ISO/IEC 25010:2011 quality model              | Appendix demo | Template citation example in `appendix/showcase.tex`, not part of the thesis argument.                            |
| `Beck2000a` | Extreme Programming Explained: Embrace Change | Appendix demo | Template `textcite` example in `appendix/showcase.tex`, not part of the thesis argument.                          |
| `Beck2000b` | Test Driven Development: By Example           | Appendix demo | Template `citeauthor` / `citetitle` / `cite` example in `appendix/showcase.tex`, not part of the thesis argument. |

## Quick RQ-To-Source Summary

| Thesis section | Main source role                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `RQ1.1`        | Coarse split-point screening, transfer-vs-compute trade-off, and context-dependent boundary choice.                      |
| `RQ1.2`        | Fine-grained refinement inside the carried-forward region and block-level performance differences.                       |
| `RQ1.3`        | Explanatory synthesis using activation-transfer burden, compute distribution, and ResNet-18 structure.                   |
| `RQ1.4`        | Cost of adding more boundaries in an in-cluster Kubernetes chain.                                                        |
| `RQ1.5`        | Transfer validation from local Kubernetes to AKS under managed-cloud overhead and noise.                                 |
| `RQ2.1`        | Service identity, mTLS, authorization policy, and sidecar overhead in AKS.                                               |
| `RQ2.2`        | Confidential VM / SEV-SNP execution, AKS confidential nodes, trust-boundary limits, and workload-dependent TEE overhead. |

## Maintenance Notes

- `references.bib` currently contains duplicate entries for several RQ1-era keys. This
  file intentionally lists the cited sources once per key.
- `meshinsight_socc23` and `zhu2023_meshinsight` refer to the same SoCC 2023 paper in
  the bibliography. The current thesis text uses `meshinsight_socc23`.
- If a source is added to a literature-context section later, update both the relevant
  table row and the `Used in` column here.
