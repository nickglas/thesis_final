# RQ2.1b Experimental Design

## Multi-Node Sensitivity Validation for the RQ2.1 mTLS/AuthZ Pair

---

## Design Recommendation

**Decision: add RQ2.1b as a focused multi-node sensitivity stage for the
existing RQ2.1 `chain_2svc` plain versus mTLS/AuthZ pair.**

**Do not make multi-node placement the default RQ2.1 result.** The current
single-node RQ2.1 pair remains the primary causal result because it isolates the
incremental cost of the security mechanism from the cost of crossing AKS nodes.

RQ2.1b has a narrower role: measure whether the mTLS/AuthZ overhead observed in
the controlled single-node RQ2.1 experiment changes when the protected
service-to-service hop is forced across a node boundary.

### Why this is a sensitivity stage and not a replacement

- **The primary RQ2.1 answer stays causally clean.** Single-node placement holds
  service placement constant and attributes the paired delta mainly to entering
  the mesh, mTLS enforcement, AuthorizationPolicy, sidecars, and their resource
  footprint.
- **Multi-node placement is production-relevant but confounded.** It includes
  cross-node network latency, CNI behavior, scheduling variance, and sidecar
  data-path effects. That makes it valuable as sensitivity evidence, but weaker
  as the default causal estimate.
- **The new result connects RQ1 and RQ2.** RQ1.5b showed that node placement can
  materially increase chain latency. RQ2.1b asks whether the same placement
  effect amplifies the cost of service-mesh hardening.
- **The matrix stays bounded.** Only the selected RQ2.1 pair is repeated. The
  split-point sensitivity and ablation studies remain single-node unless a
  separate thesis need appears.

---

## 1. Research Question

> **RQ2.1b:** When the protected RQ2.1 service-to-service hop is forced across
> AKS worker nodes, how does the incremental latency and resource overhead of
> managed-Istio mTLS/AuthZ compare with the same RQ2.1 pair under same-node
> placement?

### Operative phrases

- **"protected RQ2.1 service-to-service hop"** means the existing `chain_2svc`
  path: service1 calls service2, and the service2 workload is protected by
  workload-scoped STRICT mTLS plus AuthorizationPolicy allowing only the
  service1 principal.
- **"forced across AKS worker nodes"** means service1 and service2 must run on
  distinct benchmark-pool nodes. The benchmark client should also run on a
  dedicated node so the client-to-service1 hop is held constant across the
  plain and secure multi-node pair.
- **"compare with the same RQ2.1 pair under same-node placement"** means RQ2.1b
  is interpreted through deltas, not absolute latency alone.

### What RQ2.1b is NOT

- **Not a new split-point study.** The default target is the existing RQ2.1
  `chain_2svc` split after `layer2`, because that is the current paired,
  ablation, and thesis-facing RQ2.1 contract.
- **Not a replacement for RQ2.1.** The same-node result remains the primary
  estimate of the security mechanism's overhead.
- **Not a full chain-family rerun.** Do not repeat `chain_3svc`,
  `chain_4svc`, or `chain_5svc` unless a later thesis decision explicitly
  expands scope.
- **Not a multi-region or WAN study.** All nodes stay in one AKS cluster, one
  region, and one virtual network.
- **Not a mesh comparison.** The mechanism remains the Azure-native managed
  Istio add-on in sidecar mode.

---

## 2. Dependency on Earlier Stages

| Stage | Status | Role in RQ2.1b |
| --- | --- | --- |
| RQ1.4/RQ1.5 | Frozen | Defines the Kubernetes and AKS chain execution model. |
| RQ1.5b | Frozen | Shows that multi-node placement can add meaningful latency and motivates RQ2.1b. |
| RQ2.1 paired | Primary | Supplies the same-node plain versus mTLS/AuthZ security overhead baseline. |
| RQ2.1 split sensitivity | Secondary | Stays single-node; provides payload-size context but is not repeated here. |
| RQ2.1 ablation | Secondary | Stays single-node; explains which parts of the hardening bundle dominate. |
| RQ2.2 | Separate | Confidential-compute placement remains its own question and is not mixed into RQ2.1b. |

### Inherited unchanged

- ResNet-18 model, pretrained weights, CPU FP32 execution.
- `chain_2svc` topology with split after `layer2`.
- gRPC plus Protocol Buffers application protocol.
- Benchmark client outside the mesh.
- Service namespace meshed only for the mTLS/AuthZ condition.
- Managed AKS Istio add-on in sidecar mode.
- Workload-scoped downstream STRICT `PeerAuthentication`.
- Downstream `AuthorizationPolicy` allowing only the service1 principal.
- Explicit per-service Kubernetes `ServiceAccount` identities.
- Same image digest across the paired plain and secure conditions.
- Same warmup, measured iterations, cooldown, resource sampling, and pass count
  as the final RQ2.1 paired run.

### Changed variable

Only placement changes:

- from `strict_same_node`
- to `multi_node_anti_affinity`

The security comparison remains exactly:

- plain non-mesh `chain_2svc`
- managed-Istio mTLS/AuthZ `chain_2svc`

---

## 3. Condition Matrix

RQ2.1b adds the two multi-node cells needed to complete a clean placement
sensitivity comparison.

| Placement | Plain condition | mTLS/AuthZ condition | Interpretation |
| --- | --- | --- | --- |
| Same-node | Existing `chain_2svc_plain` | Existing `chain_2svc_mtls` | Primary RQ2.1 causal security overhead. |
| Multi-node | New `chain_2svc_plain_multinode` | New `chain_2svc_mtls_multinode` | RQ2.1b placement sensitivity. |

### Required new configs

Create the new configs under a separate subdirectory so they cannot be confused
with the primary RQ2.1 same-node configs:

```text
configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml
configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml
```

These should be cloned from the final same-node RQ2.1 `chain_2svc` configs and
changed only where placement and naming require it.

### Minimal config delta

For both new configs:

```yaml
kubernetes:
  namespace: "rq21b-chain2-plain"        # or rq21b-chain2-mtls
  client_namespace: "rq21b-client-plain" # or rq21b-client-mtls
  placement:
    strategy: "multi_node_anti_affinity"
    require_same_node: false
    fail_if_not_colocated: false
    require_distinct_nodes: true
    require_dedicated_client_node: true
    min_nodes: 3
    node_pool: "rq21bpool"
    node_selector:
      workload: "benchmark"
    tolerations:
      - key: "workload"
        operator: "Equal"
        value: "benchmark"
        effect: "NoSchedule"
    require_control_plane_isolation: true
```

For the mTLS/AuthZ config, keep the existing mesh block intact except for names
that must match the new namespace and condition names.

---

## 4. Placement Contract

### Same-node baseline recap

The primary RQ2.1 pair uses one benchmark-pool node:

```text
benchmark node A:
  benchmark-client
  service1
  service2
```

This isolates mesh/security overhead because both plain and mTLS/AuthZ execute
the service graph without inter-node data-plane traffic.

### Multi-node RQ2.1b contract

RQ2.1b uses three benchmark-pool nodes:

```text
benchmark node A:
  benchmark-client

benchmark node B:
  service1

benchmark node C:
  service2
```

This deliberately makes the normal data path:

```text
client -> service1 -> service2 -> service1 -> client
```

cross node boundaries in both the plain and mTLS/AuthZ conditions. The main
protected hop, service1 to service2, must cross from node B to node C.

### Why the client gets a dedicated node

Putting the client on a dedicated node avoids accidentally giving one condition
a cheaper client-to-service1 path. It also mirrors the RQ1.5b sensitivity
principle: every active communication boundary that can cross a node should be
made explicit and verified.

The cost of the client-to-service1 boundary is not the primary RQ2.1b question,
but it is common to both conditions. The paired delta still isolates the
additional cost of adding the security mechanism under multi-node placement.

---

## 5. Infrastructure Contract

### Cluster shape

| Pool | Count | SKU | Purpose |
| --- | ---: | --- | --- |
| `systempool` | 1 | `Standard_D2s_v3` | AKS system and managed-Istio control-plane workloads. |
| `rq21bpool` | 3 | `Standard_D8s_v3` | Benchmark client, service1, and service2 on distinct nodes. |

This is the smallest AKS shape that preserves the dedicated-client multi-node
contract for `chain_2svc`.

### Quota footprint

Approximate DSv3-family requirement:

```text
1 x Standard_D2s_v3  =  2 vCPU
3 x Standard_D8s_v3  = 24 vCPU
total                = 26 vCPU
```

Check both total regional vCPU quota and DSv3-family quota before provisioning.

### Cost posture

The RQ2.1b run is intentionally smaller than RQ1.5b. It needs three benchmark
nodes rather than six because it tests only `chain_2svc`, not `chain_5svc`.

Use the same auto-destroy policy as the other AKS building plans:

- destroy resource group on success
- destroy resource group on failure after diagnostics are captured
- do not leave idle AKS infrastructure running

---

## 6. Runner and Code Reuse Plan

### Existing pieces to reuse

| Artifact | Reuse | Note |
| --- | --- | --- |
| `k8s/aks/generate_aks_manifests.py` | High | Already supports `multi_node_anti_affinity`. |
| `src/benchmark/config.py` | High | Already models `require_distinct_nodes`, `require_dedicated_client_node`, and `min_nodes`. |
| `src/benchmark/deployment_metadata.py` | High | Reuse `validate_multi_node_placement()`. |
| `scripts/run_rq21_paired_benchmark.py` | Medium-High | Best orchestration base, but validation must become placement-aware. |
| `scripts/run_rq21_fully_controlled.py` | Medium | Reuse provisioning and mesh enablement helpers. |
| `scripts/sample_k8s_resources.py` | High | Same resource-sampling contract as RQ2.1. |

### Required runner refinement

The current RQ2.1 paired runner assumes the final same-node contract. For
RQ2.1b it must become placement-aware:

1. Permit `--node-count 3` when both configs use
   `placement.strategy=multi_node_anti_affinity`.
2. Require `placement.min_nodes >= 3`.
3. Require `placement.require_distinct_nodes=true`.
4. Require `placement.require_dedicated_client_node=true`.
5. Do not run the same-node runtime checks for the multi-node configs.
6. Instead, validate that service pods are on distinct nodes and the client node
   is separate from all service nodes.
7. Write a `multi_node_validation` block into the merged artifact set.
8. Prefer a distinct output prefix such as:

```text
results/rq2_1b_multinode_<timestamp>/
```

If keeping the existing paired runner output prefix temporarily, the final
artifact directory must still include an explicit experiment signature:

```json
{
  "signature": "rq2_1b_multinode",
  "stage": "RQ2.1b",
  "mode": "multi_node",
  "placement_strategy": "multi_node_anti_affinity"
}
```

### Validation function split

The runner should branch by placement mode:

```text
strict_same_node:
  existing RQ2.1 colocated service/client validation

multi_node_anti_affinity:
  service1 node != service2 node
  client node != service1 node
  client node != service2 node
  all node names known
```

This keeps both experiments fail-closed without weakening the original RQ2.1
same-node checks.

---

## 7. Measurement Contract

Use the same measured quantities as the final RQ2.1 paired run.

### Primary metrics

- mean end-to-end latency
- p95 end-to-end latency
- paired pass-level mean delta: `mtls - plain`
- paired pass-level delta percentage
- inferred non-compute/platform overhead
- total compute time
- per-hop `forward_ms`
- application-container CPU and memory
- `istio-proxy` CPU and memory
- total pod CPU and memory
- sidecar startup delay
- deployment complexity delta

### Additional placement metrics

RQ2.1b must report:

- client node name
- service1 node name
- service2 node name
- whether service nodes are distinct
- whether the client node is dedicated
- number of benchmark-pool nodes requested
- number of benchmark-pool nodes observed Ready
- whether avoidable managed-Istio control-plane pods share the benchmark pool

### Required security validation

For the plain multi-node condition:

- no mesh namespace revision label
- no `istio-proxy` sidecars
- no `PeerAuthentication`
- no `AuthorizationPolicy`
- full chain succeeds
- service1 and service2 are on distinct nodes
- client is on a dedicated node

For the mTLS/AuthZ multi-node condition:

- service pods have injected `istio-proxy` sidecars
- benchmark client remains outside the mesh
- service pods use explicit ServiceAccounts
- downstream service has workload-scoped STRICT mTLS
- downstream AuthorizationPolicy allows only the service1 principal
- direct non-mesh probe to protected service2 is denied
- service1 and service2 are on distinct nodes
- client is on a dedicated node
- resource samples contain `istio-proxy` rows for both services

---

## 8. Analysis Model

The analysis should not read RQ2.1b as "the new RQ2.1 number." It should read it
as a four-cell decomposition.

Let:

```text
P_s = plain same-node mean latency
M_s = mTLS/AuthZ same-node mean latency
P_m = plain multi-node mean latency
M_m = mTLS/AuthZ multi-node mean latency
```

Then report:

```text
Security overhead, same-node       = M_s - P_s
Placement overhead, plain          = P_m - P_s
Security overhead, multi-node      = M_m - P_m
Placement overhead, mTLS/AuthZ     = M_m - M_s
Security-placement interaction     = (M_m - P_m) - (M_s - P_s)
```

### Thesis interpretation

The key RQ2.1b quantity is the interaction term.

- If it is near zero, then mTLS/AuthZ overhead is mostly additive and does not
  materially worsen when the service boundary crosses nodes.
- If it is positive and stable, then cross-node placement amplifies the
  security overhead.
- If it is negative or noisy, then the thesis should avoid an amplification
  claim and report that multi-node placement increases total latency while the
  incremental security delta remains bounded by measurement variability.

### Reporting table

Minimum thesis-facing table:

| Comparison | Formula | Mean delta ms | Delta percent | p95 delta ms | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| Security, same-node | `M_s - P_s` | TBD | TBD | TBD | Primary RQ2.1 security overhead. |
| Placement, plain | `P_m - P_s` | TBD | TBD | TBD | Cost of crossing nodes without mesh security. |
| Security, multi-node | `M_m - P_m` | TBD | TBD | TBD | Security overhead under cross-node placement. |
| Placement, mTLS/AuthZ | `M_m - M_s` | TBD | TBD | TBD | Placement cost when security is enabled. |
| Interaction | `(M_m - P_m) - (M_s - P_s)` | TBD | TBD | TBD | Whether placement amplifies security overhead. |

---

## 9. Run Procedure

The final command should mirror the RQ2.1 paired runner, but with the multi-node
configs and three benchmark nodes.

Example command after the runner accepts placement-aware validation:

```pwsh
python scripts/run_rq21_paired_benchmark.py `
  --plain-config configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml `
  --mtls-config configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml `
  --topology chain2 `
  --resource-group rg-thesis-rq21b `
  --cluster-name thesis-rq21b `
  --nodepool rq21bpool `
  --node-count 3 `
  --system-nodepool systempool `
  --system-node-count 1 `
  --paired-passes 5 `
  --order seeded `
  --order-seed 42 `
  --provision --push --build `
  --destroy-infrastructure-on-success `
  --destroy-infrastructure-on-failure
```

If an image digest has already been frozen, prefer `--image-ref <digest>` over a
new build so the multi-node result differs only by placement.

### Smoke run

Before the full run:

```pwsh
python scripts/run_rq21_paired_benchmark.py `
  --plain-config configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml `
  --mtls-config configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml `
  --topology chain2 `
  --resource-group rg-thesis-rq21b-smoke `
  --cluster-name thesis-rq21b-smoke `
  --nodepool rq21bpool `
  --node-count 3 `
  --paired-passes 1 `
  --smoke `
  --provision --push --build `
  --destroy-infrastructure-on-success `
  --destroy-infrastructure-on-failure
```

The smoke run must prove placement, mesh validation, resource sampling, and
artifact export before the full measured run is attempted.

---

## 10. Required Artifacts

Produce artifacts under:

```text
results/rq2_1b_multinode_<timestamp>/
```

Required files:

- `raw_iterations.csv`
- `paired_summary.json`
- `paired_summary.csv`
- `paired_summary.md`
- `aggregated_results.md`
- `resource_samples.csv`
- `deployment_metadata.json`
- `environment.json`
- `execution_order.json`
- `security_validation.json` or condition-specific validation summaries
- `multi_node_validation.json`
- effective plain config
- effective mTLS/AuthZ config
- generated manifests for both conditions

The artifact set is incomplete if service node placement is missing or if
multi-node validation cannot prove distinct service nodes and a dedicated client
node.

---

## 11. Implementation Roadmap

### Stage 1: Scope lock

1. Confirm RQ2.1b repeats only the `chain_2svc` plain versus mTLS/AuthZ pair.
2. Confirm the split remains the current RQ2.1 split after `layer2`.
3. Confirm same-node RQ2.1 remains the headline security-overhead result.

**Exit criterion:** no split-point, chain-depth, mesh, or RQ2.2 scope changes
are bundled into RQ2.1b.

### Stage 2: Config pair

1. Add the two RQ2.1b multi-node configs.
2. Set `multi_node_anti_affinity` placement in both configs.
3. Set `min_nodes: 3`, `require_distinct_nodes: true`, and
   `require_dedicated_client_node: true`.
4. Keep image, resources, mesh policy, benchmark parameters, and service graph
   aligned with the primary RQ2.1 configs.

**Exit criterion:** a config diff shows only naming, namespace, nodepool, and
placement differences relative to the existing final RQ2.1 pair.

### Stage 3: Placement-aware runner update

1. Teach the RQ2.1 paired runner to classify the placement mode from both
   configs.
2. Relax the isolated-pool `node_count == 1` check only when both configs use
   `multi_node_anti_affinity`.
3. Add the multi-node runtime validation branch.
4. Preserve the original same-node validation branch unchanged.
5. Emit `rq2_1b_multinode` experiment signature metadata.

**Exit criterion:** unit tests or smoke validation prove same-node configs still
fail if colocated placement is broken, while multi-node configs fail if distinct
placement is broken.

### Stage 4: Smoke validation

1. Provision one system node and three benchmark nodes.
2. Deploy the plain and mTLS/AuthZ multi-node pair with one smoke pass.
3. Validate placement, sidecar injection, security policy, resource sampling,
   and artifact export.
4. Destroy infrastructure after diagnostics are collected.

**Exit criterion:** smoke artifacts contain known node names for client,
service1, and service2 in both conditions, and all validation gates pass.

### Stage 5: Full measured run

1. Run five paired passes with interleaved plain and mTLS/AuthZ ordering.
2. Keep image digest fixed across the pair.
3. Keep benchmark parameters equal to the final RQ2.1 paired run.
4. Export and analyze the merged artifact set.
5. Destroy infrastructure on success or failure.

**Exit criterion:** the result produces stable paired deltas and a complete
multi-node validation artifact.

### Stage 6: Thesis integration

1. Keep the single-node RQ2.1 table as the main security-overhead result.
2. Add an RQ2.1b sensitivity table using the four-cell decomposition.
3. State clearly that multi-node increases production realism but not causal
   isolation.
4. Report whether the security-placement interaction is positive, near zero, or
   inconclusive.
5. Link the interpretation back to RQ1.5b placement sensitivity.

**Exit criterion:** RQ2.1 can be written as "controlled security overhead plus
placement sensitivity" rather than as two competing defaults.

---

## 12. Risks and Mitigations

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Running only mTLS/AuthZ multi-node | Cannot separate security overhead from placement overhead. | Always run the matched plain multi-node condition. |
| Treating multi-node as the headline default | Confounds the RQ2.1 causal claim. | Label as RQ2.1b sensitivity and keep same-node as primary. |
| Runner still enforces same-node validation | Multi-node run fails for the wrong reason. | Add placement-aware validation before running the full experiment. |
| Missing node metadata | Placement claim cannot be defended. | Make node-name capture and multi-node validation fail-closed. |
| Control-plane pod sharing benchmark nodes | Adds avoidable contention. | Preserve system/benchmark pool split and control-plane isolation validation. |
| Azure background variance | May obscure small interaction effects. | Use paired interleaving and pass-level deltas. |
| Scope creep into all split points or ablations | Expands matrix without improving the core claim. | Keep RQ2.1b to one selected pair unless explicitly re-scoped. |

---

## Final Recommendation

Add RQ2.1b as a **two-condition multi-node paired sensitivity run**:

- `chain_2svc_plain_multinode`
- `chain_2svc_mtls_multinode`

Do not replace the current RQ2.1 result. The clean thesis story is:

1. RQ2.1 single-node estimates the controlled overhead of mTLS/AuthZ.
2. RQ2.1b tests whether that overhead changes when the protected service
   boundary crosses AKS nodes.
3. RQ1.5b and RQ2.1b together show why placement matters, while the same-node
   RQ2.1 pair preserves the causal security-overhead estimate.
