# RQ2.2 Experimental Design

## AMD SEV-SNP VM-Level Confidential Execution for the Protected Downstream Inference Service

---

## Design Recommendation

**Decision:** RQ2.2 evaluates VM-level confidential execution as an incremental extension of the completed RQ2.1 secure AKS path.

**Primary configuration:** `chain_2svc`.

**Security baseline carried forward:** the final RQ2.1 `chain_2svc_mtls` contract: managed Istio / Azure Service Mesh mTLS, service identity, and AuthorizationPolicy for the downstream service.

**Confidential execution mechanism:** Azure Confidential VM / AKS confidential node execution using AMD SEV-SNP.

**Only approved region:** West Europe.

**Only approved standard comparator:** `Standard_D8as_v5`.

**Only approved confidential service2 node:** `Standard_DC8as_v5`.

**Initial protected workload:** service2 only.

**The approved AMD SEV-SNP path is the only RQ2.2 plan.** If it cannot be used, RQ2.2 stops at feasibility/provisioning evidence and the thesis reports the platform limitation rather than switching to a different confidential-computing path or VM shape.

---

## 1. Working RQ2.2 Framing

> **RQ2.2:** What additional performance and operational overhead is introduced when the protected downstream inference service is moved into an AMD SEV-SNP VM-level confidential execution environment while preserving the mTLS, service identity, and AuthorizationPolicy protections from RQ2.1?

### Thesis-Facing Interpretation

RQ2.1 measured communication-level hardening: service identity, managed-Istio mTLS, and AuthorizationPolicy for microservice-based ResNet-18 inference on AKS.

RQ2.2 measures VM-level confidential execution as an additional protection layer on top of that completed RQ2.1 contract.

RQ2.2 is therefore an incremental confidential-execution overhead study. It does not repeat the RQ2.1 plain-versus-mTLS comparison, and it does not use old RQ2.1 benchmark artifacts as the primary standard baseline. The standard baseline must be newly collected as part of the RQ2.2 pair.

### Protected Service Selection

The protected workload is `service2` in `chain_2svc_mtls`.

This is the natural RQ2.2 target because RQ2.1 already treats service2 as the downstream protected hop: service2 receives intermediate activations from service1, executes the later ResNet-18 segment after the split after `layer2`, and is protected by workload-scoped STRICT mTLS plus AuthorizationPolicy that allows only the service1 principal.

### What RQ2.2 Measures

1. Additional end-to-end latency when service2 runs on an AMD SEV-SNP confidential node.
2. Additional tail-latency effects.
3. Additional startup, scheduling, and readiness cost.
4. Resource effects for service2, service1, and their sidecars.
5. Whether the RQ2.1 secure chain remains deployable and measurable when the protected downstream service is placed in a VM-level confidential execution environment.

### Scope Boundaries

RQ2.2 is not:

- a new service-mesh study
- a new partition-selection study
- a mixed-cloud or cross-cluster deployment study
- an application-level trusted-code isolation study
- a comparison of Azure confidential-computing products
- a `chain_5svc` first-pass experiment

---

## 2. Platform and Quota Contract

### Required Azure Platform

RQ2.2 uses one AKS cluster in **West Europe** with heterogeneous node pools.

The only valid VM pair for the thesis-facing run is:

| Role | Azure SKU | Azure quota family | Azure series | vCPUs |
| --- | --- | --- | --- | ---: |
| Standard service1 and standard service2 baseline | `Standard_D8as_v5` | `Standard DASv5 Family vCPUs` | `Dasv5` | 8 |
| Confidential service2 | `Standard_DC8as_v5` | `Standard DCASv5 Family vCPUs` | `DCasv5` | 8 |

### Confirmed Quota Requests

The accepted quota envelope for the full RQ2.2 experiment is:

```text
Region: West Europe
Quota: Standard DCASv5 Family vCPUs
Requested new limit: 16
Reason: AKS confidential VM node pool for thesis benchmarking using Standard_DC8as_v5 / AMD SEV-SNP.
```

```text
Region: West Europe
Quota: Standard DASv5 Family vCPUs
Requested new limit: 16
Reason: matched non-confidential baseline using Standard_D8as_v5.
```

### Quota Interpretation

The `DASv5` quota supports the standard RQ2.2 baseline with:

- service1 on `Standard_D8as_v5`
- service2 on `Standard_D8as_v5`

The `DCASv5` quota supports the confidential RQ2.2 condition with:

- service2 on `Standard_DC8as_v5`

The runner should use a rolling service2 strategy when needed so the standard service2 pool and confidential service2 pool do not need to coexist. The planned thesis-facing pair remains the same either way: `Standard_D8as_v5` versus `Standard_DC8as_v5`.

### Hard Gate

The benchmark runner and preflight must fail closed if the selected standard/confidential pair is not:

- region: `westeurope`
- standard size: `Standard_D8as_v5`
- confidential size: `Standard_DC8as_v5`
- confidential backend: AMD SEV-SNP
- standard quota family: `Standard DASv5 Family vCPUs`
- confidential quota family: `Standard DCASv5 Family vCPUs`

Only this approved AMD SEV-SNP SKU pair and newly collected RQ2.2 baseline are valid for the primary RQ2.2 result.

---

## 3. Baseline and Condition Set

### Baseline Principle

RQ2.2 must isolate confidential-execution overhead from:

1. the RQ2.1 service-mesh overhead already measured
2. VM generation and CPU-family differences
3. temporal cloud noise

Therefore RQ2.2 needs a new paired comparison collected close in time.

### Primary Condition Pair

| Condition | Meaning | Status |
| --- | --- | --- |
| `chain_2svc_mtls_standard` | `chain_2svc` with RQ2.1 mTLS/service identity/Authz active; client outside mesh; service1 on `Standard_D8as_v5`; service2 on `Standard_D8as_v5` | Required |
| `chain_2svc_mtls_confidential_service2` | Same secure deployment and benchmark protocol; service1 on `Standard_D8as_v5`; service2 on `Standard_DC8as_v5` AMD SEV-SNP confidential infrastructure | Required |

### Condition A: `chain_2svc_mtls_standard`

- benchmark client remains outside the mesh
- service namespace remains meshed
- service1 runs on `Standard_D8as_v5`
- service2 runs on `Standard_D8as_v5`
- service1 to service2 remains protected by mTLS
- service2 AuthorizationPolicy allows only the service1 principal

### Condition B: `chain_2svc_mtls_confidential_service2`

- benchmark client remains outside the mesh
- service namespace remains meshed
- service1 runs on `Standard_D8as_v5`
- service2 runs on `Standard_DC8as_v5`
- service1 to service2 uses the same mTLS policy as condition A
- service2 uses the same AuthorizationPolicy as condition A
- service2 placement on confidential AMD SEV-SNP infrastructure must be validated before benchmarking

### Intended Changed Variable

The intended changed variable is:

- service2 execution environment: standard Azure/AKS node versus AMD SEV-SNP confidential Azure/AKS node

Everything else should remain identical or be recorded as a validity limitation.

---

## 4. Controlled Variables

The following should remain identical across the paired conditions:

- ResNet-18 model
- split after `layer2`
- `chain_2svc` service1 to service2 topology
- image digest
- benchmark protocol
- warmup iterations
- measured iterations
- paired-pass count
- random seed and alternating/interleaved order
- mTLS policy
- service accounts and service identity assumptions
- AuthorizationPolicy for service2
- resource requests and limits
- security validation logic
- activation-transfer size
- result aggregation and reporting format

If any value differs, the artifact must record the difference explicitly.

---

## 5. Deployment Contract

### Core Idea

RQ2.2 moves from the RQ2.1 same-node benchmark contract to a service2-aware placement contract.

The benchmark keeps service1 in the standard execution environment and moves only service2 between a standard node and a confidential node.

### Critical Comparison Rule

The standard and confidential conditions must have matched topology.

That means:

- client placement stays the same across the pair
- service1 placement stays standard across the pair
- service count stays at two
- service-to-service topology stays the same
- service2 is the only intended placement difference
- the standard condition is rerun as part of RQ2.2

### Infrastructure Contract

Use one AKS cluster with heterogeneous pools:

- `systempool`: standard small system pool for AKS system workloads
- `service1-standard-pool`: standard pool for service1
- `service2-standard-pool`: standard pool for service2 in `chain_2svc_mtls_standard`
- `service2-confidential-pool`: AMD SEV-SNP confidential pool for service2 in `chain_2svc_mtls_confidential_service2`

The benchmark client may share a standard pool if the runner records and validates that placement consistently across conditions.

### Placement Contract

- benchmark client pod remains outside mesh injection
- service1 pod remains on `Standard_D8as_v5` infrastructure in both conditions
- service2 pod runs on `Standard_D8as_v5` in condition A
- service2 pod runs on `Standard_DC8as_v5` in condition B
- service2 placement must be validated from pod placement, node labels, node pool, VM SKU, and node image metadata
- service1 must not accidentally run on the confidential node
- if service1 and service2 are on different nodes, the cross-node path must be matched in the standard baseline and reported as part of the deployment contract

---

## 6. Benchmark Design

Use a paired/interleaved design like RQ2.1:

- 5 paired passes if feasible
- 200 measured iterations per condition per pass
- 1000 measured iterations per condition in the full run
- same warmup settings as RQ2.1 unless a smoke test explicitly uses fewer iterations
- alternating or seeded interleaved condition order
- same pinned image digest
- same RQ2.1 mTLS/Authz security validation before benchmarking
- merged artifacts and summaries exported for the pair

Do not compare against old RQ2.1 artifacts as the primary baseline.

The old RQ2.1 result remains useful context for the thesis narrative: it shows the cost of adding communication-level hardening. RQ2.2 reports its primary overhead relative to the new RQ2.2 `chain_2svc_mtls_standard` baseline.

---

## 7. Azure Infrastructure Plan

### Required Azure Checks

Before running the benchmark pipeline, verify:

1. regional availability for `Standard_DC8as_v5` in West Europe
2. regional availability for `Standard_D8as_v5` in West Europe
3. approved `Standard DCASv5 Family vCPUs` quota is visible as 16
4. approved `Standard DASv5 Family vCPUs` quota is visible as 16
5. the selected AKS version and OS image support the required confidential node-pool configuration
6. whether the Terraform AzureRM provider version in use supports the required node-pool fields, or whether a controlled Azure CLI step is needed

### AKS Node-Pool Requirements

The implementation plan should add:

- a standard service1 node placement target
- a standard service2 baseline node placement target
- an AMD SEV-SNP confidential service2 node placement target
- node labels that distinguish standard and confidential service2 pools
- node selectors and tolerations for service1 and service2
- validation that service2 lands on the intended node pool in each condition
- validation that service1 remains on a standard node
- validation that the benchmark client remains outside mesh injection

### Metadata to Record

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

### Expected Verification Commands

Examples of checks to preserve in implementation notes or preflight artifacts:

```powershell
az vm list-skus -l westeurope --size Standard_DC8as_v5 -o table
az vm list-skus -l westeurope --size Standard_D8as_v5 -o table
az vm list-usage -l westeurope -o table
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

### Resource and Operation

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

### Validity Checks

RQ2.2 should report:

- activation bytes identical across conditions
- same split topology
- same image digest
- service2 placement validated
- service1 placement validated
- benchmark client outside mesh
- mTLS and AuthorizationPolicy still active
- confidential hardware capability verified

---

## 9. Threat Model and Limitations

AMD SEV-SNP Confidential VM support is a VM-level TEE / confidential-computing environment.

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
- RQ2.2 is not generalizable beyond the approved AMD SEV-SNP AKS confidential-node path without a separate experiment design.

### Istio Sidecar and Plaintext Handling

Istio sidecar placement affects where plaintext exists.

If the service2 sidecar runs on the same confidential node and pod environment as service2, the sidecar and service process are inside the confidential VM boundary. Nevertheless, plaintext exists inside the guest runtime after TLS termination.

If the sidecar cannot run on the confidential node, the RQ2.2 design must stop and be revisited because the RQ2.1 security contract would no longer be preserved in the intended form.

### Hardware Matching Limitation

The approved comparison is:

- standard service2: `Standard_D8as_v5`
- confidential service2: `Standard_DC8as_v5`

If this exact pair cannot be used, preserve the feasibility artifacts and report the platform limitation instead of changing the thesis-facing benchmark path.

### Placement Limitation

Single-node versus cross-node placement can affect latency. If service1 and service2 are on different nodes, the standard and confidential conditions must use matched cross-node topology where possible, and the network-path change must be reported.

---

## 10. Staged Implementation Plan

### Stage 0: Azure Feasibility

Objective: prove that the approved AMD SEV-SNP AKS platform is available before running the benchmark.

Tasks:

1. Verify `Standard_DC8as_v5` availability in West Europe.
2. Verify `Standard_D8as_v5` availability in West Europe.
3. Verify `Standard DCASv5 Family vCPUs` quota limit is 16.
4. Verify `Standard DASv5 Family vCPUs` quota limit is 16.
5. Check whether AKS confidential node pools support the required cluster, OS image, and node-pool configuration.
6. Decide whether Terraform alone is sufficient or whether an Azure CLI node-pool step is required.

Exit criteria:

- the approved standard and confidential SKUs are confirmed
- the approved quotas are visible in Azure
- no blocking AKS confidential node-pool limitation is discovered
- the selected SKU pair is recorded before benchmarking begins

### Stage 1: Manifest and Provisioning Design

Objective: design the placement/provisioning model without running the full benchmark.

Tasks:

1. Add config fields for service2 confidential placement.
2. Add Terraform/node-pool plan for standard service1, standard service2 baseline, and confidential service2 placement.
3. Add manifest-generation plan for `chain_2svc_mtls_standard`.
4. Add manifest-generation plan for `chain_2svc_mtls_confidential_service2`.
5. Run generate-only validation once implementation begins.

Exit criteria:

- generated manifests can express service1 standard placement and service2 standard/confidential placement
- no ad hoc manifest editing is required

### Stage 2: Smoke Deployment

Objective: prove the secure chain works with service2 on the approved confidential node.

Tasks:

1. Deploy `chain_2svc_mtls_confidential_service2`.
2. Validate service2 placement on `Standard_DC8as_v5`.
3. Validate service1 placement on `Standard_D8as_v5`.
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

### Stage 3: Paired RQ2.2 Benchmark

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

### Stage 4: Thesis Interpretation

Objective: write the result without overstating the security claim.

Tasks:

1. Report incremental confidential-execution overhead.
2. Compare only against the newly paired RQ2.2 standard baseline.
3. Treat old RQ2.1 results as context, not the primary baseline.
4. State that the benchmark used the approved `Standard_D8as_v5` versus `Standard_DC8as_v5` pair in West Europe.
5. Discuss sidecar/plaintext and VM-level TEE limitations carefully.

Exit criteria:

- thesis wording distinguishes RQ2.1 communication-level hardening from RQ2.2 VM-level confidential execution
- the result does not claim application-level isolation

---

## 11. Risks and Mitigations

### Risk 1: Approved Quotas Are Not Visible to the Active Subscription

**Mitigation:** Treat Stage 0 Azure feasibility as a formal gate. Record `az vm list-usage -l westeurope` in the artifact before provisioning.

### Risk 2: AKS Rejects the Approved Confidential Node Pool

**Mitigation:** Validate live creation of a temporary `Standard_DC8as_v5` node pool before running any benchmark. If AKS rejects the node pool, stop and preserve the failure artifact.

### Risk 3: Confounding Confidential Execution With Network Topology

**Mitigation:** Match service1/service2 placement topology across the standard and confidential conditions. If cross-node placement is used, use it in both conditions and report it.

### Risk 4: Mesh Sidecar Behavior Differs on Confidential Nodes

**Mitigation:** Treat sidecar readiness and mTLS/Authz validation as required preflight gates.

### Risk 5: RQ2.2 Grows Beyond the Approved AMD Path

**Mitigation:** Keep the initial experiment service2-only, `chain_2svc`-only, West Europe-only, `DASv5`/`DCASv5`-only, and AMD SEV-SNP-only.

### Risk 6: Intro and Abstract Wording Lag Behind the Implemented RQ2 Structure

**Mitigation:** Once RQ2.2 is accepted, update thesis framing so RQ2.1 is described as communication-level hardening and RQ2.2 as VM-level confidential execution.

---

## 12. Final Recommendation

The next step is a narrow, platform-first RQ2.2:

- keep `chain_2svc` as the only initial topology
- keep the RQ2.1 secure mesh contract
- protect service2 first, not the full chain
- use AMD SEV-SNP Azure Confidential VM / AKS confidential node execution
- use West Europe only
- use `Standard_D8as_v5` versus `Standard_DC8as_v5` only
- rely on the approved 16-vCPU `Standard DASv5 Family vCPUs` and 16-vCPU `Standard DCASv5 Family vCPUs` quotas
- compare only against a newly collected RQ2.2 standard baseline
- treat old RQ2.1 results as context
- defer `chain_5svc` until the primary service2-only path is stable

This plan is academically cautious, implementation-ready, and aligned with the thesis claim: RQ2.2 evaluates the additional overhead of placing the protected downstream inference service in a VM-level confidential execution environment using AMD SEV-SNP while preserving the communication-level protections introduced in RQ2.1.
