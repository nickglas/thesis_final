# RQ2.1 mTLS Split-Point Sensitivity Plan

## Purpose

The frozen RQ2.1 result answers the thesis question at the selected-deployment level:
it measures the overhead of adding managed-Istio service identity, mTLS, and
AuthorizationPolicy to the AKS `chain_2svc` path selected for RQ2.1, with `chain_5svc`
as a deeper stress case.

This split-point sensitivity study is a follow-up, not a replacement. Its purpose is
to test whether the RQ2.1 hardened-path overhead changes when the two-service split
point moves through ResNet-18 and the protected inter-service activation tensor becomes
smaller.

The study asks:

> Does managed-Istio mTLS/AuthZ overhead decrease at later split points, or is the
> measured overhead mostly a fixed per-boundary service-mesh data-path cost?

## Why This Is Worth Measuring

RQ1.1 showed that activation tensors shrink through the network: early split points
transfer large feature maps, while later split points transfer smaller tensors. RQ2.1
then showed that adding the managed-Istio hardening bundle introduces measurable
latency, resource, and operational overhead on the selected AKS chain.

The current RQ2.1 `chain_2svc` versus `chain_5svc` comparison is useful, but it mixes
multiple factors:

- the number of protected service boundaries
- the number of injected sidecars
- cumulative forwarding depth
- cumulative transferred activation volume

This new experiment isolates a different question. It keeps exactly one protected
inter-service boundary and varies only the model split point. That makes it the cleanest
way to connect the RQ1.1 activation-size result to the RQ2.1 security-hardening result.

The payoff is useful in either direction:

- If mTLS/AuthZ overhead decreases at later split points, the thesis can argue that
  security hardening amplifies poor split choices with larger activation payloads.
- If mTLS/AuthZ overhead is roughly flat, the thesis can argue that the managed-Istio
  cost is mostly per-boundary/platform cost rather than payload-size cost.
- If the pattern is noisy or non-monotonic, the thesis can report that no clear
  payload-size trend was observed and lean on the ablation result that the mesh data
  path dominates.

## Scope

The experiment is limited to two-service chains. It must not become a new full
architecture search and it must not repeat the four-condition ablation across every
split point.

Fixed across all conditions:

- ResNet-18 model, pretrained weights, CPU, FP32, input shape `1 x 3 x 224 x 224`
- two-service chain topology
- one protected inter-service boundary
- same AKS isolated benchmark/system node-pool contract as final RQ2.1
- same-node placement on the tainted benchmark node pool
- same image digest across all conditions
- same gRPC and Protocol Buffers application protocol
- benchmark client outside the mesh
- service namespace meshed only for mTLS/AuthZ conditions
- same managed AKS Istio add-on revision
- same proxy resource requests and limits
- same warmup, measured iterations, cooldown, and resource sampling cadence
- same security validation gates as the final RQ2.1 hardened condition

Changed variable:

- split point: after `layer1`, `layer2`, `layer3`, or `layer4`

Security comparison within each split:

- plain non-mesh AKS chain
- managed-Istio mTLS/AuthZ chain

Important scope note:

`split_after_layer4` is included as a diagnostic endpoint because it has the smallest
activation tensor. It remains compute-degenerate as a microservice decomposition and
must not be promoted as a deployment candidate even if its raw latency is low.

## Condition Matrix

Each split point receives a matched plain/mTLS pair.

| Split key | Chain split point | Protected inter-service tensor | Protected-hop activation size | Plain condition | mTLS/AuthZ condition |
| --- | --- | --- | ---: | --- | --- |
| `l1` | `layer1` | `64 x 56 x 56` | 784 KiB | `chain_2svc_split_l1_plain` | `chain_2svc_split_l1_mtls` |
| `l2` | `layer2` | `128 x 28 x 28` | 392 KiB | `chain_2svc_split_l2_plain` | `chain_2svc_split_l2_mtls` |
| `l3` | `layer3` | `256 x 14 x 14` | 196 KiB | `chain_2svc_split_l3_plain` | `chain_2svc_split_l3_mtls` |
| `l4` | `layer4` | `512 x 7 x 7` | 98 KiB | `chain_2svc_split_l4_plain` | `chain_2svc_split_l4_mtls` |

The protected-hop activation size is the main thesis-facing payload-size variable. The
runner should still record `total_activation_bytes`, but interpretation must distinguish
the protected inter-service activation from total transferred bytes if the pipeline also
counts the client-to-service1 input payload.

## Hypotheses

H1: Raw split-chain latency should generally improve as the split moves later and the
protected inter-service activation tensor shrinks, subject to compute-placement effects.

H2: Absolute mTLS/AuthZ overhead may decrease for later split points if sidecar and mTLS
processing are meaningfully payload-sensitive for this workload.

H3: If the absolute mTLS/AuthZ delta is roughly flat across split points, then the
managed-Istio overhead behaves mainly like a fixed per-boundary/platform cost.

H4: The latest split may show low raw latency but remains structurally compute-degenerate,
so suitability and security-overhead sensitivity must be discussed separately.

## Measurements

### Latency

Collect the same latency metrics already used in RQ2.1:

- mean end-to-end latency
- median end-to-end latency
- p95 and p99 end-to-end latency
- paired mean latency delta: `mtls - plain`
- paired mean latency delta percentage
- paired p95 latency delta
- inferred non-compute/platform overhead
- total compute time
- protected-hop `forward_ms`
- per-hop `forward_ms` for all active hops
- protected-hop activation bytes
- total activation bytes

Primary latency comparison:

- for each split, compare its mTLS/AuthZ condition against its matched plain condition

Secondary latency comparison:

- compare mTLS/AuthZ deltas across split points against protected-hop activation size

### Resource Overhead

Collect per-condition resource samples:

- application-container CPU
- `istio-proxy` CPU
- total pod CPU
- application-container memory
- `istio-proxy` memory
- total pod memory
- sidecar sample row count
- resource sample count
- resource passes covered
- sidecar request and limit totals

Expected strongest signal:

- every mTLS/AuthZ condition should show sidecar CPU and memory rows
- every plain condition should have zero `istio-proxy` rows
- resource overhead may be similar across split points if the proxy cost is mostly
  fixed per injected service rather than payload-size dependent

### Operational Overhead

Collect the same operational metrics used in the RQ2.1 paired runner:

- schedule-to-ready duration
- pod scheduled timestamp
- app container start timestamp
- sidecar start timestamp
- sidecar readiness delay
- sidecar restart count
- failed scheduling events
- Kubernetes object count by kind
- ServiceAccount count
- PeerAuthentication count
- AuthorizationPolicy count
- injected container count
- mesh control-plane pod count and placement

Expected strongest signal:

- operational complexity should be nearly identical across mTLS split points because
  every condition has the same two-service mesh shape
- any large difference should be treated as a validity issue unless explained by
  deployment events or resource pressure

### Security Validation

Validation must be condition-specific.

For each plain condition:

- no `istio-proxy` sidecars are present
- no mesh namespace revision label is active
- no PeerAuthentication or AuthorizationPolicy is present
- full-chain positive probe succeeds
- resource samples contain no `istio-proxy` rows

For each mTLS/AuthZ condition:

- service pods have injected `istio-proxy` sidecars
- benchmark client remains outside the mesh
- service pods use explicit ServiceAccounts
- downstream service has workload-scoped `STRICT` PeerAuthentication
- AuthorizationPolicy selects service2 and allows only the service1 principal
- full-chain positive probe through service1 succeeds
- direct non-mesh probe to protected service2 is denied
- resource samples contain `istio-proxy` rows for both service pods
- mesh control-plane pods remain off the benchmark node when control-plane isolation is
  required

## Experimental Design

Use a repeated, interleaved paired design. Do not run all plain conditions first and
all mTLS/AuthZ conditions later.

Recommended primary design:

- split points: `layer1`, `layer2`, `layer3`, `layer4`
- security modes: `plain`, `mtls`
- total conditions: 8
- passes: 5
- warmup iterations per condition execution: 50
- measured iterations per condition execution: 200
- total measured iterations per condition after merge: 1000
- cooldown: 5 seconds
- order seed: 42
- execution order: seeded split order with alternating plain/mTLS order inside each
  split pair

Example order policy:

1. Build a seeded split order for pass 1.
2. Rotate the split order in later passes.
3. Alternate the within-pair security order so some passes run `plain` first and some
   passes run `mtls` first.
4. Record the exact order in `execution_order.json`.

The paired delta for each split must be computed within pass:

```text
delta(split, pass) = mean_latency(split, mtls, pass) - mean_latency(split, plain, pass)
```

The thesis-facing per-split delta is the aggregate of the five pass-level deltas and
the merged condition samples.

## Analysis Outputs

Produce artifacts under:

```text
results/rq2_1_mtls_split_<timestamp>/
```

Required files:

- `rq2_1_mtls_split_run_metadata.json`
- `execution_order.json`
- `effective_configs/*.yaml`
- per-condition manifests
- per-condition static validation JSON
- per-condition runtime validation JSON
- `raw_iterations.csv`
- `aggregated_results.csv`
- `split_sensitivity_summary.json`
- `split_sensitivity_summary.csv`
- `split_sensitivity_summary.md`
- `resource_summary_by_split.csv`
- `operational_overhead_by_split.json`

Required thesis-facing tables:

1. Raw latency by split and security mode.
2. Per-split mTLS/AuthZ latency deltas: mean delta, delta percent, p95 delta, and
   non-compute/platform delta.
3. Activation sanity table: protected-hop activation bytes and recorded total activation
   bytes for each split/security pair.
4. Resource overhead by split: sidecar CPU, total pod CPU delta, sidecar memory, and
   total pod memory delta.
5. Operational complexity by split: additional sidecars, ServiceAccounts,
   PeerAuthentications, AuthorizationPolicies, and schedule-to-ready delta.
6. Security validation summary by split.

Recommended figures:

- mTLS/AuthZ mean and p95 latency overhead by split point
- mTLS/AuthZ mean latency overhead versus protected-hop activation size
- optional raw plain versus mTLS latency by split point

Trend analysis should be descriptive. With only four split points, avoid presenting a
strong statistical model unless the trend is visually and numerically clear. A simple
correlation or fitted line can be included as supporting evidence, but the thesis claim
should remain qualitative and bounded.

## Interpretation Rules

If overhead decreases as split points move later:

- interpret the managed-Istio hardening cost as partly payload-sensitive
- state that security hardening amplifies the penalty of early, large-activation splits
- keep the claim bounded to this AKS managed-Istio sidecar workload

If overhead is approximately flat:

- interpret the managed-Istio hardening cost as mostly fixed per protected boundary
- connect this to the RQ2.1 ablation result that mesh data-path entry dominates
- state that split choice affects raw inference latency, but not much of the security
  delta itself

If overhead is noisy or non-monotonic:

- report that no clear activation-size sensitivity was observed
- do not force a monotonic conclusion
- use the result as supporting evidence that mTLS/AuthZ overhead is not explained by
  activation size alone

If `split_after_layer4` is fastest:

- report it as the low-payload diagnostic endpoint
- preserve the compute-degeneracy interpretation from RQ1.1
- do not revise the selected deployment solely because the downstream payload is small

## Threats To Validity

- The experiment uses managed AKS Istio sidecar mode, so results may not generalize to
  self-managed Istio, Ambient mode, Linkerd, eBPF-based meshes, or application-managed
  TLS.
- gRPC channels are reused after warmup, so the benchmark measures steady-state request
  overhead, not repeated TLS handshake cost.
- The benchmark client remains outside the mesh, so the measured hardening path is the
  inter-service boundary, not external ingress security.
- Small per-split differences may be masked by cloud noise or pass-to-pass variation.
- `split_after_layer4` is useful for payload sensitivity but remains compute-degenerate.
- The pipeline's `total_activation_bytes` may include client ingress as well as the
  protected inter-service activation; analysis must identify the protected hop.
- The result is specific to ResNet-18, FP32 CPU inference, same-node AKS placement, and
  the selected managed-Istio revision.
- AuthorizationPolicy cost is measured for a simple service graph and small policy set;
  larger policy graphs could behave differently.

## Implementation Plan

Current status:

- Design only. No configs, runner, tests, or final artifacts have been created for this
  split-point sensitivity experiment yet.

### Step 1: Add Configs

Create new configs under:

```text
configs/rq2/2.1/mtls_split/
```

Required config files:

- `rq2_1_mtls_split_l1_plain.yaml`
- `rq2_1_mtls_split_l1_mtls.yaml`
- `rq2_1_mtls_split_l2_plain.yaml`
- `rq2_1_mtls_split_l2_mtls.yaml`
- `rq2_1_mtls_split_l3_plain.yaml`
- `rq2_1_mtls_split_l3_mtls.yaml`
- `rq2_1_mtls_split_l4_plain.yaml`
- `rq2_1_mtls_split_l4_mtls.yaml`

Each file should differ only in:

- condition name
- namespace and client namespace
- `chain_split_points`
- `security_condition`
- mesh fields for mTLS/AuthZ conditions

The `l2` pair should reproduce the current RQ2.1 `chain_2svc` split after `layer2`
contract, apart from condition names and namespaces.

### Step 2: Add Runner

Prefer a separate runner rather than heavily mutating the frozen paired runner.

Candidate:

```text
scripts/run_rq21_mtls_split.py
```

The runner should reuse `scripts/run_rq21_paired_benchmark.py` where possible and add:

- four split-specific condition pairs
- seeded rotated split order
- alternating plain/mTLS order within each split pair
- per-split paired-delta summaries
- protected-hop activation reporting
- condition-specific validation using the existing plain and mTLS checks
- resource completeness gates for all eight conditions

The runner should preserve the existing RQ2.1 behavior:

- common infrastructure provisioning/reuse
- common image digest pinning
- mesh enablement and revision capture
- resource sampling
- security preflight and runtime validation
- same-node placement and control-plane isolation checks

### Step 3: Add Tests

Add tests similar to the existing paired and ablation tests.

Candidate:

```text
tests/test_rq21_mtls_split.py
```

Test coverage should include:

- config matrix contains exactly four split pairs
- each pair has matching model, resources, image, placement, benchmark cadence, and
  service count
- execution order is seeded, rotated, and records both security orders across passes
- plain conditions reject unexpected sidecar resource rows
- mTLS conditions require sidecar resource rows for both service pods
- mTLS validation expects strict downstream PeerAuthentication and service1-only AuthZ
- per-split paired deltas are computed correctly
- activation sanity distinguishes protected-hop activation bytes from total activation
  bytes

### Step 4: Generate-Only Validation

Run the runner in generate-only mode.

Exit criteria:

- all eight effective configs are written
- all eight manifest sets render
- plain manifests contain no mesh artifacts
- mTLS manifests contain namespace revision labels, ServiceAccounts, proxy annotations,
  downstream strict PeerAuthentication, and AuthorizationPolicy
- object counts match expectations

### Step 5: Smoke Run

Run one smoke pass with reduced measured iterations.

Exit criteria:

- all eight conditions deploy
- all full-chain positive probes pass
- all mTLS direct-denial probes pass
- all plain direct behavior matches expectation
- resource samples are present
- sidecar rows appear only in mTLS conditions
- same-node placement holds
- mesh control-plane isolation holds
- split summary is produced

### Step 6: Full Campaign

Run the five-pass split sensitivity campaign.

Freeze artifacts only if:

- all eight conditions complete all passes
- validation passes for all mTLS and plain conditions
- resource metrics are complete
- image digest is identical across conditions
- no policy/resource leakage occurs between namespaces
- activation bytes match expectations for each split
- execution order and run metadata are preserved

### Step 7: Thesis Integration

Recommended placement:

- short subsection inside RQ2.1 after the ablation subsection, or
- appendix section referenced from the RQ2.1 interpretation

Recommended subsection title:

```text
Split-Point Sensitivity of mTLS/AuthZ Overhead
```

Recommended wording:

> The main RQ2.1 result remains the bundle-level cost of hardening the selected AKS
> chain. This sensitivity experiment tests whether that cost changes when the protected
> inter-service activation payload shrinks across the same coarse split points studied
> in RQ1.1.

Promote the sensitivity experiment into the main RQ2.1 chapter only if the full campaign
passes validation and the result adds a clear interpretation. If the deltas are noisy,
keep the result as supporting evidence and avoid letting it distract from the frozen
RQ2.1 paired result and the ablation.

## Final Recommendation

Implement the split-point sensitivity study as a compact eight-condition follow-up:
four two-service split points, each with a matched plain and mTLS/AuthZ condition.

Do not repeat the full ablation across split points. The existing ablation already
explains the hardening bundle. This experiment should answer one focused question:
whether the final RQ2.1 mTLS/AuthZ overhead is sensitive to the size and location of the
protected activation transfer.
