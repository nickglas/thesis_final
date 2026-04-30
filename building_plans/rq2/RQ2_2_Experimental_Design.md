# RQ2.2 Experimental Design

## AMD SEV-SNP VM-Level Confidential Execution for the Protected Downstream Inference Service

---

## Design Recommendation

**Decision: RQ2.2 should evaluate VM-level confidential execution as an incremental extension of the completed RQ2.1 secure AKS path, not as a new architecture study.**

**Primary configuration: `chain_2svc`.**

**Security baseline carried forward: the final RQ2.1 `chain_2svc_mtls` contract: managed Istio / Azure Service Mesh mTLS, service identity, and AuthorizationPolicy for the downstream service.**

**TEE mechanism recommendation: Azure Confidential VM / AKS confidential node execution using AMD SEV-SNP. This is a VM-level TEE, not Intel SGX and not an application-level enclave design.**

**Initial protected workload: service2 only.**

**Do not use the old RQ2.1 `Standard_D8s_v3` result as the primary RQ2.2 baseline. RQ2.2 requires a new paired comparison.**

**`chain_5svc` is not part of the initial RQ2.2 experiment. It can only be considered later as optional stress evidence after `chain_2svc` is stable.**

### Why this is the right RQ2.2 shape

RQ2.2 should answer a narrow question: what additional cost is paid when the selected protected downstream inference service is moved into a VM-level confidential execution environment while preserving the communication-level protections introduced in RQ2.1?

It should not reopen:

- split-point selection
- chain-topology selection
- service-mesh mechanism choice
- mixed-ownership orchestration design
- application-level trusted-code partitioning
- Intel SGX packaging, EPC memory management, or SGX attestation plumbing

The strongest thesis story is:

1. RQ1 selected and transferred the deployment path.
2. RQ2.1 hardened that path with service identity, mTLS, and AuthorizationPolicy.
3. RQ2.2 adds VM-level confidential execution to the already protected downstream service and measures the incremental cost.

That means the primary RQ2.2 comparison is not plain AKS versus secure AKS, and not old RQ2.1 standard-node results versus new confidential-node results. It is a new paired comparison between the same secure `chain_2svc_mtls` deployment with service2 on a standard node and with service2 on an AMD SEV-SNP confidential node.

---

## 1. Working RQ2.2 Framing

> **RQ2.2:** What additional performance and operational overhead is introduced when the protected downstream inference service is moved into an AMD SEV-SNP VM-level confidential execution environment while preserving the mTLS, service identity, and AuthorizationPolicy protections from RQ2.1?

### Thesis-facing interpretation

RQ2.1 measured communication-level hardening: service identity, managed-Istio mTLS, and AuthorizationPolicy for microservice-based ResNet-18 inference on AKS.

RQ2.2 measures VM-level confidential execution as an additional protection layer on top of that completed RQ2.1 contract.

RQ2.2 is therefore an incremental confidential-execution overhead study. It does not repeat the RQ2.1 plain-versus-mTLS comparison, and it does not treat the old RQ2.1 `Standard_D8s_v3` run as the primary standard baseline.

### Protected service selection

The initial protected workload is `service2` in `chain_2svc_mtls`.

This is the natural RQ2.2 target because RQ2.1 already treats service2 as the downstream protected hop: service2 receives intermediate activations from service1, executes the later ResNet-18 segment after the split after `layer2`, and is protected by workload-scoped STRICT mTLS plus AuthorizationPolicy that allows only the service1 principal.

### What RQ2.2 should explicitly measure

1. Additional end-to-end latency when service2 runs on an AMD SEV-SNP confidential node.
2. Additional tail-latency effects.
3. Additional startup, scheduling, and readiness cost.
4. Resource effects for service2, service1, and their sidecars.
5. Whether the RQ2.1 secure chain remains deployable and measurable when the protected downstream service is placed in a VM-level confidential execution environment.

### What RQ2.2 should not become

RQ2.2 is not:

- a new service-mesh study
- a new partition-selection study
- a mixed-cloud or cross-cluster deployment study
- an Intel SGX or Gramine exercise
- an application-level trusted-code isolation study
- a comparison of all Azure confidential-computing products
- a `chain_5svc` first-pass experiment

---

## 2. Platform Recommendation

### Recommended primary platform

**Use AKS confidential VM node pools backed by AMD SEV-SNP as the primary RQ2.2 mechanism.**

This is the best thesis-facing choice because it:

1. keeps RQ2.2 inside the AKS deployment path already established in RQ1.5 and RQ2.1
2. supports heterogeneous node pools, allowing service1 and service2 to run on different execution environments inside one cluster
3. provides VM-level confidential computing without requiring Python, PyTorch, gRPC, or model-code rewrites
4. preserves the RQ2.1 service-mesh and AuthorizationPolicy model
5. gives a reproducible implementation path through Kubernetes placement, Azure node-pool metadata, and runtime validation

### Recommended VM family and sizes

Primary target:

- standard baseline service2 node: `Standard_D8as_v5`, if available
- confidential service2 node: `Standard_DC8as_v5`

Reason:

`Standard_D8as_v5` and `Standard_DC8as_v5` are much closer in generation, processor family, vCPU count, and memory shape than the old RQ2.1 `Standard_D8s_v3` baseline versus a new `Standard_DC8as_v5` confidential node. This makes the RQ2.2 comparison more defensible.

Recommended confidential family:

- family: `DC`
- series: `DCasv5`
- preferred size: `Standard_DC8as_v5`
- quota-limited fallbacks:
  - `Standard_DC4as_v5`
  - `Standard_DC2as_v5`

Preferred standard baseline family:

- series: `Dasv5`
- preferred size: `Standard_D8as_v5`

Fallback standard baseline:

- `Standard_D8s_v3`, only if `Standard_D8as_v5` is unavailable or quota-blocked

If the fallback baseline is used, the thesis must explicitly frame the result as the overhead of moving to the selected confidential Azure deployment path, not as a hardware-identical measurement of pure SEV-SNP overhead.

### Azure series to avoid for this RQ2.2 plan

Avoid:

- `DCsv2` / `DCsv3` as the AMD SEV-SNP path, because those are associated with Intel SGX-style confidential-computing nodes and imply a different threat model and implementation path
- `DCesv6` / `DCedsv6` unless the project intentionally switches to Intel TDX
- any wording that describes AMD SEV-SNP Confidential VMs as application-level enclaves

### Why not AKS Confidential Containers preview

Do not use AKS Confidential Containers as the primary RQ2.2 path.

This RQ2.2 plan needs a stable thesis anchor. Confidential VM node pools are the cleaner fit because they preserve the existing container, service mesh, and AKS workflow while changing the node execution environment.

### Why not Intel SGX-first

Intel SGX would push RQ2.2 toward application-level trusted-code packaging, EPC memory constraints, SGX-specific attestation, and possible application rewrites. That is a legitimate future extension, but it is not the lowest-risk way to answer the current thesis question.

### RQ2.2 platform decision

**Primary mechanism:** AMD SEV-SNP Azure Confidential VM / AKS confidential node.

**Primary series:** `DCasv5`.

**Primary confidential size:** `Standard_DC8as_v5`.

**Preferred standard comparator:** `Standard_D8as_v5`.

**Not primary:** AKS Confidential Containers preview.

**Not primary:** Intel SGX / DCsv2 / DCsv3.

---

## 3. Baseline and Condition Set

### Baseline principle

RQ2.2 must isolate confidential-execution overhead from:

1. the RQ2.1 service-mesh overhead already measured
2. VM generation and CPU-family differences
3. temporal cloud noise

Therefore RQ2.2 needs a new paired comparison. The old RQ2.1 `Standard_D8s_v3` artifacts may be used as context, but not as the primary baseline.

### Primary condition pair

| Condition | Meaning | Status |
| --- | --- | --- |
| `chain_2svc_mtls_standard` | `chain_2svc` with RQ2.1 mTLS/service identity/Authz active; client outside mesh; service1 on standard node; service2 on standard node | Required |
| `chain_2svc_mtls_confidential_service2` | Same secure deployment and benchmark protocol, but service2 runs on an AMD SEV-SNP confidential node | Required |

### Condition A: `chain_2svc_mtls_standard`

- benchmark client remains outside the mesh
- service namespace remains meshed
- service1 runs on a standard Azure/AKS node
- service2 runs on a standard Azure/AKS node
- service1 to service2 remains protected by mTLS
- service2 AuthorizationPolicy allows only the service1 principal
- preferred service2 node SKU: `Standard_D8as_v5`
- fallback service2 node SKU: `Standard_D8s_v3`, only if `Standard_D8as_v5` is unavailable or quota-blocked

### Condition B: `chain_2svc_mtls_confidential_service2`

- benchmark client remains outside the mesh
- service namespace remains meshed
- service1 runs on a standard Azure/AKS node
- service2 runs on an AMD SEV-SNP confidential node
- service1 to service2 uses the same mTLS policy as condition A
- service2 uses the same AuthorizationPolicy as condition A
- service2 placement on confidential hardware must be validated before benchmarking
- preferred service2 node SKU: `Standard_DC8as_v5`
- quota-limited service2 fallbacks: `Standard_DC4as_v5`, then `Standard_DC2as_v5`

### Why this pair is correct

This pair keeps the comparison narrow:

- same ResNet-18 model
- same split after `layer2`
- same service1 to service2 topology
- same mTLS and service identity policy
- same service2 AuthorizationPolicy
- same service image digest where possible
- same benchmark client process and benchmark protocol
- new paired standard baseline collected close in time to the confidential condition

The intended changed variable is:

- service2 execution environment: standard node versus AMD SEV-SNP confidential node

### Optional stress evidence

`chain_5svc` should not be included in the initial RQ2.2 experiment. It can be treated only as later optional stress evidence after the `chain_2svc` service2-only path is stable and the thesis has enough time and quota.

---

## 4. Controlled Variables

The following should remain identical, or as close as Azure availability permits:

- ResNet-18 model
- split after `layer2`
- `chain_2svc` service1 to service2 topology
- image digest, if possible
- benchmark protocol
- warmup iterations
- measured iterations
- paired-pass count
- random seed and alternating/interleaved order
- mTLS policy
- service accounts and service identity assumptions
- AuthorizationPolicy for service2
- resource requests and limits where possible
- security validation logic
- activation-transfer size
- result aggregation and reporting format

The intended changed variable is:

- service2 execution environment: standard Azure/AKS node versus AMD SEV-SNP confidential Azure/AKS node

If the standard and confidential VM sizes cannot be closely matched, the mismatch must be recorded as an experimental limitation and reflected in the wording of the result.

---

## 5. Deployment Contract

### Core idea

RQ2.2 should move from the RQ2.1 same-node benchmark contract to a service2-aware placement contract.

The benchmark should keep service1 in the standard execution environment and move only service2 between a standard node and a confidential node.

### Critical comparison rule

The standard and confidential conditions must have matched topology.

That means:

- client placement stays the same across the pair
- service1 placement stays standard across the pair
- service count stays at two
- service-to-service topology stays the same
- service2 is the only intended placement difference
- the standard condition should be rerun as part of RQ2.2, not imported from old RQ2.1 artifacts

### Recommended infrastructure contract

Use one AKS cluster with heterogeneous pools:

- `systempool`: standard small system pool for AKS system workloads
- `clientpool`: standard pool for the non-meshed benchmark client, if separated from service1
- `service1pool`: standard pool for service1, or the same standard pool as the benchmark client if the design intentionally chooses that simplification
- `service2-standard-pool`: standard pool for service2 in `chain_2svc_mtls_standard`
- `service2-confidential-pool`: AMD SEV-SNP confidential pool for service2 in `chain_2svc_mtls_confidential_service2`

### Placement contract

- benchmark client pod remains outside mesh injection
- service1 pod remains on a standard node in both conditions
- service2 pod runs on a standard node in condition A
- service2 pod runs on an AMD SEV-SNP confidential node in condition B
- service2 placement must be validated from pod placement, node labels, node pool, VM SKU, and node image metadata
- service1 must not accidentally run on the confidential node unless the experiment is explicitly changed
- if service1 and service2 are on different nodes, the cross-node path must be matched in the standard baseline and reported as part of the deployment contract

This is a deliberate break from the RQ2.1 same-node client-plus-service contract. The break is necessary because service2-only confidential placement changes the service-hosting node trust model.

---

## 6. Benchmark Design

Use a paired/interleaved design like RQ2.1:

- 5 paired passes if feasible
- 200 measured iterations per condition per pass
- 1000 measured iterations per condition in the full run
- same warmup settings as RQ2.1 unless a smoke test explicitly uses fewer iterations
- alternating or seeded interleaved condition order
- same pinned image digest where possible
- same RQ2.1 mTLS/Authz security validation before benchmarking
- merged artifacts and summaries exported for the pair

Do not compare against old RQ2.1 artifacts as the primary baseline.

The old RQ2.1 result remains useful context for the thesis narrative: it shows the cost of adding communication-level hardening. RQ2.2 should report its primary overhead relative to the new RQ2.2 `chain_2svc_mtls_standard` baseline.

---

## 7. Azure Infrastructure Plan

### Required Azure checks

Before implementing the benchmark pipeline, verify:

1. regional availability for `Standard_DC8as_v5`
2. quota for `Standard_DC8as_v5`
3. regional availability for `Standard_D8as_v5`
4. quota for `Standard_D8as_v5`
5. fallback availability for `Standard_DC4as_v5` and `Standard_DC2as_v5`
6. whether the target AKS version and OS image support the desired confidential node-pool configuration
7. whether the Terraform AzureRM provider version in use supports the required node-pool fields, or whether a controlled Azure CLI step is needed

### AKS node-pool requirements

The implementation plan should add:

- a standard service1 node placement target
- a standard service2 baseline node placement target
- an AMD SEV-SNP confidential service2 node placement target
- node labels that distinguish standard and confidential service2 pools
- node selectors and tolerations for service1 and service2
- validation that service2 lands on the intended node pool in each condition
- validation that service1 remains on a standard node
- validation that the benchmark client remains outside mesh injection

### Metadata to record

Each RQ2.2 run should record:

- Azure region
- cluster name and resource group
- node pool names
- node SKU for service1 and service2
- node image version
- whether the service2 node pool is confidential
- confidential-computing capability evidence available from Azure and Kubernetes metadata
- Azure resource IDs if available
- service1 pod node
- service2 pod node
- benchmark client pod node
- image digest
- mesh revision
- PeerAuthentication and AuthorizationPolicy resources
- attestation artifact path or explicit note that attestation was not collected

### Expected verification commands

Examples of checks to preserve in the implementation notes or preflight artifacts:

```powershell
az vm list-skus -l <region> --size Standard_DC8as_v5 -o table
az vm list-skus -l <region> --size Standard_D8as_v5 -o table
az vm list-usage -l <region> -o table
az aks nodepool show -g <resource-group> --cluster-name <cluster> -n <pool> --query "{name:name,vmSize:vmSize,nodeImageVersion:nodeImageVersion,osSKU:osSKU,mode:mode}"
kubectl get nodes -L agentpool,node.kubernetes.io/instance-type,kubernetes.azure.com/mode
kubectl get pod -n <service-namespace> -o wide -l condition=chain_2svc_mtls_confidential_service2,segment-index=2
kubectl get pod -n <service-namespace> -o wide -l condition=chain_2svc_mtls_confidential_service2,segment-index=1
kubectl get namespace <service-namespace> --show-labels
kubectl get peerauthentication,authorizationpolicy -n <service-namespace> -o yaml
az aks show -g <resource-group> -n <cluster> --query serviceMeshProfile
```

---

## 8. Metrics

### Latency

RQ2.2 should report:

- mean end-to-end latency
- median end-to-end latency
- p95 latency
- p99 latency
- paired pass deltas
- service1 forward time
- service2 compute time
- inferred non-compute/platform overhead if available

### Security

RQ2.2 should report:

- mTLS validation
- AuthorizationPolicy validation
- full-chain positive probe through service1
- direct-denial probe against protected service2 from a non-meshed pod
- service2 confidential node/VM validation

### Resource and operation

RQ2.2 should report:

- service2 CPU and memory
- service1 CPU and memory
- sidecar CPU and memory
- total pod CPU and memory
- startup/readiness time
- scheduling delay
- failed scheduling events
- node SKU and confidential metadata
- additional Kubernetes and Azure resources
- cost/runtime notes if available

### Validity checks

RQ2.2 should report:

- activation bytes identical across conditions
- same split topology
- same image digest, or a documented image difference
- service2 placement validated
- service1 placement validated
- benchmark client outside mesh
- mTLS and AuthorizationPolicy still active
- confidential hardware capability verified

---

## 9. Threat Model and Limitations

AMD SEV-SNP Confidential VM support is a VM-level TEE / confidential-computing environment. It is not Intel SGX and should not be described as application-level enclave execution.

The guest OS, Python runtime, PyTorch process, Istio sidecar, and service code remain inside the confidential VM trust boundary. RQ2.2 does not isolate one Python function, one model layer, or one model segment from the guest OS.

The valid security claim is narrower:

- RQ2.2 evaluates the overhead of placing the protected downstream service in an AMD SEV-SNP VM-level confidential execution environment.
- This adds protection against host or hypervisor-level access according to Azure's confidential VM threat model.
- RQ2.1 communication protections remain active: mTLS, service identity, and AuthorizationPolicy.

The invalid security claims are:

- RQ2.2 does not prove application-level isolation within service2.
- RQ2.2 does not protect against bugs in the Python service, PyTorch runtime, application logic, or guest OS.
- RQ2.2 does not protect against malicious code already running inside the guest.
- RQ2.2 does not protect against compromised credentials inside the VM.
- RQ2.2 does not eliminate all side channels.
- RQ2.2 is not generalizable to Intel SGX or Intel TDX without a separate experiment.

### Istio sidecar and plaintext handling

Istio sidecar placement affects where plaintext exists.

If the service2 sidecar runs on the same confidential node and pod environment as service2, the sidecar and service process are inside the confidential VM boundary. Nevertheless, plaintext exists inside the guest runtime after TLS termination.

If the sidecar cannot run on the confidential node, the RQ2.2 design must be revisited because the RQ2.1 security contract would no longer be preserved in the intended form.

### Hardware matching limitation

The preferred comparison is:

- standard service2: `Standard_D8as_v5`
- confidential service2: `Standard_DC8as_v5`

If `Standard_D8as_v5` is unavailable and `Standard_D8s_v3` is used as the standard baseline, the comparison is not hardware-identical. In that case, the result must be framed as:

> overhead of moving the protected downstream service to the selected confidential Azure deployment path

not as:

> pure SEV-SNP overhead under matched hardware

### Placement limitation

Single-node versus cross-node placement can affect latency. If service1 and service2 are on different nodes, the standard and confidential conditions must use matched cross-node topology where possible, and the network-path change must be reported.

---

## 10. Staged Implementation Plan

### Stage 0: Azure feasibility

Objective: prove that the target Azure platform is available before changing code.

Tasks:

1. Verify `DCasv5` availability in the target region.
2. Verify `Standard_DC8as_v5` quota.
3. Verify `Standard_D8as_v5` quota.
4. Identify fallback SKUs: `Standard_DC4as_v5`, `Standard_DC2as_v5`, and `Standard_D8s_v3`.
5. Check whether AKS confidential node pools support the required cluster, OS image, and node-pool configuration.
6. Decide whether Terraform alone is sufficient or whether an Azure CLI node-pool step is required.

Exit criteria:

- target confidential and standard SKUs are confirmed, or fallback strategy is selected
- no blocking AKS confidential node-pool limitation is discovered
- the selected SKU pair is recorded before implementation begins

### Stage 1: Manifest and provisioning design

Objective: design the placement/provisioning model without running the full benchmark.

Tasks:

1. Add planned config fields for service2 confidential placement.
2. Add Terraform/node-pool plan for standard service1, standard service2 baseline, and confidential service2 placement.
3. Add manifest-generation plan for `chain_2svc_mtls_standard`.
4. Add manifest-generation plan for `chain_2svc_mtls_confidential_service2`.
5. Run generate-only validation once implementation begins.

Exit criteria:

- generated manifests can express service1 standard placement and service2 standard/confidential placement
- no ad hoc manifest editing is required

### Stage 2: Smoke deployment

Objective: prove the secure chain works with service2 on a confidential node.

Tasks:

1. Deploy `chain_2svc_mtls_confidential_service2`.
2. Validate service2 placement on the confidential node.
3. Validate service1 placement on a standard node.
4. Validate benchmark client remains outside mesh injection.
5. Validate mTLS and AuthorizationPolicy.
6. Validate direct-denial probe against protected service2.
7. Run a small smoke benchmark.
8. Preserve artifacts for inspection.

Exit criteria:

- service2 placement is validated on AMD SEV-SNP confidential infrastructure
- service1 placement is validated on standard infrastructure
- RQ2.1 mTLS/Authz behavior still passes
- a small smoke benchmark completes

### Stage 3: Paired RQ2.2 benchmark

Objective: run the thesis-facing RQ2.2 pair.

Tasks:

1. Run `chain_2svc_mtls_standard` versus `chain_2svc_mtls_confidential_service2`.
2. Use 5 paired passes if feasible.
3. Use the same measured-iteration protocol as RQ2.1.
4. Collect latency, resource, readiness, security, placement, and confidential-node metadata.
5. Export merged results and summaries.

Exit criteria:

- one complete paired `chain_2svc` RQ2.2 run succeeds
- merged artifacts contain enough metadata to defend the placement and platform claims

### Stage 4: Thesis interpretation

Objective: write the result without overstating the security claim.

Tasks:

1. Report incremental confidential-execution overhead.
2. Compare only against the newly paired RQ2.2 standard baseline.
3. Treat old RQ2.1 results as context, not the primary baseline.
4. Explain whether the preferred `D8as_v5` versus `DC8as_v5` comparison was achieved.
5. If a fallback baseline was used, state the hardware-matching limitation directly.
6. Discuss sidecar/plaintext and VM-level TEE limitations carefully.

Exit criteria:

- thesis wording distinguishes RQ2.1 communication-level hardening from RQ2.2 VM-level confidential execution
- the result does not claim AMD SEV-SNP application-level isolation

---

## 11. Risks and Mitigations

### Risk 1: Confidential SKU quota or regional availability mismatch

**Mitigation:** Treat Stage 0 Azure feasibility as a formal gate before implementation work.

### Risk 2: Standard comparator SKU unavailable

**Mitigation:** Prefer `Standard_D8as_v5`; fall back to `Standard_D8s_v3` only with explicit limitation wording.

### Risk 3: Confounding confidential execution with VM generation or CPU differences

**Mitigation:** Use the closest available standard/non-confidential comparator and record exact VM SKUs, node images, and region.

### Risk 4: Confounding confidential execution with network topology

**Mitigation:** Match service1/service2 placement topology across the standard and confidential conditions. If cross-node placement is used, use it in both conditions and report it.

### Risk 5: Mesh sidecar behavior differs on confidential nodes

**Mitigation:** Treat sidecar readiness and mTLS/Authz validation as required preflight gates.

### Risk 6: RQ2.2 grows into a broader confidential-computing comparison

**Mitigation:** Keep the initial experiment service2-only, `chain_2svc`-only, and AMD SEV-SNP-only.

### Risk 7: Intro and abstract wording lag behind the implemented RQ2 structure

**Mitigation:** Once RQ2.2 is accepted, update thesis framing so RQ2.1 is described as communication-level hardening and RQ2.2 as VM-level confidential execution.

---

## 12. Final Recommendation

The next step should be a narrow, platform-first RQ2.2:

- keep `chain_2svc` as the only initial topology
- keep the RQ2.1 secure mesh contract
- protect service2 first, not the full chain
- use AMD SEV-SNP Azure Confidential VM / AKS confidential node execution
- prefer `Standard_D8as_v5` versus `Standard_DC8as_v5`
- fall back to `Standard_D8s_v3` versus `Standard_DC8as_v5` only with explicit limitation wording
- compare only against a newly collected RQ2.2 standard baseline
- treat old RQ2.1 results as context
- defer `chain_5svc` until the primary service2-only path is stable

This plan is academically cautious, implementation-ready, and aligned with the thesis claim: RQ2.2 evaluates the additional overhead of placing the protected downstream inference service in a VM-level confidential execution environment using AMD SEV-SNP while preserving the communication-level protections introduced in RQ2.1.
