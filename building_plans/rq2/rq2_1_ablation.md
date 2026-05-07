# RQ2.1 Ablation Plan

## Purpose

The frozen RQ2.1 result answers the thesis question at the bundle level: it measures
the overhead of adding the managed-Istio communication-hardening configuration to the
selected AKS microservice inference path. That configuration includes service identity,
sidecar proxying, Istio auto-mTLS behavior, strict downstream mTLS enforcement, and
AuthorizationPolicy.

This ablation study is a follow-up, not a replacement. Its purpose is to separate the
main contributors inside the RQ2.1 hardening bundle as far as the AKS managed-Istio
configuration allows.

The study asks:

> Which parts of the RQ2.1 hardened-path overhead appear to come from entering the
> service-mesh data path, requiring strict mTLS on the protected downstream workload,
> and enforcing inter-service AuthorizationPolicy?

## Why This Is Worth Measuring

The current RQ2.1 result is defensible, but it should not be phrased as "pure mTLS
cryptography adds 3.122 ms." The measured delta is the cost of a deployed security
configuration. Istio's sidecar data path adds proxying, socket handling, protocol
parsing, buffer copies, resource requests, and readiness behavior. Istio also enables
auto-mTLS between meshed workloads by default, so a sidecar-injected condition is not
necessarily a plaintext condition.

The ablation can add a sharper thesis insight:

> Most of the observed overhead may come from entering the service-mesh data path,
> while strict mTLS enforcement and AuthorizationPolicy add important security
> semantics with smaller incremental steady-state latency effects.

This is useful even if some adjacent deltas are small or statistically noisy, because
the operational overheads are expected to separate clearly.

## Scope

The primary ablation target is `chain_2svc`, because it is the selected AKS
microservice inference path and contains exactly one protected inter-service activation
transfer.

`chain_5svc` is optional and should be used only as an amplifier if `chain_2svc`
adjacent deltas are too small to interpret. It should remain secondary stress evidence,
not the headline result.

The ablation keeps fixed:

- ResNet-18 model and split after `layer2`
- AKS cluster family and isolated benchmark/system node-pool contract
- same-node service placement on the tainted benchmark pool
- same container image digest across conditions
- same gRPC protocol and service-side forwarding implementation
- same benchmark client outside the mesh unless explicitly stated otherwise
- same warmup, measured iterations, resource requests, and resource sampling cadence

## Primary Conditions

### C0: `plain_nonmesh`

Standard Kubernetes service-to-service communication with no service mesh injection.

Purpose:

- Baseline for the selected AKS chain.
- Measures the non-mesh gRPC chain cost.

Expected resources:

- no `istio-proxy` sidecars
- no mesh ServiceAccounts required for identity policy
- no PeerAuthentication
- no AuthorizationPolicy

Security semantics:

- no mesh identity
- no mesh-enforced mTLS
- no mesh AuthorizationPolicy

### C1: `mesh_default_no_authz`

Service namespace has managed-Istio sidecar injection enabled. Inference services use
explicit ServiceAccounts and injected sidecars. No workload-scoped strict
PeerAuthentication and no AuthorizationPolicy are applied.

Purpose:

- Measures the cost of entering the managed-Istio sidecar data path under default mesh
  behavior.
- Captures sidecar resource footprint, readiness delay, and control-plane operational
  complexity before explicit downstream authorization is added.

Important wording:

- Do not call this condition "sidecars without mTLS" unless validation proves plaintext.
- Istio auto-mTLS normally means traffic between meshed workloads uses mTLS by default.
- Safer thesis label: "mesh-default sidecar / auto-mTLS / no AuthZ".

Expected resources:

- two injected `istio-proxy` sidecars for `chain_2svc`
- two ServiceAccounts
- no workload-scoped strict PeerAuthentication
- no AuthorizationPolicy

Security semantics:

- service identity exists through mesh workload identity
- inter-sidecar traffic may use Istio auto-mTLS
- plaintext/non-mesh fallback may still be accepted by the destination unless stricter
  PeerAuthentication is applied
- no explicit inter-service allow policy

### C2: `mesh_strict_mtls_no_authz`

Same as C1, but add workload-scoped `STRICT` PeerAuthentication for the downstream
service. Do not add AuthorizationPolicy.

Purpose:

- Measures the incremental cost of requiring mTLS on the protected downstream workload
  beyond the mesh-default sidecar/auto-mTLS condition.
- Tests whether strict enforcement itself changes steady-state latency when the normal
  service1-to-service2 path was probably already using auto-mTLS.

Expected resources:

- two injected sidecars
- two ServiceAccounts
- namespace default PeerAuthentication, if retained for consistency
- one workload-scoped downstream `STRICT` PeerAuthentication
- no AuthorizationPolicy

Security semantics:

- downstream workload rejects plaintext/non-mesh direct access
- valid meshed upstream-to-downstream traffic succeeds
- no explicit identity allow-list beyond mTLS identity authentication

Expected result:

- latency delta from C1 to C2 may be small or near noise, because auto-mTLS may already
  encrypt the normal inter-service path in C1
- direct non-mesh denial should now pass for the downstream service

### C3: `mesh_strict_mtls_authz`

Current RQ2.1 hardened condition: sidecars, ServiceAccounts, workload-scoped strict
mTLS on the downstream service, and AuthorizationPolicy allowing only the expected
upstream service principal.

Purpose:

- Measures the incremental cost of identity-based inter-service authorization.
- Preserves the current RQ2.1 security contract.

Expected resources:

- two injected sidecars
- two ServiceAccounts
- downstream strict PeerAuthentication
- one AuthorizationPolicy selecting service2 and allowing only service1 principal

Security semantics:

- downstream service requires mTLS
- downstream service allows only the intended upstream service identity
- non-mesh direct access is denied
- unexpected meshed identity should be denied if tested

Expected result:

- latency delta from C2 to C3 may be very small
- operational complexity delta is clear: one additional AuthorizationPolicy and one
  additional validation gate

## Optional Diagnostic Condition

### C1b: `mesh_plaintext_no_authz`

This condition is optional and should be treated as a diagnostic control, not part of
the main thesis path. It attempts to measure sidecar proxying with plaintext
inter-service traffic by explicitly disabling mTLS.

Possible implementation:

- workload or namespace PeerAuthentication with `mtls.mode: DISABLE`
- DestinationRule for the service2 host with `trafficPolicy.tls.mode: DISABLE`
- validation that inter-service traffic is actually plaintext

Why optional:

- It adds Istio traffic-policy complexity.
- It is easier to misconfigure than the main four-condition ablation.
- It answers a more artificial question because the realistic managed-Istio default is
  auto-mTLS between meshed workloads.

Use this only if the thesis needs a true "proxy-only, no mTLS" diagnostic.

## Measurements

### Latency

Collect the same latency metrics already used in RQ2.1:

- mean end-to-end latency
- median end-to-end latency
- p95 and p99 end-to-end latency
- inferred non-compute/platform overhead
- per-hop `forward_ms`
- client serialization and deserialization timing
- total compute time

Primary adjacent deltas:

- mesh-default cost: `C1 - C0`
- strict enforcement cost: `C2 - C1`
- authorization-policy cost: `C3 - C2`
- total hardened cost: `C3 - C0`

### Resource Overhead

Collect per-condition resource samples:

- application-container CPU
- `istio-proxy` CPU
- total pod CPU
- application-container memory
- `istio-proxy` memory
- total pod memory
- sidecar request and limit totals
- service pod request and limit totals

Expected strongest signal:

- C1/C2/C3 should have clear sidecar memory and request overhead relative to C0.
- C2 and C3 may have similar runtime resource use, with C3 adding policy objects rather
  than large steady-state resource changes.

### Operational Overhead

Collect deployment and readiness metrics:

- schedule-to-ready duration
- pod scheduled timestamp
- app container start timestamp
- `istio-proxy` start timestamp
- sidecar readiness delay
- sidecar restart count
- Kubernetes object count by kind
- ServiceAccount count
- PeerAuthentication count
- AuthorizationPolicy count
- injected container count
- mesh control-plane pod count and placement

Expected strongest signal:

- C1 introduces most operational overhead: sidecars, explicit proxy resources, mesh
  revision labels, and control-plane dependency.
- C2 adds PeerAuthentication complexity and direct-denial validation.
- C3 adds AuthorizationPolicy complexity and identity-policy validation.

### Security Validation

Validation must be condition-specific.

For C0:

- no sidecars are present
- no mesh policy resources are present
- full-chain positive probe succeeds
- direct service2 access from a non-mesh debug/client pod is expected to succeed unless
  other Kubernetes policy blocks it

For C1:

- service pods have `istio-proxy`
- client pod does not have `istio-proxy`
- ServiceAccounts are present and used by the service pods
- no AuthorizationPolicy is present
- no workload-scoped strict PeerAuthentication is present
- full-chain positive probe succeeds
- direct non-mesh access to service2 may succeed because strict mTLS is not required

For C2:

- service pods have `istio-proxy`
- client pod remains non-meshed
- downstream strict PeerAuthentication is present and selects only service2
- no AuthorizationPolicy is present
- full-chain positive probe succeeds
- direct non-mesh access to service2 is denied

For C3:

- all C2 validations pass
- AuthorizationPolicy is present and selects service2
- AuthorizationPolicy allows only the service1 principal
- direct non-mesh access to service2 is denied
- optional: a meshed pod with an unexpected ServiceAccount is denied

## Experimental Design

Use a repeated, interleaved execution plan rather than running all C0 passes first,
then all C1 passes, and so on.

Recommended primary design:

- topology: `chain_2svc`
- conditions: C0, C1, C2, C3
- passes: 5
- measured iterations per condition per pass: 200
- total measured iterations per condition: 1000
- warmup iterations per condition execution: 50
- cooldown: 5 seconds
- order: seeded Latin-square or rotated order

Example five-pass order:

1. C0, C1, C2, C3
2. C1, C2, C3, C0
3. C2, C3, C0, C1
4. C3, C0, C1, C2
5. C0, C2, C1, C3

The exact order should be generated from a seed and recorded in `execution_order.json`.

## Analysis Outputs

Produce the following thesis-facing artifacts:

- `rq2_1_ablation_summary.md`
- `rq2_1_ablation_summary.json`
- `aggregated_results.csv`
- `raw_iterations.csv`
- `resource_summary.csv`
- `operational_overhead.json`
- per-condition static and runtime validation JSON

Required tables:

1. Raw latency by condition.
2. Adjacent latency deltas: C1-C0, C2-C1, C3-C2, C3-C0.
3. Resource overhead by condition.
4. Operational complexity by condition.
5. Security semantics and validation result by condition.

Recommended figure:

- stacked or waterfall latency-delta figure showing the adjacent deltas from C0 to C3

Important interpretation rule:

- If C2-C1 or C3-C2 is smaller than pass-to-pass noise, report it as small/not cleanly
  distinguishable rather than forcing a precise causal millisecond claim.

## What Each Result Would Show

If C1-C0 is large:

- The main cost of RQ2.1 comes from entering the service-mesh sidecar data path and
  carrying its resource/readiness footprint.

If C2-C1 is small:

- Strict PeerAuthentication mainly changes enforcement semantics for bypass/plaintext
  traffic, while the ordinary meshed service1-to-service2 path was already close to the
  final mTLS data path because of auto-mTLS.

If C3-C2 is small:

- AuthorizationPolicy adds a strong identity-based allow-list with little additional
  steady-state latency in this workload.

If C2-C1 or C3-C2 is measurable:

- The thesis can report a concrete incremental runtime cost for strict enforcement or
  policy evaluation, bounded to this AKS/Istio/workload configuration.

If all mesh conditions are close together:

- The practical conclusion is that the dominant runtime decision is whether to enter the
  mesh at all; strict mTLS and AuthZ then mainly strengthen semantics and operational
  complexity.

## Threats To Validity

- Istio auto-mTLS means C1 is not a pure "sidecar without mTLS" condition.
- Adjacent latency deltas may be smaller than cloud noise or pass-to-pass variation.
- gRPC channels are reused after warmup, so the benchmark mostly measures steady-state
  request cost, not repeated TLS handshake cost.
- The result is specific to AKS managed Istio add-on, sidecar mode, the selected mesh
  revision, same-node placement, and the ResNet-18 chain workload.
- AuthorizationPolicy behavior may be cheap in this simple service graph but costlier
  under larger policy sets or higher request concurrency.
- The ablation measures data-plane behavior and deployment complexity; it does not
  reduce trust in the mesh control plane or certificate authority.

## Implementation Plan

Current status:

- Step 1 is implemented for `chain_2svc` under `configs/rq2/2.1/ablation/`.
- Step 2 required no renderer change: the existing AKS manifest generator already
  supports mesh-enabled configs with no AuthorizationPolicy, mesh-enabled configs with
  no strict PeerAuthentication workloads, and strict PeerAuthentication without AuthZ.
- Generated manifests for C0-C3 have been validated for object counts, mesh revision
  labels, proxy annotations, ServiceAccounts, PeerAuthentication selectors, and the
  C3 service1-only AuthorizationPolicy principal.
- Step 3 is implemented in `scripts/run_rq21_ablation.py` as a separate four-condition
  runner with seeded/rotated execution order and adjacent-delta summaries.
- Step 4 is implemented with condition-specific static validation and runtime validation
  hooks. The live runtime validation expects full-chain success for all conditions,
  direct service2 access to succeed for C0/C1, and direct service2 access to be denied
  for C2/C3.
- Step 5 and Step 6 completed for `chain_2svc` on AKS on 2026-05-06. The full
  five-pass campaign produced artifacts under
  `results_exports/rq2_1_ablation_20260506_105639/`, with all validation gates and
  resource-metric completeness checks passing.

### Step 1: Add Configs

Create new configs under `configs/rq2/2.1/ablation/`:

- `rq2_1_ablation_chain2_plain_nonmesh.yaml`
- `rq2_1_ablation_chain2_mesh_default_no_authz.yaml`
- `rq2_1_ablation_chain2_mesh_strict_mtls_no_authz.yaml`
- `rq2_1_ablation_chain2_mesh_strict_mtls_authz.yaml`

Use distinct namespaces so artifacts and policies cannot leak between conditions.

### Step 2: Extend Manifest Generation If Needed

The existing AKS manifest generator already supports:

- mesh enablement
- namespace revision labels
- service accounts
- proxy resource annotations
- optional PeerAuthentication
- optional AuthorizationPolicy

Likely required additions:

- allow mesh-enabled configs with `authorization_policy.enabled: false`
- allow mesh-enabled configs with no strict PeerAuthentication workloads
- optionally emit DestinationRule only for the C1b plaintext diagnostic

### Step 3: Add Ablation Runner

Prefer a separate runner or mode rather than heavily mutating the frozen two-condition
RQ2.1 runner.

Candidate:

- `scripts/run_rq21_ablation.py`

The runner should support:

- arbitrary ordered condition keys
- seeded rotated execution order
- per-condition validation hooks
- per-condition resource sampling
- common image digest pinning
- common infrastructure provisioning/reuse
- merged adjacent-delta summaries

### Step 4: Add Validation Logic

Implement condition-specific validation:

- C0: prove no mesh artifacts
- C1: prove sidecars and ServiceAccounts, but no strict downstream policy and no AuthZ
- C2: prove strict downstream PeerAuthentication and no AuthZ
- C3: prove strict downstream PeerAuthentication plus expected AuthZ principal

Add optional mTLS evidence where practical:

- Envoy config inspection, if reliable
- Istio proxy metrics, if available
- direct non-mesh probe behavior
- optional debug HTTP/gRPC metadata is not required for the main thesis result

### Step 5: Smoke Run

Run one smoke pass with low measured iterations.

Exit criteria:

- all four conditions deploy
- all full-chain probes pass
- C2/C3 direct-denial probes pass
- C0/C1 direct behavior matches expectation
- resource samples include sidecars for C1-C3 and no sidecars for C0
- merged summary produces adjacent deltas

### Step 6: Full Chain-2 Campaign

Run the five-pass ablation campaign.

Freeze artifacts only if:

- all conditions complete all passes
- validation passes for all conditions
- resource metrics are complete
- same-node placement holds
- mesh control-plane isolation holds
- no policy/resource leakage occurs between condition namespaces

### Step 7: Optional Chain-5 Amplifier

Only run if the chain-2 adjacent deltas are too small to interpret or if the thesis
needs stress evidence.

Keep it explicitly secondary.

## Thesis Integration

Recommended placement:

- short subsection after the current RQ2.1 answer, or
- appendix section referenced from RQ2.1

Recommended wording:

> The main RQ2.1 result remains the bundle-level cost of the selected hardened
> configuration. The ablation suggests how that cost decomposes across mesh data-path
> entry, strict mTLS enforcement, and authorization policy. Because Istio uses auto-mTLS
> between meshed workloads, the mesh-default condition should not be interpreted as a
> plaintext sidecar-only baseline.

Promote the ablation into the main chapter only if the results are stable and the
adjacent deltas are easy to explain. Otherwise, use it as supporting evidence and keep
the frozen RQ2.1 bundle result as the headline answer.

## Final Recommendation

Implement the four primary conditions for `chain_2svc`. Do not start with the optional
plaintext diagnostic. The likely thesis payoff is high enough to justify the work, and
the scope remains controlled if the current RQ2.1 result stays as the main answer.
