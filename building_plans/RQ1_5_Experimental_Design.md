# RQ1.5 Experimental Design

## Azure AKS Transfer Validation of the Local Kubernetes Chain Family

---

## Design Recommendation — Subset or Full Family

**Decision: Full 5-condition family.**

RQ1.5 should carry forward all five conditions from RQ1.4 to AKS:
`monolithic_k8s_1svc`, `chain_2svc`, `chain_3svc`, `chain_4svc`, `chain_5svc`.

### Rationale

**The thesis framing demands full coverage.**
The introduction explicitly states: "Later RQ1 stages move the selected decompositions into broader deployment contexts, including Kubernetes-based orchestration in RQ1.4 and Azure-hosted execution in RQ1.5, so that the thesis can compare how the same architectural decision behaves under local, orchestrated, and cloud environments." The phrase "the same architectural decision" refers to the full predefined chain family, not a curated subset of it. A subset would undermine this framing.

**The key RQ1.4 finding requires full validation.**
RQ1.4's most thesis-interesting result is the bounded non-linearity: the `chain_4svc` → `chain_5svc` increment is only 0.312 ms despite adding a fourth service boundary, because later boundaries contribute less activation transfer. This finding is only a general claim if it also holds on AKS. Omitting `chain_4svc` or `chain_5svc` would make this observation local-only and weaken the thesis narrative.

**Azure cost does not justify a subset.**
At approximately 100 ms per iteration on a Standard_D4s_v5 node, the full 5-condition experiment (5 × 200 iterations × 5 conditions = 5,000 iterations) takes roughly 8–12 minutes of execution time, plus pod deployment overhead. A single-node AKS cluster at this tier costs approximately $0.20–$0.30 per hour. The entire AKS experiment costs less than $5 in compute time. There is no cost-driven reason to omit any condition.

**A subset introduces unjustifiable selection.**
Any subset choice (e.g., {monolithic, chain_2svc, chain_3svc, chain_5svc}) would immediately raise the question: why these and not the others? The full 1→2→3→4→5 service-count progression is architecturally self-contained and requires no post-hoc justification. The conditions were predefined in RQ1.4 for exactly this reason.

**Why Option A (subset) is rejected:**
A 3- or 4-condition subset could confirm directional consistency but would sacrifice the full progression, hide or bypass the non-linearity finding, and produce an AKS dataset that is structurally different from the RQ1.4 dataset. The additional execution time is negligible. A subset is not a meaningfully cheaper design; it is only a weaker one.

---

## 1. Research Question

> **RQ1.5:** Does the end-to-end latency behavior observed across the synchronously chained coarse-stage ResNet-18 service family under local Kubernetes execution remain directionally consistent when the same family is deployed and measured on Azure Kubernetes Service?

### Thesis-Facing Interpretation

RQ1.5 is a **cloud transfer validation study**. It does not select boundaries, refine splits, introduce new architectural variants, or reopen earlier carry-forward logic. Its sole purpose is to determine whether the patterns established by RQ1.4 — specifically, the monotonic overhead progression across service counts and its bounded non-linearity at higher service counts — also hold under Azure-managed infrastructure.

The thesis requires this stage because RQ1.4 ran on a single-node local `kind` cluster, a controlled environment that eliminates Azure-specific confounds by design. That design choice was correct for RQ1.4, but it means the local results cannot be cited as cloud-representative without a validation step. RQ1.5 provides that step.

**"Directional consistency"** is the operative phrase. The question is not whether absolute latencies match between local kind and AKS (they will not; the hardware, hypervisor, and network substrate are different), but whether:

1. The ordering of conditions by mean latency is preserved on AKS.
2. The monotonic-but-bounded overhead trend (more services → higher overhead, but with diminishing per-boundary increments at higher service counts) is reproduced on AKS.
3. The relative overhead fractions (overhead as a percentage of the AKS monolithic baseline) are broadly comparable in magnitude to those observed in RQ1.4.

Absolute latency differences between RQ1.4 and RQ1.5 are expected, acknowledged, and will be discussed in the thesis as platform-environment effects rather than as architectural effects.

### What RQ1.5 Is NOT

- **Not a new boundary selection study.** No new split points are introduced or evaluated.
- **Not a block-level refinement study.** RQ1.2 handled that; it is frozen and not reopened.
- **Not a network emulation study.** Network conditions are not artificially varied.
- **Not a multi-region or multi-cluster study.** All pods run in a single AKS cluster in a single Azure region.
- **Not a security study.** TEEs and encryption are RQ2's concern.
- **Not a protocol comparison.** gRPC with Protocol Buffers is fixed.
- **Not a GPU inference study.** CPU-only FP32 is maintained throughout.
- **Not an Azure performance optimisation study.** RQ1.5 is not trying to minimize AKS latency; it is trying to validate that the RQ1.4 findings transfer.

---

## 2. Dependency on Earlier Stages

### Dependency Chain

| Stage                               | Status | Role in RQ1.5                                                                                                                                                                              |
| ----------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **RQ1.1** (coarse screening)        | Frozen | Established coarse split-point vocabulary; `layer2` selected as 2-way boundary. Indirectly justifies the split points used in each RQ1.4/RQ1.5 condition.                                  |
| **RQ1.2** (fine-grained refinement) | Frozen | Confirmed coarse boundaries are sufficient granularity. Justifies why RQ1.5 does not test block-level variants in AKS.                                                                     |
| **RQ1.3** (explanatory synthesis)   | Frozen | Explained cost patterns via compute distribution and activation-transfer burden. Provides interpretive context for evaluating whether RQ1.5 results conform to the same explanatory model. |
| **RQ1.4** (local Kubernetes chain)  | Frozen | The direct parent of RQ1.5. Defines the conditions, configurations, split-point choices, measurement contract, and execution architecture that RQ1.5 carries to AKS.                       |

### What RQ1.5 Inherits Directly from RQ1.4

- **All five conditions**, exactly as defined: `monolithic_k8s_1svc`, `chain_2svc`, `chain_3svc`, `chain_4svc`, `chain_5svc`.
- **All split-point assignments** per condition (see RQ1.4 Section 3 configuration table).
- **The service-side forwarding model** and chain topology.
- **The proto schema** including `HopTiming` accumulation.
- **The primary metric and measurement contract** (end-to-end latency, client pod timing).
- **The repetition structure** (5 rounds × 200 iterations × 5 conditions).
- **The warmup policy** (50 iterations, CV calibration, window=10, threshold=0.02).
- **The parity validation protocol** (3-phase: local segment, live chain, per-round gRPC).
- **The analysis pipeline** (`run_analysis.py` with `raw_iterations.csv` input).
- **The environment metadata schema** (`environment.json` with `deployment` section).
- **The K8s manifest structure** (`k8s/base/` + environment overlay).
- **The cluster-agnostic runner code** (`K8sBenchmarkRunner`, `ChainClient`, `chain_service_runner.py`).

### What RQ1.5 Does NOT Reopen

- **RQ1.1 carry-forward results.** Accepted as-is. The split points used in each condition were locked in RQ1.4.
- **RQ1.2 refinement results.** Accepted as-is. Block-level granularity is not studied on AKS.
- **RQ1.3 internal timing mode.** Not rerun. AKS-side compute distribution is discussed using the already-frozen local timing data.
- **RQ1.4 condition definitions.** The five conditions, their split points, and their service topologies are locked. RQ1.5 does not modify any of them.
- **RQ1.4 results.** They are used as the comparison reference, not re-derived. The frozen RQ1.4 result artifacts remain unchanged.

### Dependency Constraint

RQ1.5 cannot begin until RQ1.4 results are frozen and the following are confirmed ready:

1. The container image builds successfully and passes parity validation for all five chain configurations.
2. The `K8sBenchmarkRunner`, `ChainClient`, and `chain_service_runner.py` components have been validated in a local K8s environment.
3. The `k8s/base/` manifests have been confirmed cluster-agnostic (no Minikube-specific or kind-specific constructs in core manifests).
4. The experiment runner and client code pass a local multi-process smoke test that matches the RQ1.4 CSV schema.

---

## 3. Recommended Configuration Set

### Independent Variable

**Number of services** in the synchronous chain: 1, 2, 3, 4, 5.

This is identical to RQ1.4. The configurations are carried forward without modification. No new configurations are added. No existing configurations are removed.

### Configuration Table (Carried Forward Unchanged)

| Condition             | Services | Boundaries | Split Points                     | Service Graph                                                       |
| --------------------- | -------- | ---------- | -------------------------------- | ------------------------------------------------------------------- |
| `monolithic_k8s_1svc` | 1        | 0          | —                                | `[stem → layer1 → layer2 → layer3 → layer4 → tail]`                 |
| `chain_2svc`          | 2        | 1          | `layer2`                         | `[stem → layer1 → layer2]` → `[layer3 → layer4 → tail]`             |
| `chain_3svc`          | 3        | 2          | `layer1, layer3`                 | `[stem → layer1]` → `[layer2 → layer3]` → `[layer4 → tail]`         |
| `chain_4svc`          | 4        | 3          | `layer1, layer2, layer3`         | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4 → tail]`     |
| `chain_5svc`          | 5        | 4          | `layer1, layer2, layer3, layer4` | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4]` → `[tail]` |

### Per-Condition Rationale for AKS Inclusion

**`monolithic_k8s_1svc` — Required.**
The AKS-resident baseline. Identical to the RQ1.4 baseline in structure: full ResNet-18 as a single Kubernetes service pod, accepting the raw input tensor and returning the final output. This condition captures Azure container runtime overhead, AKS networking overhead, and the baseline gRPC cost with zero additional service boundaries. All chain conditions are compared against it. Without this baseline, no within-stage overhead computation is possible, and cross-stage comparison with RQ1.4 loses its normalization anchor.

**`chain_2svc` — Required.**
The simplest chain. Provides the AKS measurement of the smallest non-monolithic overhead point. In RQ1.4, this was +2.742 ms (3.4%), making it the least expensive chained condition. If this relative ordering holds on AKS, it strengthens the thesis claim that `chain_2svc` is the most cost-efficient chained deployment across both local and cloud environments.

**`chain_3svc` — Required.**
The first truly multi-hop condition. Tests the AKS overhead of a second service boundary. In RQ1.4, adding the second boundary (going from 2 to 3 services) added +3.419 ms relative to `chain_2svc`. Validating this on AKS determines whether multi-hop overhead scales similarly in the cloud environment.

**`chain_4svc` — Required.**
Tests the fourth-service overhead increment. In RQ1.4, the 3→4 service transition added +4.704 ms, still maintaining a roughly consistent per-boundary cost. Including this condition on AKS is necessary to validate that the approximately linear overhead trend through chain_3svc→chain_4svc holds in the cloud.

**`chain_5svc` — Required.**
Maximum coarse decomposition. The most thesis-critical condition for AKS validation because of its role in the RQ1.4 non-linearity finding. In RQ1.4, `chain_5svc` added only 0.312 ms above `chain_4svc`, despite adding a fifth service boundary, because the final boundary transfers only 98 KB of activation. This is a specific mechanistic prediction: later boundaries with smaller activation transfers cost less. If AKS reproduces this pattern, it validates the explanatory model from RQ1.3 under cloud conditions. If AKS reverses this pattern (e.g., because Azure-side scheduling overhead dominates the small activation saving), that is also a thesis-level finding. Either outcome is informative. Omitting `chain_5svc` would forfeit this test entirely.

### Why No New Conditions Are Added for RQ1.5

Adding new configurations would make RQ1.5 a partially exploratory study, not a transfer validation. New configurations would require their own carry-forward justification (which RQ1.5 does not have) and would dilute the cross-stage comparison. Every condition in RQ1.5 must have a corresponding RQ1.4 condition so that the directional consistency question can be answered condition-by-condition.

---

## 4. Execution Architecture

### High-Level Architecture

RQ1.5 uses the identical service-side forwarding model as RQ1.4. The client pod sends input to Service 1, which computes and forwards to Service 2, and so on through the chain until the final service returns its result back through the chain to the client. There are no changes to this model.

```
Client Pod (K8s Job)
    │
    │──gRPC──→ chain-svc-1 (ClusterIP)
                    │──gRPC──→ chain-svc-2 (ClusterIP)
                                    │──gRPC──→ chain-svc-3 (ClusterIP)
                                                    │──...──→ chain-svc-N (ClusterIP)
```

### AKS Cluster Configuration

**Single-node cluster with explicit pod colocation.**

This is the most important AKS architectural decision and requires justification.

RQ1.4 ran all service pods on the same node of a single-node kind cluster (`thesis-rq14-control-plane`). This was not a deliberate design choice for RQ1.4 — it was an automatic consequence of using a single-node cluster. For RQ1.5, it must be a deliberate, explicit design choice.

If RQ1.5 deploys services across multiple AKS nodes without affinity constraints, inter-service gRPC calls will traverse real inter-VM Azure Virtual Network paths. That changes the network topology relative to RQ1.4 (where all gRPC hops were intra-node loopback or inter-pod within the same node's network stack). This would confound the comparison: any latency difference between RQ1.4 and RQ1.5 would conflate Azure platform effects with inter-node network effects, making it impossible to attribute differences to the cloud environment itself.

**Recommended approach:** Provision an AKS cluster with a single node pool of 1–2 nodes, and deploy all service pods for each condition with pod affinity rules requiring colocation on the same node. This ensures the intra-condition network topology is the same as RQ1.4 (same-node pod-to-pod communication) while running on Azure-managed infrastructure.

**Pod affinity configuration:**

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            experiment: rq15
        topologyKey: "kubernetes.io/hostname"
```

This constraint must apply to all service pods within a condition. The client job does not require colocation with service pods but must run in the same cluster.

**Why not multi-node?**
A multi-node experiment would answer a different question: "what is the cross-VM communication overhead in Azure?" That question is interesting but belongs to a different RQ. RQ1.5 is specifically a directional consistency validation, and the best way to isolate Azure platform effects from topology changes is to keep the topology identical to RQ1.4.

**Rolling execution is valid.**
The five-condition family does not need to be deployed simultaneously to answer RQ1.5. A rolling execution model that deploys one condition at a time, measures it, tears it down, and then proceeds to the next condition is methodologically acceptable, provided that each condition preserves the same fully controlled pod profile, single-threaded execution settings, image digest, and same-node colocation contract. This preserves the full 1→2→3→4→5 service-count progression while reducing cluster capacity requirements from the sum of all deployed services to the largest single condition plus the benchmark client.

### Service Discovery

Unchanged from RQ1.4: Kubernetes ClusterIP Services with DNS-based discovery. Each service resolves its next-hop target via `chain-svc-{N}.rq15.svc.cluster.local`. The `kubernetes.namespace` config field changes from `rq14` to `rq15` (or `rq15-aks`); no code changes are required.

### Kubernetes Client

The benchmark driver runs as a Kubernetes Job in the same namespace as the service pods. It must run inside the cluster to preserve the same network context as RQ1.4. An external client (from outside the cluster, e.g., a laptop running `kubectl port-forward`) is rejected because it would add external-to-cluster network overhead that is not present in RQ1.4 and would conflate measurement boundaries.

### Container Image and Registry

All service pods use the same single container image as RQ1.4 (`Dockerfile` unchanged). The image must be pushed to an Azure Container Registry (ACR) and the AKS cluster must be configured to pull from that registry. The segment loaded at runtime is selected via the same CLI arguments (`--segment-index`, `--split-points`, `--next-hop`) defined in `chain_service_runner.py`.

Image pinning: the thesis-facing AKS run must use a pinned image digest (not a mutable tag) to ensure the exact same code runs throughout the experiment. Record the full image digest in `environment.json`.

### What Remains Identical to RQ1.4

| Component         | RQ1.4                              | RQ1.5                             | Notes           |
| ----------------- | ---------------------------------- | --------------------------------- | --------------- |
| Forwarding model  | Service-side                       | Service-side                      | Unchanged       |
| gRPC transport    | ClusterIP, K8s DNS                 | ClusterIP, K8s DNS                | Unchanged       |
| Proto schema      | `inference.proto` with `HopTiming` | Same                              | Unchanged       |
| Client type       | `ChainClient` (in-cluster job)     | `ChainClient` (in-cluster job)    | Unchanged       |
| Service image     | Single image, segment-at-runtime   | Same image, pushed to ACR         | Build unchanged |
| Condition set     | 5 conditions                       | 5 conditions (same)               | Unchanged       |
| Timing boundaries | Client pod, `time.perf_counter()`  | Client pod, `time.perf_counter()` | Unchanged       |

### What Changes Because the Environment Is Azure AKS

| Aspect                   | RQ1.4 (kind)                     | RQ1.5 (AKS)                        |
| ------------------------ | -------------------------------- | ---------------------------------- |
| Cluster provisioner      | kind CLI                         | `az aks create` / Terraform        |
| Image registry           | Local `docker load`              | ACR push + AKS pull permission     |
| Node infrastructure      | Local VM (Windows host)          | Azure-managed VM (Standard_D4s_v5) |
| Node kernel / hypervisor | Host kernel                      | Azure Linux + Azure hypervisor     |
| CPU governor control     | DaemonSet / manual (best-effort) | Not available (managed nodes)      |
| Turbo boost control      | sysfs DaemonSet (best-effort)    | Not available (managed nodes)      |
| CNI plugin               | kindnet                          | Azure CNI or Kubenet               |
| DNS provider             | CoreDNS (kind-configured)        | CoreDNS (AKS-configured)           |
| Result extraction        | Local filesystem / `kubectl cp`  | `kubectl cp`                       |
| Pod placement guarantee  | Automatic (single node)          | Explicit affinity rule             |
| Namespace                | `rq14`                           | `rq15`                             |
| Config YAML section      | `kubernetes.namespace: rq14`     | `kubernetes.namespace: rq15`       |

---

## 5. Measurement Contract

### Primary Metric

**Mean end-to-end inference latency (ms)** — measured at the client pod, from immediately before the input tensor is serialized for the gRPC call to Service 1, to immediately after the final response from Service 1 is deserialized. This is identical to RQ1.4.

This metric is primary because it captures the full cost of inference as seen by a caller in the AKS environment, including model computation, serialization, gRPC framing, pod-to-pod network transport, and container runtime overhead.

### Secondary Metrics

Identical to RQ1.4:

| Metric                    | Type          | Description                                                           |
| ------------------------- | ------------- | --------------------------------------------------------------------- |
| `median_end_to_end_ms`    | Summary       | Robust central tendency                                               |
| `p95_end_to_end_ms`       | Summary       | Tail behavior                                                         |
| `std_end_to_end_ms`       | Summary       | Variability                                                           |
| `total_compute_ms`        | Per-iteration | Sum of server-reported `compute_ms` across all hops                   |
| `total_activation_bytes`  | Per-iteration | Sum of activation bytes transferred across all boundaries             |
| `num_hops`                | Per-iteration | Number of gRPC boundaries (services − 1 for chains, 1 for monolithic) |
| `non_compute_overhead_ms` | Derived       | `end_to_end_ms − total_compute_ms`                                    |

The `non_compute_overhead_ms` naming is intentionally preserved from RQ1.4. In AKS, the residual overhead includes container runtime, AKS networking, Azure hypervisor, and any Azure-infrastructure-level latency that cannot be attributed to model computation.

### Per-Hop Diagnostic Metrics

Same as RQ1.4: `hop_{i}_compute_ms`, `hop_{i}_deserialize_ms`, `hop_{i}_serialize_ms`, `hop_{i}_forward_ms`, `hop_{i}_activation_bytes` for each hop `i`. These are diagnostic only; they support interpretation but do not carry main thesis claims.

### Per-Iteration CSV Schema

**Unchanged from RQ1.4.** The `raw_iterations.csv` schema must be identical to enable direct loading into the existing `run_analysis.py` pipeline:

```
round, condition, iteration,
end_to_end_ms, total_compute_ms, non_compute_overhead_ms,
total_activation_bytes, num_hops,
hop_1_compute_ms, hop_1_deserialize_ms, hop_1_serialize_ms, hop_1_forward_ms, hop_1_activation_bytes,
hop_2_compute_ms, ..., hop_2_activation_bytes,
...
hop_5_compute_ms, ..., hop_5_activation_bytes
```

Preserving this schema is critical. Any deviation would break the analysis pipeline and complicate cross-stage comparison.

### Baseline

The AKS-resident monolithic baseline is `monolithic_k8s_1svc` deployed to AKS. All overhead calculations within RQ1.5 are relative to this baseline:

```
aks_overhead_ms(condition) = mean_aks(condition) - mean_aks(monolithic_k8s_1svc)
aks_overhead_pct(condition) = aks_overhead_ms / mean_aks(monolithic_k8s_1svc) × 100
```

Cross-stage comparison (RQ1.4 vs RQ1.5) uses the frozen RQ1.4 summary statistics. It compares:

- Whether the condition ordering is preserved.
- Whether the relative overhead percentages are directionally similar.
- Whether the non-linearity at `chain_5svc` is reproduced.

Absolute cross-stage latency differences (e.g., the AKS monolithic baseline will likely differ from 81.447 ms) are expected and are discussed as environment-level effects, not experimental confounds.

### Additional Azure Environment Metadata

The `environment.json` artifact must include an extended `deployment` section for AKS:

```json
{
  "deployment": {
    "type": "kubernetes",
    "cluster_type": "aks",
    "cluster_version": "<k8s-server-version>",
    "node_count": "<node-count-in-pool>",
    "node_instance_type": "Standard_D4s_v5",
    "azure_region": "<region>",
    "cni": "<azure-cni|kubenet>",
    "namespace": "rq15",
    "pod_colocation_enforced": true,
    "pod_placement": {
      "chain-svc-1": "<node-hostname>",
      "chain-svc-2": "<node-hostname>",
      ...
    },
    "container_image_digest": "sha256:<digest>",
    "acr_registry": "<registry>.azurecr.io"
  }
}
```

The `pod_colocation_enforced` and `pod_placement` fields are mandatory. If pod colocation cannot be verified (e.g., the affinity constraint was ineffective), the experiment must be aborted and the colocation constraint diagnosed before proceeding.

### Comparability with RQ1.4

| Aspect               | RQ1.4 (kind)                  | RQ1.5 (AKS)                  | Compatible?                                                     |
| -------------------- | ----------------------------- | ---------------------------- | --------------------------------------------------------------- |
| Primary metric       | `end_to_end_ms` (client pod)  | `end_to_end_ms` (client pod) | Yes — identical semantics                                       |
| Baseline             | `monolithic_k8s_1svc` on kind | `monolithic_k8s_1svc` on AKS | Same structure; different absolute value                        |
| Overhead calculation | vs K8s monolithic             | vs AKS monolithic            | Within-stage comparison valid; cross-stage is thesis discussion |
| CSV schema           | Fixed schema                  | Identical fixed schema       | Yes — enables pipeline reuse                                    |
| Repetition           | 5 × 200                       | 5 × 200                      | Yes — identical                                                 |
| Warmup               | 50 iter, CV calibration       | 50 iter, CV calibration      | Yes — identical                                                 |
| Parity tolerance     | atol=1e-5, 5 inputs           | atol=1e-5, 5 inputs          | Yes — identical                                                 |

---

## 6. Parity, Warmup, and Reproducibility

### Parity Validation

Identical three-phase protocol from RQ1.4:

**Phase 1 — Local segment validation (pre-deployment):**
Before deploying anything to AKS, validate locally that chaining all N model segments produces numerically equivalent output to monolithic ResNet-18. Tolerance: `atol = 1e-5`. Inputs: 5 deterministic test inputs. Fail-closed. This is unchanged from RQ1.4 and uses the same `validate_chain_equivalence()` function.

**Phase 2 — Live chain validation (post-deployment on AKS):**
After all AKS pods are running and ready, send test inputs through the deployed chain on AKS and compare final output against the expected monolithic output. This validates end-to-end gRPC chain correctness including ACR-pulled image integrity and AKS-side serialization. Fail-closed: divergence aborts the experiment.

**Phase 3 — Per-round gRPC parity (round 1 only):**
Run gRPC parity check for each condition after its warmup in round 1. Record results in `parity_validation.json` alongside `environment.json`.

### Warmup Policy

Unchanged from RQ1.4:

- `warmup_iterations = 50` per condition per round
- `window = 10`, `cv_threshold = 0.02`
- All warmup iterations traverse the full AKS chain, warming model computation in each pod, gRPC connections between pods, in-cluster AKS DNS resolution, and connection pooling.
- All warmup iterations are discarded from measurement.
- Warmup calibration metadata recorded in `warmup_calibration.json`.

**AKS-specific warmup note:** AKS pods may exhibit slower initial stabilization than kind pods due to Azure hypervisor scheduling and Azure CNI initialization overhead. If the CV threshold is not reached within 50 warmup iterations, the warmup limit should be raised to 100 for the AKS run. This should be recorded as a deviation from RQ1.4 warmup behavior if it occurs, and reported transparently in the thesis.

### Repeated Runs Structure

| Parameter                                 | Value                              | Same as RQ1.4? |
| ----------------------------------------- | ---------------------------------- | -------------- |
| Rounds                                    | 5                                  | Yes            |
| Measured iterations per round × condition | 200                                | Yes            |
| Total per condition                       | 1,000                              | Yes            |
| Total iterations (5 conditions)           | 5,000                              | Yes            |
| Condition ordering                        | Randomized per round, seeded       | Yes            |
| Cooldown between conditions               | 5 seconds                          | Yes            |
| Pod lifecycle                             | All pods remain running throughout | Yes            |

**Why the 5×200 structure is preserved:**
The repetition structure was designed in RQ1.1 for statistical power and round-to-round consistency evidence. It should not be reduced for AKS. The AKS execution time for 5,000 iterations at ~100 ms per iteration is approximately 8 minutes. This is not a significant cost or time constraint. Reducing to fewer rounds or iterations would weaken the statistical comparability with RQ1.4 and undermine the cross-stage comparison.

### Condition Ordering

Randomized per round using seeded `Random(seed + round_num)`. Same seed as RQ1.4 for structural symmetry; since the experiment is independent, reusing the same random seed does not introduce dependence between datasets.

### Pod Lifecycle During Experiment

All service pods remain running throughout the entire AKS experiment. Pods are not restarted between rounds or conditions. If a pod crashes during the experiment, abort and re-provision from scratch. Partial results from a crashed AKS experiment are not used.

### AKS-Specific Variance Acknowledgements

The thesis must explicitly note the following AKS-specific variance sources that are not present in RQ1.4:

1. **Azure VM hypervisor scheduling.** AKS nodes run on Azure-managed VMs with a hypervisor layer that can introduce scheduling jitter not present in a bare-metal or localhost kind cluster.
2. **Azure CNI or Kubenet overhead.** AKS networking (whether Azure CNI or Kubenet) adds a managed networking layer not present in kindnet. This may increase baseline latency and add variance.
3. **Managed control plane interference.** AKS's managed control plane (API server, etcd) may generate background traffic or scheduling pressure that does not exist in a kind cluster. This is minimized by the fact that the benchmark loop makes no Kubernetes API calls after pod deployment.
4. **No CPU governor control.** Unlike the local kind environment where a DaemonSet can request "performance" governor, AKS managed nodes do not expose CPU frequency governor controls. The Azure VM's CPU scaling behavior is managed by Azure and not directly controllable.
5. **No turbo boost control.** Same limitation as governor: Azure manages turbo behavior at the VM level.
6. **Noisy neighbor risk.** AKS nodes run on shared Azure physical infrastructure. If other workloads on the same physical host generate resource contention, measurement variance may increase. This is acknowledged and partially mitigated by the Guaranteed QoS class (which gives the pods dedicated CPU allocation via cgroups).

These limitations must be documented in `environment.json` and discussed in the thesis's threats-to-validity section. They do not invalidate RQ1.5 but they do qualify what "directional consistency" can and cannot claim.

### CPU Stabilisation in AKS

**What transfers from RQ1.4:**

| Control                                     | RQ1.4 mechanism | RQ1.5 mechanism | Notes                                      |
| ------------------------------------------- | --------------- | --------------- | ------------------------------------------ |
| Thread counts (OMP, MKL, OpenBLAS, PyTorch) | Pod env vars    | Pod env vars    | Identical — same Deployment spec env block |
| PyTorch intra/inter-op threads              | Pod env vars    | Pod env vars    | Same                                       |
| CPU requests == limits (integer values)     | Deployment spec | Deployment spec | Same — Guaranteed QoS                      |

**What cannot transfer from RQ1.4:**

| Control                      | RQ1.4 mechanism           | RQ1.5 limitation                                                      |
| ---------------------------- | ------------------------- | --------------------------------------------------------------------- |
| CPU governor ("performance") | sysfs DaemonSet           | AKS managed nodes do not expose cpufreq sysfs to DaemonSets           |
| Turbo boost disable          | sysfs DaemonSet           | Same limitation                                                       |
| CPU affinity (core pinning)  | Static CPU manager policy | AKS does not support static CPU manager in default managed node pools |

**Mitigation:** Guaranteed QoS class (CPU requests == limits with integer values) provides the strongest available AKS-level CPU isolation. Thread counts remain fully controlled. The governor and turbo limitations are documented and do not make the experiment invalid; they mean the AKS measurements will have slightly higher baseline variance than the fully controlled kind measurements, which is expected and disclosed.

---

## 7. Codebase Reuse Map

### Direct Reuse (No Changes Required)

| Component                  | File                                   | Notes                                                                |
| -------------------------- | -------------------------------------- | -------------------------------------------------------------------- |
| Timer                      | `src/benchmark/timer.py`               | Transport-agnostic; unchanged                                        |
| Warmup calibration         | `src/benchmark/warmup.py`              | Accepts any `infer_fn(tensor)` callable; unchanged                   |
| Artifact logger            | `src/benchmark/logging.py`             | All file I/O unchanged                                               |
| Chain client               | `src/client/chain_client.py`           | Sends to Service 1, extracts hop timings; cluster-agnostic by design |
| Chain service runner       | `src/services/chain_service_runner.py` | CLI args unchanged; image unchanged                                  |
| Chain service              | `src/services/chain_service.py`        | Generic gRPC servicer; unchanged                                     |
| K8s benchmark runner       | `src/benchmark/k8s_runner.py`          | Uses K8s DNS, config-driven; cluster-agnostic by design              |
| K8s experiment entry point | `run_k8s_experiment.py`                | CLI unchanged; namespace config only                                 |
| Proto schema               | `proto/inference.proto` + stubs        | Unchanged                                                            |
| Model splits               | `src/models/resnet_splits.py`          | Unchanged                                                            |
| Parity validation          | `src/models/validation.py`             | `validate_chain_equivalence()` unchanged                             |
| Statistics core            | `src/analysis/statistics.py`           | Works on any `raw_iterations.csv`                                    |
| Plots                      | `src/analysis/plots.py`                | Unchanged                                                            |
| Analysis pipeline          | `run_analysis.py`                      | Operates on `raw_iterations.csv` regardless of deployment origin     |
| Frozen results             | `results/frozen/`                      | Untouched                                                            |
| Existing configs           | `configs/rq1/1.1/`, `1.2/`, `1.4/`     | Untouched                                                            |

### Minimal New Components (Config + Manifests Only)

| Component               | File                               | Change                                                                                                             |
| ----------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| RQ1.5 experiment config | `configs/rq1/1.5/rq1_5_smoke.yaml` | New file; experiment section identical to RQ1.4, `kubernetes.namespace` changed to `rq15`                          |
| RQ1.5 full config       | `configs/rq1/1.5/rq1_5_full.yaml`  | New file; same structure as `rq1_4_full.yaml`                                                                      |
| AKS manifest overlay    | `k8s/aks/`                         | New directory; Deployment/Service YAMLs with AKS-specific overrides (ACR image, resource requests, affinity rules) |
| AKS provisioning script | `scripts/provision_aks.sh`         | New utility script for `az aks create`; not part of experiment code                                                |
| ACR push script         | `scripts/push_acr.sh`              | New utility script; not part of experiment code                                                                    |

### What MUST Stay Unchanged

Every file in this list must not be modified for RQ1.5:

- `run_experiment.py` — local RQ1.1/RQ1.2 entry point
- `run_k8s_experiment.py` — if it is already cluster-agnostic (as required by RQ1.4 design D11); config change only
- `src/benchmark/runner.py` — local benchmark runner
- `src/client/split_client.py` — local split client
- `src/services/service_b.py` — local Service B
- `src/services/chain_service.py` — chain service logic
- `src/client/chain_client.py` — chain client
- `src/benchmark/k8s_runner.py` — K8s runner
- All files under `results/frozen/`
- All files under `configs/rq1/1.1/`, `configs/rq1/1.2/`, and `configs/rq1/1.4/`
- All building plans under `building_plans/`
- `proto/inference.proto` and generated stubs

The principle is strict: RQ1.5 adds config and manifests only. It does not modify experiment logic. Any required behavior change for AKS that cannot be driven purely by config is a sign that RQ1.4's cluster-agnostic design constraint (D11) was not fully met, and must be addressed as an RQ1.4 fixup before RQ1.5 begins.

### Reuse Principle

> RQ1.5 should add a config file, an AKS manifest overlay, and two provisioning scripts. Nothing else should be new.

If more than this is needed, the RQ1.4 cluster-agnostic constraint is not satisfied. Fix RQ1.4 first.

---

## 8. Azure / AKS-Specific Concerns

### 8.1 Node SKU Selection

**Recommended: Standard_D4s_v5 (4 vCPU, 16 GiB RAM)**

Justification:

- **4 vCPUs.** The experiment runs up to 5 inference service pods plus 1 client pod on a single node. Each service pod is configured with `cpu: "1"` request and limit (Guaranteed QoS, 1 dedicated vCPU). The client pod requires approximately 0.5 vCPU during measurement. Total peak CPU: ~5.5 vCPU. On a 4-vCPU node this means moderate contention; the client pod should be configured with lower CPU limits to avoid eviction.
- **Alternative: Standard_D8s_v5 (8 vCPU, 32 GiB RAM).** Strongly preferred for the full 5-service configuration if budget allows, because it provides 8 dedicated vCPUs, allowing all 5 service pods and the client pod to run without CPU overcommit. This reduces scheduling contention and variance.
- **16 GiB RAM.** ResNet-18 weights are approximately 44 MB per segment. 5 service pods × 44 MB = 220 MB for model weights. Add Python runtime and PyTorch overhead: each pod uses approximately 500 MB–1 GB RAM. Total memory footprint: ~5 GB at most. 16 GiB is sufficient; 32 GiB (D8s_v5) is comfortable.
- **Premium SSD (the 's' in Ds_v5).** Enables faster container image pulls from ACR on first pod startup. Minimizes model-loading time that is excluded from measurements anyway.
- **v5 generation.** Current-generation Intel Sapphire Rapids CPUs in Azure D-series. Avoid v3 or v4 unless v5 is unavailable in the chosen region.

**Reject: Spot/preemptible nodes.** Spot VMs can be preempted during the experiment, which would abort the run and invalidate results. Thesis-facing experiments must use on-demand nodes.

**Reject: Burstable (B-series) VMs.** B-series instances use CPU credits and burst above baseline performance. This introduces performance variance that violates the thesis's measurement stability requirements.

**Reject: GPU SKUs.** The experiment is CPU-only FP32 inference. A GPU SKU adds unnecessary cost and introduces GPU scheduling overhead that is not part of the measurement.

### 8.2 Single-Node vs Multi-Node AKS

**Recommendation: 1 node in the node pool, with pod affinity constraints enforcing colocation.**

As argued in Section 4, multi-node deployment changes the intra-condition network topology and confounds the comparison with RQ1.4. A single node pool with 1 node is the simplest configuration that preserves the same-node communication topology.

**Scaling fallback:** If a 1-node cluster is insufficient (e.g., the node runs out of CPU for 5-service chains), provision 2–3 nodes but enforce pod affinity so all service pods for a given condition land on the same node. Record which node was used for each condition in `pod_placement` metadata.

**Why not scale out:** Scaling out to distribute inference services across multiple nodes would be architecturally realistic for a production workload, but it is not what RQ1.5 is measuring. RQ1.5 is a transfer validation; it should match RQ1.4's topology as closely as possible.

### 8.3 Pod Placement and Resource Configuration

**Guaranteed QoS class.** All service pods must have `resources.requests == resources.limits` with integer CPU values. This places pods in the Kubernetes Guaranteed QoS class and gives them guaranteed CPU allocation via cgroups. It is the AKS-available equivalent of core pinning.

```yaml
resources:
  requests:
    cpu: "1"
    memory: "1Gi"
  limits:
    cpu: "1"
    memory: "1Gi"
```

**Node affinity.** Target the correct node pool:

```yaml
nodeSelector:
  agentpool: rq15pool
```

**Pod affinity.** Enforce colocation within each condition:

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            experiment-condition: <condition-name>
        topologyKey: "kubernetes.io/hostname"
```

**No anti-affinity between service pods.** All pods for a single condition must be colocated. Anti-affinity would spread them across nodes and must not be set.

**Client pod.** The client job can share the node with service pods. Assign it a lower CPU limit to avoid preempting service pods:

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

### 8.4 Image Registry (ACR)

**Create an ACR in the same Azure region as the AKS cluster.** Image pulls across regions add latency to pod startup, which adds to overall experiment setup time (not measurement time, but operational time).

**Attach ACR to AKS:** Use `az aks update --attach-acr <acr-name>` to grant AKS the `AcrPull` role on the registry. This is the simplest approach and avoids managing image pull secrets.

**Image pinning:** Push the thesis-facing image with a content-addressed tag and pin manifests to the digest:

```
<acr>.azurecr.io/thesis-inference@sha256:<digest>
```

Record the digest in `environment.json`.

**Do not use `:latest`.** Mutable tags violate reproducibility requirements. The experiment must be tied to a specific, immutable image content.

### 8.5 Result Export

**`kubectl cp` to local filesystem.** After the client job completes, copy `raw_iterations.csv`, `environment.json`, `parity_validation.json`, and `warmup_calibration.json` from the client pod to the local machine:

```bash
kubectl cp rq15/<client-pod-name>:/app/results/ ./results/rq1_5_aks_<timestamp>/
```

This is the simplest approach for thesis-scale data volumes (total CSV size is under 10 MB). No Azure Files mount or Blob Storage is required for a single-run experiment.

**Freeze results immediately** after collection, following the same naming convention as earlier stages:

```
results/frozen/frozen_rq1_5_aks_<timestamp>/
```

**Do not retain AKS cluster after results are collected.** Delete the cluster immediately to stop incurring compute charges.

### 8.6 Cost Control

**Estimated Azure cost for one full RQ1.5 run:**

- Standard_D4s_v5 (1 node, 1-2 hours including setup/teardown): ~$0.40–$0.60
- Standard_D8s_v5 (1 node, 1-2 hours): ~$0.60–$1.00
- ACR Basic tier (days to weeks for dev): ~$0.50/month
- Total experiment cost (compute only): under $5, including re-runs

**Cost controls:**

1. Delete the AKS cluster immediately after results are collected (`az aks delete`).
2. Use the ACR Basic tier (sufficient for one image).
3. Do not retain the cluster between smoke tests and the full run if the gap is more than a day.
4. Set a budget alert in Azure Cost Management at $20 as a safety threshold.
5. Do not run the full experiment on a spot cluster (preemption risk outweighs savings).

### 8.7 Network and DNS Considerations

**Azure CNI vs Kubenet.** Either works for the in-cluster communication pattern. Azure CNI assigns each pod an actual VNet IP and generally has lower latency for pod-to-pod communication. Kubenet uses a network bridge with NAT. For collocated pods on the same node, both will use the same intra-node virtual network stack, so the difference is small. Record the CNI in `environment.json`. Do not change the CNI after the experiment starts.

**CoreDNS configuration.** AKS uses CoreDNS for service discovery. First-resolution DNS lookups may be slow due to cache warming. The warmup phase (50 iterations per condition, running through the full chain) is sufficient to warm DNS caches before measurement begins. No additional DNS pre-warming step is required.

**Azure-specific gRPC considerations.** Azure's managed infrastructure does not insert explicit gRPC-level proxies or transforms in the pod-to-pod communication path for non-LoadBalancer services. ClusterIP services communicate directly pod-to-pod within the node, with no Azure middleware in the data path. This is identical to the kind cluster topology.

---

## 9. Rejected Alternatives

### Alternative A: Block-Level Azure Study

**Description:** Extend RQ1.5 to also test block-level split points (e.g., `layer3.0`) in AKS.

**Why rejected:** RQ1.2 performed block-level refinement and produced a specific finding: the block-level variant is not meaningfully different from the coarse anchor when activation sizes are identical. Retesting this in AKS would revisit a closed question without thesis justification. RQ1.5 is explicitly a transfer validation, not a re-exploration.

### Alternative B: External Client (From Outside the Cluster)

**Description:** Run the benchmark driver on the host machine or a CI server, using `kubectl port-forward` or a LoadBalancer service to reach the AKS services from outside the cluster.

**Why rejected:** An external client adds client-to-AKS network overhead (VNet peering, Azure Load Balancer, NAT, or port-forward proxy) that is not present in RQ1.4's in-cluster client. This would make the AKS measurements include network topology effects that are not in the RQ1.4 measurements, confounding the directional consistency comparison. The client must run inside the cluster for the same reason it did in RQ1.4: to keep all conditions in the same network context.

### Alternative C: Multi-Node Deployment Without Colocation

**Description:** Let pods schedule freely across AKS nodes without pod affinity constraints.

**Why rejected:** This changes the intra-condition network topology. In RQ1.4, all pods were colocated on a single node. Cross-node gRPC in AKS involves inter-VM communication across Azure's virtual network, with latency characteristics that are fundamentally different from same-node pod-to-pod communication. Multi-node deployment would answer "what is distributed cross-VM chain overhead in Azure?" — a different question from "does the RQ1.4 single-node result transfer to AKS?" RQ1.5 answers the latter.

### Alternative D: Network Emulation (Artificial Latency Injection)

**Description:** Use `tc netem` or an Azure network policy to inject artificial network latency between pods.

**Why rejected:** Network emulation is not a transfer validation; it is a sensitivity analysis. RQ1.5 does not study network latency as a variable. The pod-to-pod latency in AKS is a naturally occurring measurement condition, not a controlled variable. Artificially modifying it would answer a different question entirely.

### Alternative E: Adding Security Mechanisms (mTLS, TEE)

**Description:** Enable mutual TLS between gRPC services, or run services inside Azure Confidential Computing VMs (TEE) in RQ1.5.

**Why rejected:** TEE overhead is RQ2's concern. mTLS comparison is not part of any current RQ. Introducing security mechanisms in RQ1.5 would conflate their overhead with the baseline architectural transfer validation, making it impossible to attribute latency differences to the cloud environment vs. the security mechanism. RQ1.5 must remain a clean architectural transfer study.

### Alternative F: Protocol Comparison in AKS

**Description:** Compare gRPC against REST or other protocols in AKS.

**Why rejected:** Protocol comparison is not part of any thesis RQ. The protocol is fixed at gRPC throughout the thesis. Introducing a protocol axis in RQ1.5 would broaden scope without thesis justification.

### Alternative G: Selective Carry-Forward (Subset) to AKS

**Description:** Carry only 3–4 conditions to AKS (e.g., monolithic, chain_2svc, chain_3svc, chain_5svc).

**Why rejected:** See the design recommendation at the top of this document. The full 5-condition family is required for a complete directional consistency validation and to test the non-linearity finding at chain_5svc. The marginal Azure cost of the additional condition is negligible. Omitting any condition introduces an arbitrary selection that requires justification the thesis does not support.

### Alternative H: Combining RQ1.4 and RQ1.5 Into a Single Experiment

**Description:** Run both the kind-cluster and AKS measurements as a single experiment, possibly in parallel.

**Why rejected:** The thesis structure separates local Kubernetes (RQ1.4) from Azure AKS (RQ1.5) as distinct stages with a defined dependency relationship. RQ1.5 depends on frozen RQ1.4 results. Combining them would blur this dependency, complicate attribution of findings, and prevent the clean "local then cloud" thesis narrative. The stages must remain separated.

### Alternative I: AKS Multi-Region Study

**Description:** Run RQ1.5 in multiple Azure regions to study regional latency variation.

**Why rejected:** RQ1.5 is not a regional performance characterization. A single-region run in a single AKS cluster is sufficient for directional consistency validation. Multi-region adds cost, complexity, and scope without thesis justification.

### Alternative J: Helm or Kustomize-Based Deployment

**Description:** Use Helm charts or Kustomize overlays as the primary AKS deployment mechanism.

**Why rejected for day one:** Adds tooling complexity without experimental value. The AKS manifest overlay (k8s/aks/) can be plain YAML that extends the k8s/base/ templates with AKS-specific fields. If the base/local structure is well-organized, a manual AKS overlay is straightforward. Helm or Kustomize can be adopted in the future if the manifest count grows, but are not required for RQ1.5.

---

## 10. Implementation Roadmap

**Status:** Planning only. No implementation has begun.
**Dependency:** All phases below depend on RQ1.4 being fully complete, frozen, and validated.

### Pre-Phase: RQ1.4 Cluster-Agnostic Verification

**Before any RQ1.5 work begins, verify that the RQ1.4 codebase satisfies all cluster-agnostic constraints from RQ1.4 design decision D11.**

Checklist:

- [ ] `run_k8s_experiment.py` takes namespace as a config parameter, not hardcoded.
- [ ] `K8sBenchmarkRunner` resolves service endpoints via `kubernetes.namespace` + DNS, not hardcoded `127.0.0.1`.
- [ ] No Minikube-specific or kind-specific commands exist in `run_k8s_experiment.py`, `k8s_runner.py`, or `chain_client.py`.
- [ ] `k8s/base/` manifests use generic Deployment/Service YAMLs with no cluster-distribution-specific fields.
- [ ] The container image builds and passes parity for all 5 conditions.

If any checklist item fails, fix it in RQ1.4's codebase (under the RQ1.4 implementation scope) before proceeding to RQ1.5.

---

### Phase 1: AKS Infrastructure Provisioning

**Goal:** Create the Azure resources required for RQ1.5.

**Steps:**

1. Create an Azure Resource Group for the thesis experiment (e.g., `rg-thesis-rq15`).
2. Create an ACR (Basic tier) in the same region (e.g., `West Europe` or `UK South`).
3. Build the thesis container image locally and push to ACR:
   ```bash
   docker build -t <acr>.azurecr.io/thesis-inference:v1 .
   docker push <acr>.azurecr.io/thesis-inference:v1
   ```
4. Record the pushed image digest.
5. Create an AKS cluster with a single node pool (1 node, Standard_D8s_v5 preferred):
   ```bash
   az aks create --resource-group rg-thesis-rq15 \
     --name thesis-rq15 \
     --node-count 1 \
     --node-vm-size Standard_D8s_v5 \
     --attach-acr <acr-name> \
     --generate-ssh-keys
   ```
6. Obtain credentials (`az aks get-credentials`) and verify cluster is healthy.

**Deliverable:** Running AKS cluster with ACR attached. `scripts/provision_aks.sh` utility script.

---

### Phase 2: AKS Manifest Overlay Creation

**Goal:** Create `k8s/aks/` with AKS-specific overrides applied on top of `k8s/base/`.

**Steps:**

1. Copy or extend the `k8s/base/` manifests to `k8s/aks/`.
2. Apply AKS-specific overrides:
   - Replace image with ACR image + digest.
   - Set `resources.requests == resources.limits` with integer CPU values (Guaranteed QoS).
   - Add pod affinity rules for condition colocation.
   - Add `nodeSelector` for the correct node pool.
   - Set namespace to `rq15`.
3. Create a namespace YAML for `rq15`.
4. Create `configs/rq1/1.5/rq1_5_smoke.yaml` (1 round, 10 iterations, all 5 conditions).
5. Create `configs/rq1/1.5/rq1_5_full.yaml` (5 rounds, 200 iterations, all 5 conditions).

**Deliverable:** `k8s/aks/`, `configs/rq1/1.5/`.

---

### Phase 3: Local Pre-Validation of AKS Manifests

**Goal:** Before deploying to AKS, validate the AKS manifest structure locally using `kubectl apply --dry-run=server` or by running against a local cluster with the AKS manifests applied.

**Steps:**

1. Run `kubectl apply --dry-run=client -f k8s/aks/` to check manifest syntax.
2. If a local kind or Minikube cluster is available, apply the AKS manifests with local image (override ACR reference) and confirm pods start correctly.
3. Run Phase 1 parity validation locally against the AKS-manifest pod structure.
4. Confirm the `environment.json` output records the correct AKS-specific fields.

**Deliverable:** Confirmed manifest correctness without cloud spend.

---

### Phase 4: AKS Smoke Test

**Goal:** Deploy to AKS and run a 1-round, reduced-iteration smoke test to validate the full pipeline end-to-end on Azure infrastructure.

**Steps:**

1. Apply namespace and manifests: `kubectl apply -f k8s/aks/`.
2. Wait for all service pods to reach Running status.
3. Run Phase 1 local segment parity validation.
4. Run Phase 2 live chain parity validation on AKS (send test inputs through the deployed AKS chain).
5. Run 1 round of 10 iterations using `configs/rq1/1.5/rq1_5_smoke.yaml`.
6. Collect output via `kubectl cp`.
7. Confirm CSV schema matches RQ1.4 schema exactly.
8. Confirm `environment.json` records cluster type as `aks`, correct instance type, correct pod placement, and `pod_colocation_enforced: true`.
9. Check that all pods remained on the same node.

**Acceptance criteria:** CSV schema correct, parity passes, all pods colocated, `environment.json` populated correctly.

**Deliverable:** Smoke test results in `results/rq1_5_smoke_<timestamp>/`. Confirmed AKS pipeline works.

---

### Phase 5: Full RQ1.5 AKS Experiment

**Goal:** Run the thesis-facing experiment: 5 rounds × 200 iterations × 5 conditions on AKS.

**Steps:**

1. Confirm smoke test passed and all manifests are in correct state.
2. Confirm the ACR image is pinned to a content-addressed digest.
3. Deploy all pods for the first condition in the run order.
4. Run `run_k8s_experiment.py` with `configs/rq1/1.5/rq1_5_full.yaml`.
5. Monitor progress; do not interrupt the run.
6. If a pod crashes, abort and rerun from scratch (partial results are not used).
7. After completion, collect all artifacts via `kubectl cp`.

**Deliverable:** Full `raw_iterations.csv`, `environment.json`, `parity_validation.json`, `warmup_calibration.json`.

---

### Phase 6: Result Validation and Freezing

**Goal:** Validate collected results and freeze them.

**Steps:**

1. Confirm `raw_iterations.csv` has the expected row count: 5 rounds × 200 iterations × 5 conditions = 5,000 rows.
2. Confirm no NaN, zero, or implausibly large/small values in primary metrics.
3. Confirm `pod_colocation_enforced: true` in `environment.json` and all service pods listed in `pod_placement` are on the same node.
4. Run `run_analysis.py` on the collected CSV to confirm the analysis pipeline runs without error.
5. Review the summary statistics for directional consistency with RQ1.4 frozen results:
   - Condition ordering should match RQ1.4 (monolithic < chain_2svc < chain_3svc < chain_4svc, chain_5svc ≥ chain_4svc).
   - Relative overhead percentages should be in a broadly comparable range (within one order of magnitude).
6. Copy results to `results/frozen/frozen_rq1_5_aks_<timestamp>/`.
7. Delete the AKS cluster: `az aks delete --name thesis-rq15 --resource-group rg-thesis-rq15`.
8. Record the image digest, cluster version, and node instance type in the frozen result metadata.

**Deliverable:** Frozen RQ1.5 AKS results.

---

### Phase 7: Cross-Stage Analysis

**Goal:** Produce the cross-stage comparison between frozen RQ1.4 (kind) and frozen RQ1.5 (AKS) results.

**Steps:**

1. Load both frozen `raw_iterations.csv` files.
2. Compute per-condition summary statistics for both stages.
3. Compare relative overhead percentages (overhead/monolithic_baseline × 100) across stages.
4. Test whether condition ordering is preserved.
5. Evaluate whether the chain_5svc non-linearity is reproduced on AKS.
6. Produce comparative plots: grouped bar chart of relative overhead by condition, with RQ1.4 and RQ1.5 side-by-side.
7. Write thesis analysis section for RQ1.5.

**Deliverable:** Cross-stage comparison artifacts and thesis analysis text.

---

## 11. Design Decision Record

| #   | Decision                                                      | Rationale                                                                                                                                       | Status                             |
| --- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| D1  | Full 5-condition family on AKS (not subset)                   | Thesis framing requires "same architectural decision"; full family validates non-linearity finding; marginal Azure cost is negligible           | **Accepted**                       |
| D2  | Single-node colocation via pod affinity                       | Preserves same-node communication topology as RQ1.4; prevents confounding topology changes with environment effects                             | **Accepted**                       |
| D3  | Standard_D8s_v5 preferred (Standard_D4s_v5 minimum)           | 8 vCPU avoids CPU overcommit for 5 service pods; Premium SSD enables faster ACR pulls                                                           | **Accepted (D8s_v5 preferred)**    |
| D4  | In-cluster client pod (Kubernetes Job)                        | Preserves same network context as RQ1.4; external client adds confounding network overhead                                                      | **Accepted**                       |
| D5  | Identical 5×200 repetition structure                          | Statistical comparability with RQ1.4; 8–12 minutes execution time is not a constraint                                                           | **Accepted**                       |
| D6  | Identical warmup policy (50 iter, CV calibration)             | Comparability; AKS warmup may need 100-iteration fallback if CV threshold not met                                                               | **Accepted (with fallback noted)** |
| D7  | Identical primary metric and CSV schema                       | Required for analysis pipeline reuse and cross-stage comparison                                                                                 | **Accepted**                       |
| D8  | ACR with pinned image digest (not `:latest`)                  | Reproducibility requirement                                                                                                                     | **Accepted**                       |
| D9  | `kubectl cp` for result export (no Azure Files)               | Simplest approach for thesis-scale data; avoids extra Azure resource dependencies                                                               | **Accepted**                       |
| D10 | Delete AKS cluster immediately after results collected        | Cost control; no reason to retain cluster between experiment and analysis                                                                       | **Accepted**                       |
| D11 | No governor/turbo control on AKS (documented limitation)      | AKS managed nodes do not expose these controls; Guaranteed QoS provides best available isolation                                                | **Accepted (documented)**          |
| D12 | No new code components (config and manifests only)            | RQ1.5 is a transfer validation; if new code is required, it indicates an RQ1.4 cluster-agnostic failure that must be fixed first                | **Accepted**                       |
| D13 | AKS manifests in `k8s/aks/` (separate from `k8s/local/`)      | Isolates AKS-specific overrides from local cluster manifests; consistent with the base/local split established in RQ1.4 design                  | **Accepted**                       |
| D14 | On-demand nodes (not spot/preemptible)                        | Preemption during experiment invalidates results; cost savings do not justify the risk                                                          | **Accepted**                       |
| D15 | Cross-stage comparison is thesis discussion, not experimental | Local kind and AKS have different absolute latencies due to different hardware/hypervisor; directional comparison is the valid analytical frame | **Accepted**                       |

---

## Key Decisions Requiring Approval Before Implementation

The following decisions are recommended by this document but require explicit approval before any implementation work begins.

**D1 — Full 5-condition family vs subset**
This document recommends all five RQ1.4 conditions on AKS. Approve if the full family is correct; reject if a subset is preferred (and specify which conditions to omit and why).

**D3 — Node SKU**
Standard_D8s_v5 is preferred for headroom; Standard_D4s_v5 is the minimum. Approve the SKU choice. If cost is a constraint, D4s_v5 is acceptable with documented potential for CPU overcommit on the 5-service conditions.

**D2 — Single-node pod colocation as a hard constraint**
This document treats pod colocation as a required experiment constraint, not a best-effort. If colocation cannot be enforced (e.g., a 1-node cluster is insufficient for all pods), the experiment must fail rather than proceed with cross-node communication. Approve this fail-closed colocation policy.

**D11 — Acknowledged limitations of AKS CPU stabilisation**
The thesis will explicitly disclose that AKS CPU governor and turbo controls are unavailable, and that Guaranteed QoS is the best-available AKS stabilisation mechanism. Approve this framing as the honest representation of AKS limitations.

**D9 — Result export via `kubectl cp`**
No persistent Azure storage is provisioned. Results are copied out after the experiment and the cluster is deleted. Approve this approach, or specify if an Azure Files mount or Blob Storage export is preferred.

**Phase 5 trigger — when to run the full experiment**
Confirm that the full AKS experiment should only be triggered after the smoke test (Phase 4) passes all acceptance criteria. Approve the fail-closed policy (smoke test failure = full run does not proceed).
