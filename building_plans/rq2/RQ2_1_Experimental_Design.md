# RQ2.1 Experimental Design

## AKS Service Mesh mTLS Validation for the Selected Distributed Inference Configuration

---

## Design Recommendation

**Decision: `chain_2svc` should be the PRIMARY RQ2.1 configuration.**

**Security mechanism: Azure-native AKS Istio add-on in sidecar mode, using workload identity and mTLS for east-west service-to-service traffic.**

**Optional secondary stress condition: `chain_5svc`, but only after the primary `chain_2svc` path is stable and only as a paired stress check, not as the headline result.**

### Why this is the right design

**RQ2.1 is not a new architecture study.**
RQ2.1 comes after RQ1.5. Its job is to measure the incremental cost of adding transport security and service identity to the Azure-resident distributed inference deployment already established in RQ1.5. It must not reopen boundary selection, topology selection, or distributed execution strategy.

**`chain_2svc` is the cleanest non-monolithic anchor.**
`chain_2svc` is the smallest configuration that still contains a real inter-service activation transfer. That makes it the minimum valid configuration for studying east-west protection. It has exactly one protected microservice-to-microservice hop, which means the measured overhead can be interpreted primarily as the cost of service-mesh security rather than the cost of repeated chaining.

**`chain_5svc` is too confounded to be primary.**
If `chain_5svc` were used as the primary RQ2.1 condition, the study would immediately entangle three factors: service-mesh security overhead, sidecar multiplication, and repeated multi-hop forwarding. That is not methodologically clean. It would be a stress test of the most fragmented topology, not a focused validation of secure transport on the selected Azure distributed deployment.

**The primary RQ2.1 claim should be easy to defend.**
The strongest thesis story is:

1. RQ1 established that split execution is viable and characterized its cost.
2. RQ1.5 validated that the chain family transfers to AKS.
3. RQ2.1 then asks what extra cost is paid when the chosen AKS distributed deployment is hardened with service identity and mTLS.

That story is strongest when the chosen deployment is the simplest true distributed case, namely `chain_2svc`.

**Azure-native managed Istio is the least risky way to answer the question.**
The literature shows that service-mesh overhead can be substantial, and that much of it comes from sidecars and protocol processing rather than from cryptography alone. That makes mechanism choice critical. For this repository, the right move is not to build a new security stack. It is to use the AKS-native managed Istio add-on so that RQ2.1 remains a security-overhead study, not an infrastructure-engineering detour.

---

## Literature-Grounded Constraint Summary

The local RQ2 paper notes support a narrow, disciplined design rather than a broader one.

**Service-mesh overhead is real and can be large.**
`Dissecting Service Mesh Overheads` reports that service meshes can add substantial latency and CPU overhead, and that protocol parsing and sidecar data-path costs are often dominant. This argues for keeping the primary RQ2.1 topology simple so that security overhead is not hidden inside a larger chaining effect.

**mTLS overhead depends strongly on mesh architecture.**
`Performance Comparison of Service Mesh Frameworks: the MTLS Test Case` shows clear differences between sidecar and sidecar-less designs, with sidecar-less variants usually lighter. However, the same literature also shows that these are architecture comparisons, not just security comparisons. RQ2.1 should not become a broad service-mesh bake-off.

**Ambient and eBPF acceleration are interesting, but not the right thesis move here.**
The eBPF and Ambient papers motivate future optimization work, not the primary thesis implementation. Azure's AKS Istio add-on documentation also states that Ambient mode is not supported in the managed add-on path. That removes it as a realistic primary mechanism for this repository.

**Control plane trust remains a known limitation.**
`Mazu: A Zero Trust Architecture for Service Mesh Control Planes` is useful because it highlights that service-mesh control planes remain trust anchors. That strengthens the threat-model section of RQ2.1 and supports explicitly keeping control-plane compromise out of scope.

**Custom application-layer crypto would widen scope and confound the question.**
The HTTP/3 plus AES paper is useful mainly as a rejection signal here: if RQ2.1 used custom gRPC transport or application-layer encryption, the study would stop being about service identity and east-west service mesh security on AKS. It would become a protocol redesign study.

**Cryptographic secure inference literature addresses a different threat class.**
The secure-inference and partition-privacy papers are important context, but they defend against stronger adversaries and require fundamentally different protocol or hardware assumptions. They are not a minimal extension of RQ1.5.

---

## 1. Research Question Framing

> **RQ2.1:** What overhead and deployment complexity are introduced when inter-service communication is secured using mutual TLS and service identity mechanisms on the selected Azure-based distributed inference configuration?

### Thesis-facing interpretation

RQ2.1 is a **security overhead study built directly on RQ1.5**.

It asks whether the selected AKS-resident distributed inference deployment can be hardened with service identity and mTLS while preserving a methodologically clear, reproducible, and practically interpretable performance profile.

More concretely, RQ2.1 validates:

1. The additional end-to-end latency introduced by securing inter-service activation transfers.
2. The additional tail latency introduced by that security layer.
3. The added runtime resource cost attributable to sidecars and mesh enforcement.
4. The deployment and operational complexity delta relative to the frozen RQ1.5 non-mesh AKS pipeline.

### What RQ2.1 does NOT validate

RQ2.1 is not:

- A new partition-selection study.
- A new model-distribution study.
- A new distributed protocol design.
- A comparison of all service meshes as a product survey.
- A control-plane hardening study.
- An application-layer encryption study.
- A TEE, HE, MPC, or secure multi-server inference study.
- A multi-cluster, multi-region, or WAN-distribution study.
- A redesign of the RQ1.5 orchestration pipeline.

### How it fits after RQ1.5

RQ1.5 answered whether the chained inference family transfers from local Kubernetes to AKS under a tightly controlled same-node deployment contract.

RQ2.1 uses that frozen AKS execution path as the baseline and asks a narrower follow-up question: once the distributed deployment is accepted, what does it cost to secure the internal service boundaries?

That is the correct next step. It builds on RQ1.5 rather than competing with it.

---

## 2. Dependency on Earlier Stages

### What RQ2.1 inherits directly

From RQ1.1-RQ1.3:

- The selected split vocabulary and frozen split points.
- The explanation that activation-transfer burden, not only compute placement, shapes distributed inference cost.

From RQ1.4:

- The service-side forwarding model.
- The fixed chain family definitions.
- The gRPC plus Protocol Buffers transport contract.

From RQ1.5:

- AKS provisioning via Terraform and Azure CLI.
- ACR image build/push and digest pinning.
- Config-driven AKS manifest generation.
- Rolling deployment and benchmark orchestration.
- Same-node placement enforcement.
- Benchmark execution contract.
- Artifact export and host-side analysis.
- Deployment metadata capture and reproducibility structure.

### What RQ2.1 must not reopen

- No new split points.
- No new partition granularity.
- No new chain architecture.
- No new network protocol between services.
- No new container image layout.
- No migration away from AKS.

The security mechanism must therefore be layered on top of the existing service graph, not embedded into application logic.

---

## 3. Baseline Selection

### Options considered

| Option                                | Strength                                                                                               | Weakness                                                                   | Verdict                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `chain_2svc` only                     | Minimal valid distributed case; one protected east-west hop; easiest to attribute overhead to security | Does not show multi-hop accumulation by itself                             | **Best primary choice**                                      |
| `chain_5svc` only                     | Maximizes observable mesh overhead; tests cumulative hop compounding                                   | Confounds security cost with maximal fragmentation and repeated forwarding | Reject as primary                                            |
| Multiple configurations / full family | Broadest coverage                                                                                      | Reopens RQ1.5-style family analysis and expands scope unnecessarily        | Reject as primary; allow only targeted secondary stress pair |

### Final recommendation

**Primary RQ2.1 configuration: `chain_2svc`.**

This is the correct primary choice because it is the simplest configuration that still genuinely requires protected inter-service communication. It preserves methodological clarity, keeps engineering risk down, and directly answers the RQ.

### Why `chain_5svc` should NOT be primary

`chain_5svc` is architecturally interesting, but it is the wrong headline configuration for RQ2.1.

If it becomes the primary experiment, the interpretation shifts from:

"What is the cost of securing the chosen AKS distributed deployment?"

to:

"What is the cost of securing the most fragmented chain we have?"

That is a weaker thesis claim because it is easier to challenge as an extreme-case construction rather than the selected deployment.

### Role of `chain_5svc`

`chain_5svc` should be used only as an **optional stress condition**, and only as a paired secondary check after the primary `chain_2svc` study is stable.

Its role is not to define the thesis result. Its role is to answer a narrower secondary question:

"Does service-mesh overhead compound materially across deeper chain lengths?"

That is useful, but secondary.

---

## 4. Security Mechanism Selection

### Options compared

| Option                        | Fit to current repo                                   | Code change burden                                           | Operational burden                                             | Methodological clarity                                 | Verdict       |
| ----------------------------- | ----------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------ | ------------- |
| Self-managed Istio mTLS       | Reasonable Kubernetes fit, but not AKS-native         | Low application change, medium cluster change                | High; own install, lifecycle, troubleshooting                  | Good for mesh study, worse for reproducibility         | Reject        |
| Linkerd                       | Simpler than Istio in some cases                      | Low application change, medium manifest change               | Medium; new stack outside current AKS-native path              | Turns RQ2.1 into partial mesh comparison               | Reject        |
| Azure-native AKS Istio add-on | Excellent fit to existing AKS path                    | Minimal application change; minimal targeted pipeline change | Lowest of the mesh options                                     | Strongest for a focused AKS thesis chapter             | **Recommend** |
| Manual gRPC TLS               | Requires code-path and certificate-management changes | Highest application intrusion                                | High; custom certs, rotation, channel config, identity mapping | Confounds transport security with application redesign | Reject        |

### Recommendation

**Use the Azure-native AKS Istio add-on, in sidecar mode, with workload identity and mTLS enabled for inference-service east-west traffic.**

This is the right choice because:

1. It stays inside the AKS platform already used in RQ1.5.
2. It avoids creating a self-managed control plane that the thesis would then need to defend operationally.
3. It lets the experiment study service identity and mTLS without changing the application protocol or partition code.
4. It preserves the strongest reproducibility story: same cluster family, same image, same runner, same benchmark contract, one added security layer.

### Why not self-managed Istio

Self-managed Istio would still answer the technical question, but it adds unnecessary operational variance: installation mode, revision handling, upgrade burden, and support responsibility all move into thesis-owned infrastructure. That is avoidable. The Azure add-on already exists for this exact AKS context.

### Why not Linkerd

Linkerd is a valid service mesh, and some literature shows favorable overhead. But adopting it here would turn RQ2.1 into a platform-selection argument instead of an AKS-native security-overhead argument. It would also weaken reuse of Azure guidance and managed lifecycle.

### Why not manual gRPC TLS

Manual TLS is the wrong mechanism for this thesis stage because it would require changes to service code, certificate provisioning, channel bootstrapping, and identity management. It would also answer a subtly different question: application-managed secure channels, not service-mesh-managed identity and mTLS for Kubernetes microservices.

### Important Azure constraint

According to AKS Istio add-on documentation, Azure's managed add-on does **not** support Ambient mode today. That means the realistic Azure-native choice is managed sidecar-mode Istio, not Ambient.

### Contingency if managed Istio blocks implementation

The preferred mechanism remains the Azure-native AKS Istio add-on. However, if the managed add-on introduces a blocking platform limitation that prevents the RQ2.1 experiment from being executed correctly, the fallback is **self-managed Istio in sidecar mode while preserving the same experimental design**. This fallback must not change the research question, topology, benchmark protocol, or interpretation. It should only replace the mesh provisioning mechanism. If the fallback is used, the thesis must report it explicitly as an implementation deviation and record the Istio installation mode, version, revision, and configuration in deployment metadata.

---

## 5. Threat Model

### Protected assets

RQ2.1 focuses on protecting:

- Intermediate activations in transit between inference microservices.
- Service-to-service authenticity for the chained inference path.
- Integrity of inter-service messages in the presence of traffic interception or spoofing.

### Attacker capabilities considered in scope

The attacker may:

- Passively observe pod-to-pod traffic inside the cluster network path.
- Attempt to intercept or reroute traffic between services.
- Attempt to impersonate an inference service without holding the expected mesh-issued workload identity.
- Attempt a man-in-the-middle attack between chained inference services.
- Capture traffic and replay packets within the transport path.

### Attacks mitigated by the chosen mechanism

With managed Istio mTLS and workload identity, RQ2.1 should mitigate:

- Passive traffic interception of activation payloads in transit.
- Unauthorized service impersonation by workloads that lack the expected mesh identity.
- Classic on-path MITM without valid certificates.
- In-transit tampering of the protected connection.
- Connection-level replay or packet reinjection within the TLS-protected channel.

### What remains out of scope

The following are explicitly out of scope for RQ2.1:

- A compromised inference service that is already legitimately inside the mesh.
- A compromised sidecar or node that can read plaintext before encryption or after decryption.
- A compromised AKS or Istio control plane issuing valid workload credentials.
- A malicious insider able to deploy a pod under the same Kubernetes service account identity as a legitimate inference workload.
- Application-level replay by an already authorized caller.
- Model-privacy protection against the participating services themselves.

### Critical nuance

To make service identity meaningful, **each inference service should use an explicit Kubernetes ServiceAccount rather than the namespace default**.

If all services use the same default service account, the service-identity story becomes much weaker. That is avoidable and should be fixed in RQ2.1 manifests.

---

## 6. Metrics

RQ2.1 needs both performance metrics and engineering-complexity metrics.

The Istio sidecar is **not** experimental noise in this design. It is part of the chosen security mechanism, so its resource use, startup behavior, and scheduling effects are explicit elements of the reported security cost.

### Primary metrics

| Metric                              | Definition                                                                                                                             | Why primary                                                        |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Mean end-to-end latency (ms)        | Mean client-observed round-trip latency over measured iterations                                                                       | Primary performance answer to the RQ                               |
| p95 end-to-end latency (ms)         | 95th percentile client-observed latency                                                                                                | Captures tail cost of security layer                               |
| CPU overhead                        | Reported as application container CPU, `istio-proxy` CPU, and total pod CPU for matched plain versus secure runs                       | Treats sidecar runtime cost as part of the security mechanism      |
| Memory overhead                     | Reported as application container memory, `istio-proxy` memory, and total pod memory for matched plain versus secure runs              | Makes sidecar footprint explicit rather than implicit              |
| Deployment complexity delta         | Additional always-on components, additional mesh resources, and additional orchestration steps relative to RQ1.5                       | RQ2.1 explicitly asks about deployment complexity                  |
| Sidecar startup and scheduling cost | Sidecar startup delay plus any observed scheduling pressure attributable to injected sidecars and their explicit resource reservations | Captures operational cost that is part of enabling the secure path |

### Secondary metrics

| Metric                         | Definition                                                                                              | Collection plan                                                |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Relative latency overhead (%)  | `(secure mean / baseline mean - 1) * 100`                                                               | Derived from the primary latency summaries                     |
| Handshake overhead             | Excess latency of the first request on a fresh gRPC channel relative to warmed steady-state requests    | Optional cold-channel micro-benchmark or first-request tagging |
| Operational complexity metrics | Certificate rotation behavior, mesh-specific failures, restart requirements, revision-management burden | Logged during run and summarized descriptively                 |

### Precise metric definitions

**Mean end-to-end latency**
Measured exactly as in RQ1.5: client-side time from just before request serialization to just after the final response is returned.

**p95 latency**
Computed from the same raw iteration set as mean latency.

**CPU overhead**
For each benchmark condition, sample service-pod container CPU every 5 seconds during steady-state measurement. Report:

- application container CPU
- `istio-proxy` CPU
- total pod CPU
- delta versus matched non-mesh baseline at both container and total-pod level

**Memory overhead**
Same collection method as CPU. Report:

- application container memory
- `istio-proxy` memory
- total pod memory
- delta versus matched non-mesh baseline at both container and total-pod level

These CPU and memory breakdowns are part of the main RQ2.1 security-overhead story, because the sidecar footprint is a direct cost of the selected security mechanism.

**Sidecar startup delay**
Measure the interval from pod scheduling to both application container and `istio-proxy` reaching Ready. Report this explicitly for the secure deployment because it is part of the operational cost of enabling mTLS.

**Scheduling pressure caused by sidecars**
Record whether injected sidecars and their reserved resources change scheduling outcomes, increase pending time, or reduce placement headroom relative to the matched plain deployment. This should be reported descriptively and, where possible, with simple timing and allocatable-capacity evidence from the preflight gate.

**Handshake overhead**
Handshake overhead is optional rather than required. Steady-state gRPC with connection reuse does not pay a full handshake for every request, so a handshake-specific probe may be noisy and is not core to the thesis contribution. If included, it should be estimated by a fresh-connection micro-benchmark and reported separately from the main steady-state latency results.

**Deployment complexity metrics**
These should be objective, not impressionistic. The minimum scorecard should include:

- additional AKS enablement step count
- additional Kubernetes object count
- additional always-on control-plane pod count
- additional per-workload injected container count

**Operational complexity metrics**
These are secondary observational metrics and should include:

- mesh revision pinning burden
- sidecar readiness failures
- policy mismatch failures
- certificate rotation or sidecar restart anomalies

### Core reporting contract

The minimum thesis-facing RQ2.1 result table should report:

- mean latency
- p95 latency
- application container CPU
- `istio-proxy` CPU
- total pod CPU
- application container memory
- `istio-proxy` memory
- total pod memory
- sidecar startup delay
- scheduling pressure caused by sidecars
- deployment complexity scorecard

---

## 7. Experimental Design

### Baseline

**Baseline condition:** the non-secure AKS deployment inherited from RQ1.5 for `chain_2svc`, rerun under the final RQ2.1 isolated-pool AKS contract.

This is the direct reference point for RQ2.1. Same model image, same split point, same benchmark node pool, same benchmark-node placement, same client-side measurement, same warmup policy, same iteration counts.

### Condition A

**Condition A:** the same `chain_2svc` deployment with AKS managed Istio sidecars and mTLS-enabled service identity for the east-west inference hop.

### Optional stress condition

**Optional secondary condition:** a matched `chain_5svc` pair.

This should be executed only after the primary `chain_2svc_mtls` path passes the formal RQ2.1 infrastructure preflight gate and then produces stable matched results in the primary paired experiment. Its purpose is to test whether mesh overhead compounds materially across deeper chain lengths.

### Recommended condition set

| Condition          | Purpose                           | Status   |
| ------------------ | --------------------------------- | -------- |
| `chain_2svc_plain` | Primary non-mesh reference        | Required |
| `chain_2svc_mtls`  | Primary secure condition          | Required |
| `chain_5svc_plain` | Secondary matched stress baseline | Optional |
| `chain_5svc_mtls`  | Secondary secure stress condition | Optional |

### Why this set is correct

This gives one clean primary pair and one optional stress pair. It answers the RQ without drifting back into a full-family re-evaluation.

### Final RQ2.1 infrastructure contract

Final thesis-facing RQ2.1 runs use an isolated two-pool AKS contract:

- a small `Standard_D2s_v3` system pool for AKS system and managed-Istio control-plane workloads
- a benchmark pool named `rq15pool` on `Standard_D8s_v3` with one node
- a benchmark-only taint such as `workload=benchmark:NoSchedule`
- benchmark client and inference service pods with matching tolerations and node selection for the benchmark pool
- strict same-node placement within the benchmark pool

This change is scoped to RQ2.1. It is not a mandatory rerun requirement for RQ1.5, whose role is Azure transfer and validation rather than attribution-sensitive mesh overhead. Existing single-pool RQ2.1 runs remain valid but limited evidence of the managed AKS deployment used at the time. They must not be mixed with the isolated-pool campaign in final thesis reporting. Only isolated-pool RQ2.1 results are final thesis numbers.

`chain_2svc` remains the primary result. `chain_5svc` remains secondary stress evidence.

### Critical traffic-isolation decision

RQ2.1 is about **east-west traffic between inference microservices**, not about benchmark-client ingress traffic.

Therefore:

1. The benchmark client should remain **outside the mesh** in an unlabelled namespace.
2. The inference services should run in a mesh-enabled namespace.
3. `PeerAuthentication` should be applied so that the first service can still receive plaintext traffic from the client, while downstream inference services require mTLS.

For the primary `chain_2svc` case, that means:

- service 1 may accept plaintext inbound from the benchmark client
- service 2 should require mTLS from service 1

This isolates the secured **inter-service** hop rather than accidentally measuring a secured client-to-cluster ingress hop.

### Recommended policy shape

At namespace scope, use `PERMISSIVE` as the default. Then apply workload-scoped `STRICT` policies to downstream inference services.

This is the right choice because a namespace-wide `STRICT` policy would force the benchmark client into the mesh and contaminate the measurement boundary.

### Topology and execution controls

Keep the following identical to RQ1.5 wherever possible:

- Same AKS region.
- Same benchmark node SKU as the current Azure RQ1.5/RQ2.1 D8 profile.
- Same strict same-hostname placement contract for benchmark client and service pods inside the benchmark pool.
- Same image digest.
- Same benchmark repetitions and warmup calibration.
- Same gRPC settings and max message size.
- Same client-side timing boundaries.

The node-pool contract is intentionally different for final RQ2.1: the benchmark node is isolated from avoidable managed-Istio control-plane placement by using a separate system pool plus a tainted benchmark pool. With `Standard_D2s_v3` for the system pool and `Standard_D8s_v3` for the benchmark pool, the documented DSv3 quota assumption remains 10 vCPU total.

### Formal RQ2.1 infrastructure preflight gate

Before any real benchmark execution, RQ2.1 must pass a fail-closed infrastructure preflight gate using `chain_2svc_mtls`.

The preflight deployment must verify all of the following:

- sidecar injected correctly for the secure service pods
- benchmark client remains outside the mesh
- same-node placement still holds for the inference services
- both application and `istio-proxy` containers become Ready
- no obvious resource starvation or unschedulable pressure is introduced by the sidecars
- mesh control-plane/system pod placement is recorded
- no avoidable managed-Istio control-plane deployment is colocated on the benchmark node under the isolated-pool contract
- latency measurement pipeline still works end to end

This is not an informal smoke check. It is a formal exit gate for the RQ2.1 experiment path.

### Preflight exit criteria

The RQ2.1 experiment may proceed only if the `chain_2svc_mtls` preflight shows that:

- secure service pods contain the expected `istio-proxy` container
- the client pod remains non-meshed
- the secure chain still satisfies the same-node placement contract
- both containers in each secure pod become Ready without prolonged pending or restart behavior
- proxy resource reservations do not create unacceptable scheduling pressure on the selected node profile
- mesh control-plane/system pod placement is known
- avoidable managed-Istio control-plane deployments are not colocated on the benchmark node under the isolated-pool contract
- a short validation run produces usable latency artifacts with the existing measurement pipeline

If any of these checks fail, the benchmark phase must not start until the issue is corrected.

### Round ordering

Do **paired round interleaving**, not "all baseline first, all secure later".

Recommended order:

1. Baseline round 1
2. Secure round 1
3. Baseline round 2
4. Secure round 2
5. Continue until all rounds are complete

This reduces drift from Azure background variance, time-of-day changes, and cluster warm-state differences.

---

## 8. Azure Architecture Changes

### What changes

#### AKS cluster configuration

- Enable the AKS Istio add-on on the existing cluster or at cluster creation.
- Pin an explicit supported mesh revision rather than relying on the moving default.
- For final RQ2.1 runs, use a dedicated system pool plus a separate benchmark pool.
- System pool: `Standard_D2s_v3` x1, intended for AKS system and managed-Istio control-plane workloads.
- Benchmark pool: `rq15pool` on `Standard_D8s_v3` x1, intended for the benchmark client and inference services.
- Apply a benchmark-only taint such as `workload=benchmark:NoSchedule` to the benchmark pool.
- Apply matching tolerations and benchmark-pool node selection to all RQ2.1 benchmark client and inference pods.
- Keep strict same-node placement inside the benchmark pool.
- Fail preflight or paired validation if avoidable managed-Istio control-plane deployments are colocated on the benchmark node under this isolated contract.
- Continue recording mesh control-plane/system pod placement in deployment metadata. Standard Kubernetes daemonsets may still exist on the benchmark node; the isolation target is the avoidable managed-Istio control-plane deployment placement.

#### Namespace layout

- Add a new mesh-enabled namespace for the secure condition, labeled with the exact AKS Istio revision (`istio.io/rev=asm-X-Y`).
- Keep the benchmark client in a separate, non-mesh namespace.

#### Service deployment

- Keep the same inference image and same segment-runtime selection model.
- Add explicit Kubernetes ServiceAccounts per inference workload for stable service identity.
- Add explicit sidecar proxy resource controls so CPU and memory requests plus limits are visible, pinned, and reproducible.

#### Certificates and identity

- Use mesh-issued workload certificates managed by the Istio add-on.
- Do **not** introduce manual certificate provisioning.
- Record service accounts, sidecar image IDs, and mesh revision in deployment metadata.

#### Mesh security configuration

- Use namespace-level `PERMISSIVE` as the default for the secure namespace.
- Add workload-scoped `STRICT` `PeerAuthentication` resources for downstream inference services.
- Do not add traffic-routing features such as retries, VirtualServices, fault injection, or custom Envoy filters in the primary RQ2.1 study.

#### Benchmark metadata capture

- Extend deployment metadata capture to include mesh revision, namespace labels, service account names, sidecar image digests, proxy resource settings, policy resources applied, and mesh control-plane/system pod placement relative to the benchmark node.

### What should remain unchanged

| Component                   | RQ1.5                            | RQ2.1              | Notes                                        |
| --------------------------- | -------------------------------- | ------------------ | -------------------------------------------- |
| Model partition logic       | Frozen                           | Unchanged          | No repartitioning                            |
| Container image             | Single thesis image              | Same image         | Only mesh sidecar is added                   |
| gRPC protocol               | Fixed                            | Unchanged          | No custom TLS in application code            |
| Chain forwarding model      | Service-side forwarding          | Unchanged          | No architectural redesign                    |
| Benchmark runner structure  | Rolling controlled orchestration | Same base approach | Add mesh hooks only                          |
| Analysis of raw latency CSV | Existing pipeline                | Reused             | Add supplemental resource/complexity outputs |

### Recommended secure-namespace pattern

For the primary condition, a policy shape like the following is appropriate:

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: rq21-mtls
spec:
  mtls:
    mode: PERMISSIVE
---
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: downstream-strict
  namespace: rq21-mtls
spec:
  selector:
    matchLabels:
      condition: chain_2svc
      segment-index: "2"
  mtls:
    mode: STRICT
```

This keeps the benchmark client outside the mesh while still enforcing mTLS on the actual inter-service inference hop.

### Recommended proxy resource control

Use explicit proxy resource annotations on service pods, for example through generated pod metadata, so sidecar resource costs are not implicit or drifting. The exact numbers should be calibrated in preflight testing, but the pattern should be explicit rather than defaulting to opaque platform choices.

At minimum, the generated manifests or config-driven templates should surface:

- `sidecar.istio.io/proxyCPU`
- `sidecar.istio.io/proxyCPULimit`
- `sidecar.istio.io/proxyMemory`
- `sidecar.istio.io/proxyMemoryLimit`

This keeps sidecar requests and limits reproducible, reviewable, and attributable during analysis.

---

## 9. Code Reuse Map

### Existing code that should be reused directly

| Existing artifact                        | Reuse level | RQ2.1 delta                                                                                                      |
| ---------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------- |
| `infra/main.tf`                          | High        | Reuse cluster and ACR foundation; add RQ2.1-only two-pool infrastructure switch plus mesh-enable step             |
| `scripts/run_rq15_fully_controlled.py`   | High        | Reuse orchestration structure, provisioning, push, export, merge, analysis calls                                 |
| `scripts/preflight_rq15_full.py`         | Medium-High | Reuse capacity checks; extend for sidecar resource headroom and same-node secure-deployment gating               |
| `k8s/aks/generate_aks_manifests.py`      | High        | Extend to emit namespace revision labels, service accounts, proxy annotations, and optional `PeerAuthentication` |
| `scripts/inject_k8s_runtime_metadata.py` | High        | Extend to capture mesh revision, sidecar container data, proxy resources, service accounts, and mesh policies    |
| `run_analysis.py`                        | High        | Reuse latency analysis unchanged or near-unchanged for primary latency CSVs                                      |
| Deployment metadata pipeline             | High        | Reuse and extend rather than replace                                                                             |

### New files/scripts that are minimally required

The minimum new artifact set should be:

1. `configs/rq2/2.1/rq2_1_chain2_plain.yaml`
2. `configs/rq2/2.1/rq2_1_chain2_mtls.yaml`
3. `scripts/run_rq21_fully_controlled.py`
4. `scripts/sample_k8s_resources.py`

For this hardening refinement, **no additional new top-level scripts or configs beyond this set are required**. The formal RQ2.1 preflight gate should be implemented as a mode or phase of the planned RQ2.1 runner, reusing the existing preflight logic and manifest generator rather than introducing a separate benchmark path.

Optional but likely useful:

5. `configs/rq2/2.1/rq2_1_chain5_plain.yaml`
6. `configs/rq2/2.1/rq2_1_chain5_mtls.yaml`
7. A thin RQ2.1-specific postprocessor if you want one file that merges latency, resource, and complexity outputs into thesis-ready summary tables

### Why new configs are preferable to modifying old ones

RQ1.5 is frozen. The existing configs and run path should not be edited into a dual-use state if that risks changing the already completed chapter. New RQ2.1 configs preserve reproducibility and keep chapter boundaries clean.

### Why a new runner is preferable to mutating the RQ1.5 runner heavily

The RQ1.5 runner is already thesis-critical and end-to-end. RQ2.1 introduces a different execution contract:

- paired plain vs secure execution
- mesh enablement and revision handling
- resource sampling
- mesh metadata capture
- formal `chain_2svc_mtls` preflight gating

That argues for a thin new RQ2.1 runner that reuses RQ1.5 building blocks rather than heavily editing the frozen RQ1.5 path.

### Minimal implementation delta for this refinement

This hardening patch does not require a redesign of the planned implementation. The minimum incremental changes are:

- add an RQ2.1-only isolated system plus benchmark pool infrastructure contract
- add benchmark-pool taints, benchmark workload tolerations, and benchmark-pool node selection
- make final RQ2.1 preflight fail if avoidable managed-Istio control-plane deployments share the benchmark node
- extend config and manifest generation to expose explicit `istio-proxy` CPU and memory requests plus limits
- extend the planned resource sampler to report application container, proxy container, and total pod usage separately
- extend the planned RQ2.1 runner with a formal `chain_2svc_mtls` preflight phase
- extend metadata capture so proxy resources, sidecar readiness timing, and placement evidence are preserved in artifacts

No separate architecture path, no new benchmark topology, and no additional condition family are needed.

---

## 10. Experimental Risks

| Risk                                        | Why it matters                                                                                               | Mitigation                                                                                                                                                                                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sidecar not injected                        | Secure condition silently becomes non-secure                                                                 | Verify `istio-proxy` container presence before each round                                                                                                                                                                                                  |
| Wrong mesh revision label                   | Namespace labeled to unsupported or stale revision                                                           | Pin revision explicitly and record it in metadata                                                                                                                                                                                                          |
| Client accidentally enters mesh             | First-hop measurement becomes a different experiment                                                         | Keep client namespace unlabelled and validate pod container count                                                                                                                                                                                          |
| Downstream policy too strict                | Client cannot reach service 1 or chain fails unexpectedly                                                    | Use `PERMISSIVE` namespace default plus workload-scoped `STRICT`                                                                                                                                                                                           |
| Sidecar startup delay                       | Warmup may begin before data plane is actually ready                                                         | Add sidecar readiness checks and capture readiness delay                                                                                                                                                                                                   |
| Sidecar resource inflation                  | Scheduling or contention may invalidate same-node assumptions                                                | Set explicit proxy resource annotations and extend preflight                                                                                                                                                                                               |
| Hidden proxy defaults                       | Uncontrolled sidecar requests and limits weaken reproducibility                                              | Pin explicit proxy CPU and memory requests plus limits in generated manifests and configs                                                                                                                                                                  |
| Certificate rotation during run             | Can create transient latency or failure spikes                                                               | Keep benchmark windows short and record timing of any rotation event                                                                                                                                                                                       |
| Azure background noise                      | Cloud variance can mask small overheads                                                                      | Interleave baseline and secure rounds and keep same-node placement                                                                                                                                                                                         |
| Control-plane contention on experiment node | Mesh control-plane pods may share CPU with inference benchmark pods and introduce avoidable scheduling noise | Final RQ2.1 uses a dedicated system pool plus tainted benchmark pool; fail preflight if avoidable managed-Istio control-plane deployments share the benchmark node |
| Mesh misconfiguration                       | Failed or partial enforcement invalidates conclusions                                                        | Add fail-closed validation that checks sidecars, policies, and pod identities before measurement                                                                                                                                                           |

### Highest-risk implementation issue

The highest-risk design mistake is **measuring the wrong path**.

If the benchmark client is also meshed, RQ2.1 will partly become a client-to-service secure ingress study rather than a service-to-service east-west study. That must be avoided.

---

## 11. Rejected Alternatives

### Full encryption schemes for activations

Rejected because they would change the semantics of the service interaction itself rather than simply securing transport. They would push RQ2.1 toward application redesign and away from a clean infrastructure-layer security study.

### Homomorphic encryption

Rejected because it addresses a much stronger threat model than RQ2.1 and would require a different execution protocol, different latency regime, and likely a different research chapter. It does not build minimally on RQ1.5.

### MPC

Rejected for the same reason as HE. MPC-based secure inference is not a transport-hardening layer on top of RQ1.5. It is a different secure computation framework with different trust assumptions and much larger engineering scope.

### Custom gRPC TLS implementation

Rejected because it requires certificate distribution, identity mapping, channel reconfiguration, and possibly application code changes. It would also confound service identity with application-specific TLS engineering.

### Multi-region experiments

Rejected because they would introduce WAN latency, inter-region routing variability, and a fundamentally different topology question. That is not a minimal extension of the same-node AKS RQ1.5 design.

### Full service-mesh comparison study

Rejected because RQ2.1 is not trying to determine the globally best mesh. It is trying to determine the cost of securing the chosen AKS distributed inference deployment with a realistic, low-risk mechanism.

---

## 12. Implementation Roadmap

### Stage 1: Scope lock and configuration freeze

1. Freeze the primary RQ2.1 configuration as `chain_2svc`.
2. Freeze the mechanism as AKS managed Istio add-on in sidecar mode.
3. Create new RQ2.1 configs rather than editing RQ1.5 configs.

**Exit criterion:** the secure and plain configs differ only in mesh-related fields, namespaces, and measurement additions.

### Stage 2: Mesh smoke test

1. Provision the final RQ2.1 isolated-pool AKS contract: small system pool plus tainted `rq15pool` benchmark pool.
2. Enable AKS managed Istio on the cluster.
3. Label a disposable test namespace with the selected revision.
4. Deploy `chain_2svc` services with sidecars.
5. Keep the benchmark client outside the mesh.
6. Apply workload-scoped `PeerAuthentication` so only the downstream service requires mTLS.
7. Apply explicit proxy CPU and memory requests plus limits.
8. Ensure benchmark client and inference service pods select the benchmark pool and tolerate the benchmark-only taint.
9. Record mesh control-plane/system pod placement.
10. Run the formal `chain_2svc_mtls` infrastructure preflight gate.

**Exit criterion:**

- Service pods show `istio-proxy` containers.
- The client remains single-container and non-meshed.
- Same-node placement still holds inside the benchmark pool.
- Both application and proxy containers become Ready.
- No resource starvation or unschedulable pressure is observed.
- No avoidable managed-Istio control-plane deployment is colocated on the benchmark node.
- A short validation run proves that the latency pipeline still works.
- The downstream hop is confirmed to be mesh-protected.

### Stage 3: Instrumentation validation

1. Add host-side resource sampling during benchmark execution.
2. Extend deployment metadata capture for mesh revision, service accounts, sidecars, proxy resources, readiness timing, and policy resources.
3. Ensure resource outputs distinguish application container, `istio-proxy`, and total pod usage.
4. Optionally add a cold-channel handshake probe.

**Exit criterion:** a smoke run produces latency CSV, resource CSV, deployment metadata, and mesh metadata in one artifact bundle.

### Stage 4: Primary paired experiment

1. Run `chain_2svc_plain` and `chain_2svc_mtls` as interleaved rounds under the same isolated-pool AKS contract.
2. Keep same-node placement and the same image digest.
3. Verify preflight evidence that no avoidable managed-Istio control-plane deployment shares the benchmark node.
4. Export and merge artifacts using the existing RQ1.5-style directory structure.
5. Run the existing host-side latency analysis plus RQ2.1 supplemental summaries.

**Exit criterion:** primary pair produces stable matched results with interpretable latency and complexity deltas.

Stability here means not only that latency results are coherent, but also that the secure deployment shows reproducible container-level CPU and memory measurements, acceptable sidecar startup behavior, and no unresolved scheduling-pressure problems.

### Stage 5: Optional stress pair

1. Only if Stage 2 and Stage 4 both pass cleanly, repeat the paired design for `chain_5svc_plain` and `chain_5svc_mtls` under the same isolated-pool AKS contract.
2. Verify the same preflight condition: no avoidable managed-Istio control-plane deployment shares the benchmark node.
3. Treat the results as secondary stress evidence, not as the primary thesis claim.

**Exit criterion:** secondary stress data either confirms or bounds cumulative mesh-overhead behavior across deeper chains.

### Stage 6: Freeze and thesis integration

1. Freeze configs, manifest generation path, and mesh revision.
2. Treat only isolated-pool RQ2.1 artifacts as final thesis numbers.
3. Do not mix old single-pool RQ2.1 numbers with new isolated-pool numbers in final reporting.
4. Export final artifacts into a thesis-facing results directory.
5. Produce one concise summary table with:

- mean latency delta
- p95 delta
- application, proxy, and total-pod CPU overhead
- application, proxy, and total-pod memory overhead
- sidecar startup delay
- scheduling pressure summary
- deployment complexity scorecard

Handshake overhead may be included only if the optional probe was run and produced interpretable results.

6. Document threats-to-validity and out-of-scope attacker classes exactly as stated above.

**Exit criterion:** RQ2.1 can be written as a clean follow-on chapter to RQ1.5 without reopening any RQ1 architectural decision.

---

## Final Recommendation

If only one secure configuration is taken forward for RQ2.1, it should be **`chain_2svc` on AKS with the isolated two-pool contract, the Azure-native Istio add-on, and workload-scoped east-west mTLS**.

That choice gives the strongest thesis story, the smallest engineering delta from RQ1.5, and the clearest methodological interpretation.

`chain_5svc` is worth keeping only as a secondary stress check after the primary path is complete.
