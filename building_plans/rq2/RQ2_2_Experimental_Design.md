# RQ2.2 Experimental Design

## AKS Confidential-Execution Validation for the Selected Secure Distributed Inference Configuration

---

## Design Recommendation

**Decision: RQ2.2 should evaluate confidential execution as an incremental extension of the final RQ2.1 secure AKS path, not as a new architecture study.**

**Primary configuration: `chain_2svc`.**

**Security baseline carried forward: the final isolated-pool RQ2.1 `chain_2svc_mtls` deployment contract.**

**TEE mechanism recommendation: Azure AKS confidential VM node pools using AMD SEV-SNP, not AKS Confidential Containers preview and not SGX-first enclave-aware application rewrites.**

**Optional secondary stress condition: `chain_5svc`, but only after the primary `chain_2svc` path is stable.**

### Why this is the right RQ2.2 shape

RQ2.2 should answer a narrow question: what extra cost is paid when the selected secure Azure-resident distributed inference deployment is moved onto confidential-computing infrastructure?

It should not reopen:

- split-point selection
- chain-topology selection
- service-mesh mechanism choice
- mixed-ownership orchestration design
- application-level enclave programming

The strongest thesis story is:

1. RQ1 selected and transferred the deployment path.
2. RQ2.1 hardened that path with service identity and mTLS.
3. RQ2.2 adds confidential execution to that already selected secure path and measures the incremental cost.

That means the cleanest primary RQ2.2 comparison is not plain AKS versus confidential execution. It is **secure AKS on standard nodes versus the same secure AKS path on confidential-computing nodes**.

---

## 1. Working RQ2.2 Framing

> **RQ2.2:** What overhead and deployment complexity are introduced when the selected secure Azure-based distributed inference configuration is extended with trusted-execution-based confidential computing?

### Thesis-facing interpretation

RQ2.2 is a **confidential-execution overhead study** layered on top of the final RQ2.1 contract.

It asks whether the selected AKS-resident secure inference path can be moved onto TEE-backed Azure infrastructure while preserving a clear and reproducible performance story.

### What RQ2.2 should explicitly measure

1. Additional end-to-end latency attributable to confidential execution.
2. Additional tail latency attributable to confidential execution.
3. Additional startup and deployment cost attributable to confidential-computing infrastructure.
4. Resource and scheduling effects introduced by confidential node pools.
5. Whether the previously selected `chain_2svc` secure path remains a credible deployment choice once TEE support is added.

### What RQ2.2 should not become

RQ2.2 is not:

- a new service-mesh study
- a new partition-selection study
- a mixed-cloud orchestration study
- a cross-cluster deployment study
- an SGX SDK or Gramine programming exercise
- a comparison of all Azure confidential-computing products

---

## 2. Platform Recommendation

### Recommended primary platform

**Use AKS confidential VM node pools with AMD SEV-SNP as the primary RQ2.2 mechanism.**

This is the best thesis-facing choice because it:

1. keeps RQ2.2 inside the AKS deployment path already established in RQ1.5 and RQ2.1
2. supports heterogeneous node pools, which allows standard and confidential pools in one cluster
3. provides hardware-backed TEE protection without requiring enclave-aware application rewrites
4. preserves the strongest reproducibility story because the application, manifests, and runner model remain recognizably close to the current pipeline

### Why not AKS Confidential Containers preview

Do not use AKS Confidential Containers as the primary RQ2.2 path.

Current Azure documentation indicates that AKS Confidential Containers are preview-only and sunset in March 2026. They also introduce experimental constraints that are poor thesis anchors, including request/limit quirks, pod startup penalties, limited observability/debugging, and policy-heavy deployment behavior.

That is too unstable for the primary thesis mechanism.

### Why not SGX-first as the primary path

Azure AKS supports Intel SGX confidential nodes, but using SGX as the primary RQ2.2 path would push the thesis toward enclave-aware packaging, EPC memory management, attestation plumbing, and possibly application changes.

That is a legitimate future extension, but it is not the lowest-risk way to answer the thesis question.

### RQ2.2 platform decision

**Primary mechanism:** AKS confidential VM node pool (AMD SEV-SNP).

**Not primary:** AKS Confidential Containers preview.

**Possible future extension only:** SGX enclave-aware execution.

---

## 3. Baseline and Condition Set

### Baseline principle

RQ2.2 must isolate confidential-computing overhead from service-mesh overhead.

Therefore the baseline should be:

**the same secure deployment contract as RQ2.1, but without confidential-computing nodes**.

### Primary condition pair

Recommended primary pair:

| Condition                                  | Meaning                                                                                             | Status   |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- | -------- |
| `chain_2svc_mtls_standard_servicepool`     | Final RQ2.1-style secure deployment with services on a standard AKS service pool                    | Required |
| `chain_2svc_mtls_confidential_servicepool` | Same secure deployment, same image, same policies, but services scheduled on a confidential VM pool | Required |

### Optional stress pair

| Condition                                  | Meaning                                                | Status   |
| ------------------------------------------ | ------------------------------------------------------ | -------- |
| `chain_5svc_mtls_standard_servicepool`     | Secure stress baseline on a standard service pool      | Optional |
| `chain_5svc_mtls_confidential_servicepool` | Secure stress condition on a confidential service pool | Optional |

### Why this pair is correct

This pair keeps the comparison narrow:

- same model
- same chain topology
- same mTLS and service identity policy
- same service image digest
- same benchmark client process
- same benchmark contract

The only intended difference is the service-side node-pool trust model.

---

## 4. Deployment Contract

### Core idea

RQ2.2 should move from the RQ2.1 same-node benchmark contract to a **matched two-role contract**:

- one standard node pool for the benchmark client
- one service node pool for inference services

This is necessary because the service TEE property lives on the service-hosting nodes.

### Critical comparison rule

The topology must be identical between the standard and confidential conditions.

That means:

- client placement stays the same across the pair
- service count stays the same across the pair
- service-to-service topology stays the same across the pair
- only the service node-pool type changes across the pair

### Recommended infrastructure contract

Use one AKS cluster with heterogeneous pools:

- `systempool`: standard small system pool for AKS system workloads
- `clientpool`: standard benchmark pool for the benchmark client pod
- `servicepool-standard`: standard pool for the non-confidential secure baseline
- `servicepool-confidential`: confidential VM pool for the TEE condition

### Placement contract

- benchmark client pod pinned to `clientpool`
- service pods pinned either to `servicepool-standard` or `servicepool-confidential` depending on condition
- service pods remain colocated with each other within their service pool for `chain_2svc` and `chain_5svc`
- benchmark client is intentionally separated from the service pool in both conditions, so the network topology is matched

This is a deliberate break from the RQ2.1 same-node client-plus-service contract, but it is methodologically cleaner for RQ2.2 than moving only the confidential condition to a different topology.

---

## 5. Security Model for RQ2.2

### Carried forward from RQ2.1

RQ2.2 should preserve the RQ2.1 mesh policy model:

- benchmark client remains outside the mesh
- secure inference services remain in mesh-enabled namespaces
- downstream inference hops remain protected with workload-scoped `STRICT` mTLS
- explicit service accounts remain required
- authorization policies remain explicit and workload-scoped

### What the TEE adds

The TEE layer adds protection for service execution against the underlying node or hypervisor operator according to the guarantees of the confidential-computing mechanism.

### What remains out of scope

- side-channel attacks
- compromised application logic inside the confidential workload
- model-privacy guarantees stronger than those supplied by the chosen TEE model
- cross-domain attestation federation for external unmanaged segments

---

## 6. Metrics

### Primary metrics

- mean end-to-end latency
- p95 end-to-end latency
- non-compute latency delta
- application CPU and memory
- sidecar CPU and memory
- total pod CPU and memory
- schedule-to-ready delay
- confidential-workload startup overhead
- deployment complexity delta

### Additional RQ2.2-specific metrics

- confidential node-pool provisioning overhead
- attestation evidence collected successfully or not
- pod placement evidence on confidential versus standard service pool
- any confidential-runtime-specific limitations or failures

### Reporting rule

Report TEE overhead incrementally relative to the matched secure non-confidential baseline, not relative to the original plain AKS baseline.

---

## 7. Concrete Implementation Plan

### Stage 0: Scope freeze

Freeze the RQ2.2 scope before coding:

- primary topology is `chain_2svc`
- optional stress topology is `chain_5svc`
- primary TEE mechanism is AKS confidential VM node pools
- baseline is secure RQ2.1-style deployment on standard service nodes
- RQ2.2 does not yet implement mixed external segment ownership or TEE-per-segment orchestration

### Stage 1: Platform spike

Objective: prove the chosen Azure platform works before changing the benchmark pipeline.

Tasks:

1. Add a manual AKS confidential VM service pool in a scratch cluster.
2. Deploy one simple inference pod on the confidential pool.
3. Verify node labels, pod scheduling, image pull behavior, readiness, and network reachability.
4. Capture attestation evidence using Azure sample flow or documented guest-attestation example.
5. Record quota and SKU availability in the target region.

Exit criteria:

- one confidential-pool pod runs successfully
- attestation evidence can be collected or at least the documented mechanism is confirmed workable
- no blocking platform limitation is discovered

### Stage 2: Infrastructure extension

Objective: extend Terraform and provisioning scripts for RQ2.2.

Tasks:

1. Add Terraform variables for `clientpool`, `servicepool-standard`, and `servicepool-confidential`.
2. Add confidential pool support in `infra/main.tf`.
3. Add outputs for confidential-pool names, SKU, and labels.
4. Extend provisioning scripts to create the new pool contract and fail early on quota issues.

Exit criteria:

- cluster provisioning can create the full RQ2.2 pool layout reproducibly

### Stage 3: Config model extension

Objective: separate client placement from service placement.

Tasks:

1. Extend `src/benchmark/config.py` to support distinct placement for benchmark client and service pods.
2. Add an explicit service pool selector to configs.
3. Add a confidential-service-pool flag or condition-level service pool target.
4. Create `configs/rq2/2.2/` with at least:
   - `rq2_2_chain2_mtls_standard_servicepool.yaml`
   - `rq2_2_chain2_mtls_confidential_servicepool.yaml`
   - optional chain5 equivalents later

Exit criteria:

- one config can place the client on one pool and services on another without ad hoc script edits

### Stage 4: Manifest generation and runtime metadata

Objective: make manifest generation aware of the new placement model.

Tasks:

1. Update `k8s/aks/generate_aks_manifests.py` so client and service placement are generated separately.
2. Preserve existing RQ2.1 mesh settings for the secure path.
3. Extend runtime metadata capture so it records client node, service nodes, pool labels, and confidential-pool evidence.

Exit criteria:

- generated manifests show correct pool selection for client and services
- runtime metadata distinguishes standard and confidential placement correctly

### Stage 5: Preflight and validation

Objective: create a fail-closed RQ2.2 preflight gate.

Tasks:

1. Add an RQ2.2 preflight runner based on the RQ2.1 preflight pattern.
2. Verify service pods land on the intended confidential or standard service pool.
3. Verify secure mesh behavior still holds.
4. Verify startup behavior and benchmark pipeline correctness.
5. Record attestation evidence or a documented attestation artifact path.

Exit criteria:

- secure benchmark chain is functional on the confidential service pool
- placement and attestation evidence are captured

### Stage 6: Paired benchmark runner

Objective: implement the main RQ2.2 experiment runner.

Tasks:

1. Create a dedicated paired runner for RQ2.2 or adapt the RQ2.1 paired runner carefully.
2. Keep condition ordering interleaved as in RQ2.1.
3. Export merged summaries, raw iterations, placement metadata, resource metrics, and attestation evidence.
4. Explicitly compare secure-standard versus secure-confidential conditions.

Exit criteria:

- one complete `chain_2svc` paired run succeeds with stable artifacts

### Stage 7: Execution sequence

Recommended execution order:

1. Confidential platform spike
2. RQ2.2 `chain_2svc` preflight on standard service pool
3. RQ2.2 `chain_2svc` preflight on confidential service pool
4. Full paired `chain_2svc` run
5. Only if stable: optional `chain_5svc` stress pair

---

## 8. Thesis Risks and Mitigations

### Risk 1: Confidential Containers preview instability

**Mitigation:** Do not use it as the primary RQ2.2 path.

### Risk 2: Confidential SKU quota or availability mismatch

**Mitigation:** Treat platform spike and quota verification as a formal gate before pipeline work.

### Risk 3: Confounding client placement with confidential execution

**Mitigation:** keep the client on the same standard pool in both paired conditions and use matched service-pool topology across the pair.

### Risk 4: RQ2.2 growing into a mixed-segment orchestration study

**Mitigation:** defer mixed external segment ownership to a later engineering track. Day-one RQ2.2 should stay inside a fully thesis-managed AKS deployment.

### Risk 5: Intro and abstract wording lag behind the implemented RQ2 structure

**Mitigation:** once RQ2.2 is accepted, update thesis framing so RQ2.1 is described as secure transport/service identity and RQ2.2 as confidential execution.

---

## 9. Final Recommendation

The next step should be a **narrow, platform-first RQ2.2**:

- keep `chain_2svc` primary
- keep the RQ2.1 secure mesh contract
- add confidential execution through AKS confidential VM node pools
- compare against a matched secure non-confidential service-pool baseline
- treat `chain_5svc` only as optional secondary stress evidence

That plan is concrete, implementable with the current repository shape, and keeps the thesis claim defensible.
