# RQ1.4 Experimental Design

## Multi-Microservice Chained Inference Under In-Cluster Kubernetes Execution

---

## 1. Research Question

> **RQ1.4:** How does increasing the number of microservices affect end-to-end inference cost when ResNet-18 is decomposed into synchronously chained coarse architectural stages under in-cluster Kubernetes execution?

### Thesis-Facing Interpretation

RQ1.4 is a **service-count effect study**. The independent variable is the number of microservices (equivalently, the number of service boundaries) through which a single inference request is synchronously forwarded. The dependent variable is end-to-end inference latency and communication-related overhead.

### Translation to Engineering Terms

- **"Synchronously chained":** A single inference request enters Service 1, which computes its model segment and forwards the intermediate activation tensor to Service 2 via gRPC. Service 2 computes and forwards to Service 3. This continues until the final service completes inference and the result propagates back through the chain to the caller. All forwarding is synchronous and blocking.
- **"Coarse architectural stages":** The four named residual-block stages in ResNet-18 (`layer1`, `layer2`, `layer3`, `layer4`) plus the stem (`conv1/bn1/relu/maxpool`) and tail (`avgpool/fc`). Split points are placed only at coarse stage boundaries, not at block-level (block-level refinement was RQ1.2's concern).
- **"In-cluster Kubernetes execution":** All services run as Kubernetes pods within a single cluster. Communication is via in-cluster gRPC over ClusterIP Services. The client (benchmark driver) also runs inside the cluster.
- **"Increasing the number of microservices":** Configurations range from 1 service (monolithic) through 5 services (maximum coarse decomposition), forming a clean service-count progression.

### What RQ1.4 Is NOT

- **Not a split-selection study.** The configuration set is predefined by coarse architecture; no carry-forward rule is needed.
- **Not a refinement study.** Block-level splits are excluded.
- **Not a security study.** That is RQ2.
- **Not an Azure/cloud validation study.** That is RQ1.5.
- **Not a local subprocess experiment.** Services are real Kubernetes pods with real container boundaries.

---

## 2. Dependency on Earlier Stages

### Dependency Chain

| Stage                               | Status | Role in RQ1.4                                                                                                                                                                                                        |
| ----------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RQ1.1** (coarse screening)        | Frozen | Established that coarse stage boundaries produce measurable but small overhead (1.1–4.6%) under local execution. Provides the coarse split-point vocabulary reused here.                                             |
| **RQ1.2** (fine-grained refinement) | Frozen | Showed that within-stage refinement (layer3.0) yields negligible latency difference from the coarse anchor (layer3) when activation sizes are identical. Confirms that coarse boundaries are sufficient granularity. |
| **RQ1.3** (explanatory synthesis)   | Frozen | Explained RQ1.1/RQ1.2 results via activation-transfer size and compute distribution. Internal timing showed where compute is concentrated. Provides interpretive context for RQ1.4 but is not rerun.                 |

### What RQ1.4 Inherits

- **Model split definitions:** The four coarse stage boundaries from `resnet_splits.py`.
- **Measurement philosophy:** Same primary metric (end-to-end latency), same repetition structure, same warmup calibration, same parity validation.
- **gRPC transport:** Same proto-based tensor serialization.
- **Statistical analysis:** Same summary statistics, cross-condition comparison, effect sizes.

### What RQ1.4 Does NOT Reopen

- RQ1.1 carry-forward results are accepted as-is.
- RQ1.2 refinement results are accepted as-is.
- Internal timing mode is not rerun for RQ1.4.
- The local subprocess-based experiment infrastructure is preserved unchanged.

---

## 3. Recommended Configuration Set

### Independent Variable

**Number of services** in the synchronous chain: 1, 2, 3, 4, 5.

This is a **clean progression** in service count using coarse architectural stages only. Each configuration represents the most architecturally natural way to partition ResNet-18 into that many services.

### Configuration Table

| Condition             | Services | Boundaries | Split Points                     | Service Graph                                                       |
| --------------------- | -------- | ---------- | -------------------------------- | ------------------------------------------------------------------- |
| `monolithic_k8s_1svc` | 1        | 0          | —                                | `[stem → layer1 → layer2 → layer3 → layer4 → tail]`                 |
| `chain_2svc`          | 2        | 1          | `layer2`                         | `[stem → layer1 → layer2]` → `[layer3 → layer4 → tail]`             |
| `chain_3svc`          | 3        | 2          | `layer1, layer3`                 | `[stem → layer1]` → `[layer2 → layer3]` → `[layer4 → tail]`         |
| `chain_4svc`          | 4        | 3          | `layer1, layer2, layer3`         | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4 → tail]`     |
| `chain_5svc`          | 5        | 4          | `layer1, layer2, layer3, layer4` | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4]` → `[tail]` |

### Service Graph Details

**`monolithic_k8s_1svc` (1 service, 0 boundaries):**

```
Client Pod ──gRPC──→ [Svc-1: stem+layer1+layer2+layer3+layer4+avgpool+fc] ──gRPC──→ Client Pod
```

This is a monolithic model deployed as a single Kubernetes service. The client sends the raw input tensor and receives the final output. This condition captures container and in-cluster gRPC overhead with zero model-boundary cost.

**`chain_2svc` (2 services, 1 boundary):**

```
Client Pod ──gRPC──→ [Svc-1: stem+layer1+layer2] ──gRPC──→ [Svc-2: layer3+layer4+tail] ──back──→ Client Pod
```

The split at `layer2` was RQ1.1's carried-forward `selected_main` candidate — the most balanced coarse 2-way partition. It transfers 100,352 floats (≈392 KB) at the boundary.

**`chain_3svc` (3 services, 2 boundaries):**

```
Client Pod ──gRPC──→ [Svc-1: stem+layer1] ──gRPC──→ [Svc-2: layer2+layer3] ──gRPC──→ [Svc-3: layer4+tail] ──back──→ Client Pod
```

Splits at `layer1` and `layer3`. Activation sizes: 784 KB (hop 1→2), 196 KB (hop 2→3).

**`chain_4svc` (4 services, 3 boundaries):**

```
Client Pod ──gRPC──→ [Svc-1: stem+layer1] ──gRPC──→ [Svc-2: layer2] ──gRPC──→ [Svc-3: layer3] ──gRPC──→ [Svc-4: layer4+tail] ──back──→ Client Pod
```

Splits at `layer1`, `layer2`, `layer3`. Activation sizes: 784 KB, 392 KB, 196 KB.

**`chain_5svc` (5 services, 4 boundaries):**

```
Client Pod ──gRPC──→ [Svc-1: stem+layer1] ──gRPC──→ [Svc-2: layer2] ──gRPC──→ [Svc-3: layer3] ──gRPC──→ [Svc-4: layer4] ──gRPC──→ [Svc-5: tail] ──back──→ Client Pod
```

Maximum coarse decomposition. Splits at all four stage boundaries. Activation sizes: 784 KB, 392 KB, 196 KB, 98 KB.

### Justification for Each Condition

**`monolithic_k8s_1svc`:** Essential baseline. Unlike the local monolithic baseline (which runs in-process with no container or network overhead), this captures the Kubernetes deployment context — container runtime, in-cluster gRPC, pod scheduling — while having zero model-boundary overhead. All chain-condition comparisons are made against this baseline so that the measured overhead is attributable to additional service boundaries rather than to Kubernetes itself.

**`chain_2svc`:** The simplest chain. Bridges back to RQ1.1's local `split_after_layer2` condition. Enables a controlled comparison: same split point, but now with real container isolation and in-cluster networking instead of localhost subprocess communication.

**`chain_3svc`:** First truly multi-hop configuration (more than 2 services). Tests the marginal cost of the second service boundary. The split at `layer1, layer3` was chosen because it distributes stages across three segments of comparable architectural size (2 stages, 2 stages, 1 stage + tail).

**`chain_4svc`:** Progressive increase. Tests whether the overhead-per-boundary cost is approximately linear.

**`chain_5svc`:** Maximum coarse decomposition. Every stage is a separate service. Tests whether overhead continues to scale or whether diminishing activation sizes at later boundaries offset the additional boundary-crossing cost.

### Why NOT More Than 5

ResNet-18 has exactly 4 coarse architectural stages. 5 services is the maximum decomposition at coarse granularity. Going beyond 5 would require block-level splits, which violates the coarse-stage constraint.

### Why NOT Fewer Than 5

Omitting any configuration would leave a gap in the service-count progression. The thesis claim is about "how does increasing the number of microservices affect cost" — a clean 1→2→3→4→5 progression gives the strongest answer.

### Why NOT Fine-Grained or Mixed Configurations

RQ1.4's independent variable is service count, not split-point quality. Using the architecturally natural coarse boundaries at each service count keeps the experiment interpretable. Block-level refinement was RQ1.2's concern and is not reopened here.

### Why the 2-Service Split Point Is `layer2`

The `layer2` split was RQ1.1's `selected_main` carry-forward boundary — the most balanced coarse partition. Using it provides direct continuity with the frozen local results. Other 2-service options (`layer1`, `layer3`, `layer4`) would answer a different question; `layer2` is the most defensible single choice because it was already empirically validated in RQ1.1.

### Why the 3-Service Split Points Are `layer1, layer3`

Three architecturally natural options exist for a 3-service chain:

| Option | Split Points     | Segments                            | Activation Transfers |
| ------ | ---------------- | ----------------------------------- | -------------------- |
| A      | `layer1, layer2` | `[stem+L1]`, `[L2]`, `[L3+L4+tail]` | 784 KB, 392 KB       |
| B      | `layer1, layer3` | `[stem+L1]`, `[L2+L3]`, `[L4+tail]` | 784 KB, 196 KB       |
| C      | `layer2, layer3` | `[stem+L1+L2]`, `[L3]`, `[L4+tail]` | 392 KB, 196 KB       |

Option B (`layer1, layer3`) is preferred because:

- It gives the most balanced compute distribution: each segment contains either 1 coarse stage + stem, 2 coarse stages, or 1 coarse stage + tail.
- It avoids the highly imbalanced segments that Option A would create (segment 2 = one stage, segment 3 = three stages + tail).
- It creates a progression that expands naturally to the 4-service and 5-service configurations.

This is a judgment call, not a mathematical optimum. The primary purpose is a clean, interpretable service-count progression — not optimal partition balancing.

---

## 4. Execution Architecture

### Forwarding Model: Service-Side Forwarding

**Decision: Service-side forwarding, not client-side chaining.**

In service-side forwarding, the client sends the raw input tensor to Service 1. Service 1 computes its segment and forwards the intermediate to Service 2 via gRPC. This continues through the chain. The final service returns its output back through the chain. The client receives the final inference result.

```
Client Pod                    Svc-1             Svc-2             Svc-3
    │                          │                  │                  │
    │───InferRequest(input)───→│                  │                  │
    │                          │─compute segment──│                  │
    │                          │───ForwardInfer──→│                  │
    │                          │                  │─compute segment──│
    │                          │                  │───ForwardInfer──→│
    │                          │                  │                  │─compute segment─
    │                          │                  │                  │─serialize output─
    │                          │                  │←──InferResponse──│
    │                          │←──InferResponse──│                  │
    │←──InferResponse──────────│                  │                  │
```

**Why not client-side chaining?**

In client-side chaining, the client would call Service 1, receive the intermediate tensor back, then call Service 2 with it, and so on. This is rejected because:

1. **The proposal says** "intermediate activations are forwarded synchronously from one coarse-stage segment to the next." This describes in-chain forwarding — intermediates flow through the chain, not back to the client between hops.
2. **Client-side chaining adds unnecessary overhead.** Every intermediate exits and re-enters the cluster (if the client is external) or at minimum traverses an extra network hop to/from the client pod. This does not model a real microservice pipeline.
3. **In-chain forwarding reflects realistic deployment.** In production microservice pipelines, data flows through the chain; the orchestrating client only sees the final result.
4. **Measurement is cleaner.** Client-side chaining conflates boundary-crossing cost with client-to-cluster round-trip cost. In-chain forwarding isolates the per-boundary cost within the cluster.

### Request Path (Detailed)

For a `chain_3svc` configuration with split points `[layer1, layer3]`:

1. **Client** serializes raw input tensor (1×3×224×224) → sends `InferRequest` to Service 1 via gRPC.
2. **Service 1** deserializes input → runs stem + layer1 → serializes intermediate (1×64×56×56) → sends `InferRequest` to Service 2.
3. **Service 2** deserializes intermediate → runs layer2 + layer3 → serializes intermediate (1×256×14×14) → sends `InferRequest` to Service 3.
4. **Service 3** deserializes intermediate → runs layer4 + avgpool + fc → serializes output (1×1000) → returns `InferResponse` to Service 2.
5. **Service 2** receives response from Service 3 → appends its own hop timing → returns `InferResponse` to Service 1.
6. **Service 1** receives response from Service 2 → appends its own hop timing → returns `InferResponse` to Client.
7. **Client** receives final response. Extracts output tensor and accumulated hop timings.

### Timing Boundaries

**End-to-end timing (at client):**

```
t_start = immediately before client serializes input for gRPC call to Service 1
t_end   = immediately after client deserializes final response from Service 1
end_to_end_ms = (t_end - t_start) × 1000
```

**Per-hop server-side timing (at each service):**

Each service records:

- `deserialize_ms`: time to deserialize the incoming tensor from bytes
- `compute_ms`: time for the model segment forward pass
- `serialize_ms`: time to serialize the outgoing tensor to bytes
- `forward_ms`: time spent waiting for the downstream service response (0 for the last service)

These are accumulated in the response via a repeated `HopTiming` list and returned to the client.

**What is included in `end_to_end_ms`:**

- All model computation across all services
- All serialization and deserialization at every boundary
- All gRPC framework overhead (framing, scheduling, transport)
- All in-cluster network latency between pods
- Container runtime scheduling overhead
- Client-side request serialization and response deserialization

**What is excluded:**

- Model loading (happens at pod startup)
- Warmup iterations (excluded from measured data)
- Kubernetes control-plane operations (deployment, scheduling of pods)
- Pod startup time

### Monolithic K8s Baseline Request Path

For `monolithic_k8s_1svc`:

1. **Client** serializes raw input tensor → sends `InferRequest` to the monolithic service pod.
2. **Monolithic service** deserializes input → runs full ResNet-18 → serializes output → returns `InferResponse`.
3. **Client** deserializes response.

This captures the same Kubernetes deployment context (container, in-cluster gRPC, ClusterIP networking) as the chain conditions, with zero internal service boundaries. The overhead of chain conditions relative to this baseline is therefore attributable to additional service boundaries.

### Why the Client Must Also Run Inside the Cluster

If the client ran outside the cluster (e.g., on the host machine), it would add external-to-cluster network overhead that varies independently of the in-chain boundary cost. By running the client as a Kubernetes pod (or Job) in the same cluster, all conditions experience the same pod-to-pod communication context.

### Service Discovery

Each chain service is exposed as a Kubernetes `ClusterIP` Service with a stable DNS name (e.g., `chain-svc-1.rq14.svc.cluster.local`). Each service is configured with the DNS name of the next service in the chain via environment variable or command-line argument. The last service has no next-hop target.

---

## 5. Measurement Contract

### Primary Metric

**Mean end-to-end inference latency (ms)** — measured at the client pod, from immediately before the input is sent to Service 1 to immediately after the final response is received.

This is the same primary metric as RQ1.1 and RQ1.2. It captures the full cost of inference as seen by a caller, including all computation, serialization, in-cluster transport, and service-boundary overhead.

### Secondary Metrics

| Metric                   | Type          | Description                                                                            |
| ------------------------ | ------------- | -------------------------------------------------------------------------------------- |
| `median_end_to_end_ms`   | Summary       | Robust central tendency                                                                |
| `p95_end_to_end_ms`      | Summary       | Tail behavior                                                                          |
| `std_end_to_end_ms`      | Summary       | Variability                                                                            |
| `total_compute_ms`       | Per-iteration | Sum of all server-reported `compute_ms` across hops                                    |
| `total_activation_bytes` | Per-iteration | Sum of activation bytes transferred across all boundaries                              |
| `num_hops`               | Per-iteration | Number of gRPC boundaries crossed (= num_services - 1 for chain, 1 for monolithic K8s) |

### Derived Metric: Non-Compute Overhead

```
non_compute_overhead_ms = end_to_end_ms - total_compute_ms
```

**Naming rationale:** This metric captures everything that is not model computation: serialization, deserialization, gRPC framing, in-cluster network transport, container scheduling, OS scheduling, and any other runtime overhead. It is honest to call this "non-compute overhead" rather than "boundary crossing" or "communication cost" because:

1. In the local stage, `boundary_crossing_ms` was a client-side interval from serialization start to response deserialization end. In the chain, the client only sees the first and last hop — it cannot directly measure per-hop boundary-crossing intervals.
2. The residual `end_to_end - total_compute` includes Kubernetes-specific overhead (pod scheduling, container runtime) that is not purely "communication."
3. Calling it "non-compute overhead" avoids overstating what the metric isolates.

### Per-Hop Diagnostic Metrics

For each hop `i` (1-indexed), the following are recorded from server-reported timing:

| Metric                     | Description                                                       |
| -------------------------- | ----------------------------------------------------------------- |
| `hop_{i}_compute_ms`       | Server-side model segment forward pass time                       |
| `hop_{i}_deserialize_ms`   | Server-side tensor deserialization time                           |
| `hop_{i}_serialize_ms`     | Server-side tensor serialization time                             |
| `hop_{i}_forward_ms`       | Server-side time waiting for downstream response (0 for last hop) |
| `hop_{i}_activation_bytes` | Bytes of the activation tensor received at this hop               |

These are **diagnostic**, not thesis-facing primary metrics. They support interpretation but should not carry main claims.

### Cross-Condition Analysis

| Analysis                                    | Description                                                    |
| ------------------------------------------- | -------------------------------------------------------------- |
| Overhead vs monolithic K8s baseline (ms, %) | Primary comparison: `chain_mean - monolithic_k8s_mean`         |
| Marginal cost per additional boundary       | `overhead(N) - overhead(N-1)` for each step in the progression |
| Cohen's d (each chain vs monolithic K8s)    | Effect magnitude                                               |
| Cross-round consistency (CV of round means) | Stability evidence, same as RQ1.1                              |
| Total activation bytes vs overhead scatter  | Same analysis as RQ1.1 but with cumulative activation transfer |

### Per-Iteration CSV Schema

The `raw_iterations.csv` file will contain one row per measured iteration with these columns:

```
round, condition, iteration,
end_to_end_ms, total_compute_ms, non_compute_overhead_ms,
total_activation_bytes, num_hops,
hop_1_compute_ms, hop_1_deserialize_ms, hop_1_serialize_ms, hop_1_forward_ms, hop_1_activation_bytes,
hop_2_compute_ms, hop_2_deserialize_ms, hop_2_serialize_ms, hop_2_forward_ms, hop_2_activation_bytes,
...
```

For the monolithic K8s baseline, there is 1 hop (client → monolithic service → client). The `hop_1_*` fields record the monolithic service's internal timing. `hop_2_*` through `hop_N_*` are 0.

For chain conditions, `hop_1_*` through `hop_N_*` are populated. Unused hop columns beyond `num_hops` are 0.

Maximum hop count is 5 (for `chain_5svc`).

### Comparability with Local Stage

| Aspect         | Local (RQ1.1/RQ1.2)           | Kubernetes (RQ1.4)             | Compatible?                                                   |
| -------------- | ----------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Primary metric | `end_to_end_ms` (client-side) | `end_to_end_ms` (client pod)   | Yes (same name, same semantics)                               |
| Baseline       | Local monolithic (in-process) | K8s monolithic (1-service pod) | Different baselines — intentional                             |
| Overhead       | vs local monolithic           | vs K8s monolithic              | Comparable within stage; cross-stage comparison is discussion |
| Repetition     | 5 rounds × 200 iterations     | 5 rounds × 200 iterations      | Yes                                                           |
| Warmup         | 50 iterations, CV calibration | 50 iterations, CV calibration  | Yes                                                           |
| Parity         | atol=1e-5, 5 inputs           | atol=1e-5, 5 inputs            | Yes                                                           |

Cross-stage comparison (local vs K8s absolute latencies) is explicitly a **thesis discussion** topic, not a direct experimental comparison. The local and K8s stages have different deployment contexts and different baselines. Within-stage relative comparisons (e.g., "how much does adding one more service boundary increase overhead?") are the primary RQ1.4 claims.

---

## 6. Parity, Warmup, and Reproducibility

### Parity Validation

**Phase 1 — Local segment validation (pre-deployment):**

Before deploying anything to Kubernetes, validate locally that chaining all N model segments produces numerically equivalent output to monolithic ResNet-18. This uses the same `validate_equivalence()` pattern from RQ1.1 but extended to N-way segment chains.

- Tolerance: `atol = 1e-5`
- Inputs: 5 deterministic test inputs
- Fail-closed: if any segment chain fails, abort deployment

**Phase 2 — Live chain validation (post-deployment):**

After all pods are running and ready, send test inputs through the full deployed chain and compare the final output against monolithic. This validates end-to-end gRPC chain correctness including serialization round-trips.

- Run once before the first measurement round
- Fail-closed: if the chain output diverges, abort the experiment

**Phase 3 — Per-round gRPC parity (round 1 only):**

Same as RQ1.1: run gRPC parity check for each chain condition in round 1 after warmup pod readiness is confirmed. Record results in `parity_validation.json`.

### Warmup Policy

**Same calibrated warmup as RQ1.1:**

- `warmup_iterations = 50` per condition per round
- `window = 10`, `cv_threshold = 0.02`
- Warmup inferences traverse the full chain (all hops). This warms up:
  - Model computation in each service pod
  - gRPC connections between pods
  - In-cluster DNS resolution and connection pooling
  - Container runtime caches
- All warmup iterations are discarded from measurement
- Warmup calibration metadata recorded in `warmup_calibration.json`

### Repeated Runs

| Parameter                               | Value | Same as RQ1.1? |
| --------------------------------------- | ----- | -------------- |
| Rounds                                  | 5     | Yes            |
| Measured iterations per round×condition | 200   | Yes            |
| Total per condition                     | 1,000 | Yes            |
| Total iterations (5 conditions)         | 5,000 | Same scale     |

### Condition Ordering

Randomized per round using seeded `Random(seed + round_num)`. Same strategy as RQ1.1.

### Cooldown

5 seconds between conditions within a round. Same as RQ1.1.

### Pod Lifecycle During Experiment

**All service pods remain running throughout the entire experiment.** Pods are not restarted between rounds or conditions.

Rationale:

- Restarting pods between conditions would introduce model-reload and JIT re-warmup confounds.
- The warmup phase at the start of each condition×round handles stabilisation.
- Pod restart would add significant wall-clock experiment time.

**If a pod crashes during the experiment, abort and rerun from scratch.** Partial results from crashed experiments are not used.

### Pod Deployment Between Conditions

For different chain conditions (e.g., `chain_2svc` vs `chain_3svc`), the service topology changes. This requires deploying different pod sets between conditions.

**Strategy:** Deployment and teardown must never occur inside the measured iteration loop, but simultaneous pre-deployment of all configurations is not required. A configuration may be deployed and warmed before its measurement block begins, as long as deployment/startup time is excluded from measured latency and the benchmark remains fair and reproducible.

Concretely, the runner may either:

1. **Pre-deploy all configurations** before the experiment starts (simplest if cluster resources allow), or
2. **Deploy each configuration just before its first measurement block** in a given round, completing deployment, readiness checks, and warmup before any measured iteration begins. Teardown of the previous configuration may happen during cooldown.

Both approaches are valid as long as:

- No pod deployment or teardown occurs during the measured iteration window.
- Warmup is run after deployment and before measurement.
- Condition ordering remains randomized per round.
- The approach used is recorded in the experiment metadata.

**Why not require simultaneous pre-deployment:** Deploying all 1/2/3/4/5-service configurations at once may create unnecessary cluster resource pressure, complicate pod placement, and increase baseline variance from contention. Per-condition deploy-then-measure is simpler to manage and avoids these issues while preserving fairness.

**What is NOT acceptable:** Deploying or tearing down pods during the measured iteration loop. This would inject pod startup latency into measurements and break timing boundaries.

### Environment Metadata

**Cluster-level (recorded once):**

- Kubernetes server version
- Node count, instance types, CPU/memory per node
- CNI plugin
- DNS provider (CoreDNS version)
- Storage class (if relevant)
- Cluster type (Minikube, kind, kubeadm, etc.)

**Pod-level (recorded per service):**

- Container image version / digest
- Resource requests and limits (CPU, memory)
- QoS class (should be Guaranteed)
- Node placement (which node each pod landed on)
- Thread settings (env vars propagated)
- Python and PyTorch versions (from container)

**Client pod (recorded once):**

- Same environment metadata as RQ1.1 (`environment.json`)
- Plus: cluster name, namespace, pod name, node placement
- Plus: a service topology snapshot listing all deployed services and their endpoints

### CPU Stabilisation in Kubernetes

**What transfers directly:**

| Control                                     | Mechanism in K8s | Notes                                             |
| ------------------------------------------- | ---------------- | ------------------------------------------------- |
| Thread counts (OMP, MKL, OpenBLAS, PyTorch) | Pod env vars     | Identical to local stage. Set in Deployment spec. |
| PyTorch intra/inter-op threads              | Pod env vars     | Same.                                             |

**What requires K8s-level equivalents:**

| Control                | Local mechanism          | K8s equivalent                                                                                     | Notes                                                                  |
| ---------------------- | ------------------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| CPU affinity (pinning) | `os.sched_setaffinity()` | `resources.requests.cpu == resources.limits.cpu` with integer values + `static` CPU manager policy | Provides exclusive CPU allocation. Requires node-level kubelet config. |
| Process priority       | `os.nice(-5)`            | Guaranteed QoS class                                                                               | K8s does not expose nice values. Guaranteed QoS prevents preemption.   |
| CPU governor           | sysfs write              | Node-level DaemonSet or provisioning script                                                        | Cannot set from within a container without privileges.                 |
| Turbo boost            | sysfs write              | Node-level tuning                                                                                  | Same limitation.                                                       |

**Recommended K8s stabilisation approach (phased):**

1. **Mandatory (day one):** Thread counts via env vars. Resource requests == limits (Guaranteed QoS). Integer CPU values.
2. **Recommended (before thesis-facing runs):** Static CPU manager policy on nodes. Node-level governor + turbo tuning via DaemonSet if possible.
3. **Optional (only if variance is problematic):** Pod anti-affinity to spread services across nodes. Dedicated node pool with tuned kernel parameters.

**Documented limitations:** The thesis should explicitly note which stabilisation controls were active in the K8s environment and which were best-effort. This is part of the honest comparison between the controlled local stage and the K8s stage.

---

## 7. Codebase Reuse Map

### Direct Reuse (No Changes)

| Component               | File                                               | Notes                                                                 |
| ----------------------- | -------------------------------------------------- | --------------------------------------------------------------------- |
| Timer                   | `src/benchmark/timer.py`                           | Transport-agnostic                                                    |
| Warmup calibration      | `src/benchmark/warmup.py`                          | Accepts any `infer_fn(tensor)` callable                               |
| Artifact logger         | `src/benchmark/logging.py`                         | All file I/O unchanged                                                |
| Monolithic client       | `src/client/monolithic.py`                         | Not used directly in K8s conditions, but pattern is referenced        |
| Local parity validation | `src/models/validation.py`                         | Pre-flight local validation of segment chains                         |
| Full model loader       | `src/models/resnet_splits.py` → `get_full_model()` | Unchanged                                                             |
| Statistics core         | `src/analysis/statistics.py`                       | All summary/cross-condition functions work on any condition-based CSV |
| Existing plots          | `src/analysis/plots.py`                            | Box/violin/stationarity plots apply unchanged                         |
| Run analysis pipeline   | `run_analysis.py`                                  | Works on any `raw_iterations.csv` with extended columns               |
| Existing configs        | `configs/rq1/1.1/`, `configs/rq1/1.2/`             | Untouched                                                             |
| Frozen results          | `results/frozen/`                                  | Untouched                                                             |

### Minimal Extensions

| Component         | File                                 | Change                                                                                                                                                                           |
| ----------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model splits      | `src/models/resnet_splits.py`        | Add `ModelSegment` class and `get_chain_segments(split_points)` function. Reuses existing `_parse_split_point()` and module-building patterns from `PartA`/`PartB`.              |
| Config dataclass  | `src/benchmark/config.py`            | Add `type="chain"` with `chain_split_points: List[str]` to `ConditionConfig`. Add optional `kubernetes` config section. No changes to existing `"monolithic"` / `"split"` paths. |
| Proto             | `proto/inference.proto`              | Add `HopTiming` message and `repeated HopTiming hop_timings` field to `InferResponse`. Backward-compatible: existing code ignores the new field.                                 |
| CPU stabilisation | `src/benchmark/cpu_stabilisation.py` | Thread-count logic reused directly. Add K8s environment detection (optional: detect if running in a container and skip sysfs controls gracefully).                               |
| Parity validation | `src/models/validation.py`           | Add `validate_chain_equivalence(split_points_list)` that validates N-segment chains against monolithic.                                                                          |

### New Components

| Component                  | File                                   | Purpose                                                                                                                                                            |
| -------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Chain service              | `src/services/chain_service.py`        | Generic gRPC servicer: receives tensor → runs model segment → forwards to next service or returns. Accumulates `HopTiming` list.                                   |
| Chain service runner       | `src/services/chain_service_runner.py` | CLI entrypoint for each pod. Accepts `--segment-index`, `--split-points`, `--next-hop`.                                                                            |
| Chain client               | `src/client/chain_client.py`           | Client that sends input to Service 1, receives final response with accumulated hop timings, extracts metrics.                                                      |
| K8s benchmark runner       | `src/benchmark/k8s_runner.py`          | Measurement loop for K8s: assumes pre-deployed pods, uses `ChainClient` for chain conditions, monolithic K8s service for baseline. Same round×condition structure. |
| K8s experiment entry point | `run_k8s_experiment.py`                | CLI: load config → validate segments → check pod readiness → live parity → run benchmark → collect results.                                                        |
| K8s config                 | `configs/rq1/1.4/*.yaml`               | RQ1.4 experiment configs (smoke test + full).                                                                                                                      |
| K8s manifests              | `k8s/rq1_4/`                           | Deployment + Service YAML for each configuration.                                                                                                                  |
| Dockerfile                 | `Dockerfile`                           | Single container image for all segments (segment selected at runtime via args).                                                                                    |

### What MUST Stay Unchanged

- `run_experiment.py` — local RQ1.1/RQ1.2 entry point
- `src/benchmark/runner.py` — local benchmark runner
- `src/client/split_client.py` — local split client
- `src/services/service_b.py` — local Service B
- All files under `results/frozen/`
- All files under `configs/rq1/1.1/` and `configs/rq1/1.2/`
- `building_plans/RQ1_1_Experimental_Design.md` and `RQ1_2_Experimental_Design.md`

---

## 8. RQ1.5 Migration-Readiness

### Design Principle

> Build RQ1.4 as the local Kubernetes reference implementation that RQ1.5 can later carry to Azure AKS with minimal architectural rework.

### What Is Kept Portable

| Component               | Portability approach                                                                                                                                                        |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **gRPC chain services** | Container image is cluster-agnostic. Same image runs on local K8s and AKS.                                                                                                  |
| **K8s manifests**       | Use standard Kubernetes API resources (Deployment, Service, Namespace). No cluster-distribution-specific extensions (no Minikube tunnels, no kind-specific load balancers). |
| **Experiment configs**  | Service endpoints are config-driven (`kubernetes.namespace`, `kubernetes.service_base_name`). No hardcoded hostnames or IPs.                                                |
| **Benchmark runner**    | `K8sBenchmarkRunner` communicates via Kubernetes DNS names. Works identically on any cluster where pods are reachable by ClusterIP.                                         |
| **Analysis pipeline**   | Fully decoupled from deployment. Operates on `raw_iterations.csv` regardless of where the data was collected.                                                               |
| **Parity validation**   | Same protocol locally and in-cluster.                                                                                                                                       |

### What Must Be Config-Driven (Not Hardcoded)

| Setting                     | Where configured                                   | Notes                                                  |
| --------------------------- | -------------------------------------------------- | ------------------------------------------------------ |
| Kubernetes namespace        | Config YAML `kubernetes.namespace`                 | Different for local vs AKS                             |
| Container image registry    | Config YAML or manifest overlay                    | Local: loaded directly. AKS: pushed to ACR.            |
| Service DNS names           | Derived from `kubernetes.namespace` + service name | Standard K8s DNS resolution                            |
| Resource requests/limits    | Manifest or config                                 | May differ between local and AKS node types            |
| Node affinity / tolerations | Manifest overlay                                   | AKS-specific node pools                                |
| Storage for results         | Config or volume mount                             | Local: hostPath or emptyDir. AKS: Azure Files or blob. |

### What Should Be Environment-Specific but Isolated

| Concern                   | RQ1.4 (local K8s)                 | RQ1.5 (AKS)                       | Isolation mechanism           |
| ------------------------- | --------------------------------- | --------------------------------- | ----------------------------- |
| Cluster provisioning      | Minikube/kind start script        | `az aks create` / Terraform       | Separate from experiment code |
| Image registry            | Local build + load                | ACR push                          | Makefile/script target        |
| Node-level tuning         | DaemonSet or manual               | AKS node pool config              | Separate manifest overlay     |
| Result collection         | Local filesystem                  | Azure Files mount or `kubectl cp` | Config-driven output path     |
| Ingress / external access | Not needed (client is in-cluster) | Not needed (client is in-cluster) | Same                          |

### What Should NOT Be Hardcoded to Local Kubernetes

- `127.0.0.1` or `localhost` for service endpoints (use K8s DNS)
- Minikube-specific `minikube tunnel` or `minikube service` commands
- kind-specific port mappings
- Host-path volume mounts for results (use emptyDir or PVC)
- Assumptions about node count or node capacity

### How Experiment Definitions Stay Reusable

The config YAML defines the experiment (conditions, repetition, metrics). Deployment details are in a separate `kubernetes` section or in manifest files. For RQ1.5, the experiment section stays identical; only the `kubernetes` section and manifests change.

```yaml
# Same for local K8s and AKS:
experiment:
  name: "RQ1.4 ..."
conditions:
  - name: "chain_3svc"
    type: "chain"
    chain_split_points: ["layer1", "layer3"]
benchmark:
  rounds: 5
  measured_iterations: 200
  ...

# Different per environment:
kubernetes:
  namespace: "rq14"                    # or "rq15-aks"
  image: "thesis-inference:latest"     # or "myacr.azurecr.io/thesis-inference:v1"
  ...
```

### Metadata / Logging Design for Local vs AKS Comparison

The `environment.json` artifact should include a `deployment` section that captures:

```json
{
  "deployment": {
    "type": "kubernetes",
    "cluster_type": "minikube",
    "cluster_version": "v1.30.0",
    "node_count": 1,
    "node_instance_type": "local",
    "cni": "kindnet",
    "namespace": "rq14",
    "pod_placement": {
      "chain-svc-1": "minikube-node-1",
      "chain-svc-2": "minikube-node-1"
    }
  }
}
```

For AKS, this becomes:

```json
{
  "deployment": {
    "type": "kubernetes",
    "cluster_type": "aks",
    "cluster_version": "v1.30.0",
    "node_count": 3,
    "node_instance_type": "Standard_D4s_v5",
    "cni": "azure-cni",
    "namespace": "rq15",
    "pod_placement": {
      "chain-svc-1": "aks-nodepool1-12345-vmss000000",
      "chain-svc-2": "aks-nodepool1-12345-vmss000001"
    }
  }
}
```

This structured metadata enables direct comparison in the thesis discussion.

### Cluster-Agnostic Implementation Constraint

The Python experiment code (runner, client, analysis) must rely only on:

- Config-driven parameters (namespace, service names, ports)
- Standard Kubernetes DNS for service discovery (e.g., `chain-svc-1.rq14.svc.cluster.local`)
- gRPC readiness checks for pod liveness
- Standard filesystem paths for result output

The experiment code must **not** contain:

- Hardcoded `127.0.0.1` or `localhost` for K8s service endpoints
- Minikube-specific commands (`minikube tunnel`, `minikube service`)
- kind-specific port mappings or network hacks
- Cluster-distribution-specific shell invocations inside core runner code

Environment-specific deployment helpers (e.g., scripts to start Minikube, build/load images, apply manifests) may exist as separate utility scripts but must not be embedded in the experiment logic. This ensures that RQ1.5 can reuse the same runner and client code on AKS by changing only config and manifests.

---

## 9. Rejected Alternatives

### Alternative A: Block-Level Chaining

**Description:** Use block-level split points (e.g., `layer3.0`) in multi-service chains.

**Why rejected:** RQ1.4 is explicitly "coarse architectural stages." Block-level refinement was RQ1.2's concern. Including block-level splits in chained configurations would conflate service-count effects with granularity effects and make the experiment harder to interpret.

### Alternative B: Client-Side Chaining

**Description:** Client calls Service 1, gets intermediate back, calls Service 2, etc.

**Why rejected:** The proposal says "forwarded synchronously from one coarse-stage segment to the next." Client-side chaining adds unnecessary client round-trips, doesn't model real microservice pipelines, and conflates boundary cost with client-to-service transport cost. See Section 4 for full reasoning.

### Alternative C: Local Monolithic as Primary Baseline

**Description:** Use the same in-process monolithic baseline from RQ1.1 as the primary RQ1.4 comparison.

**Why rejected:** The local monolithic has zero container overhead, zero network overhead, and zero gRPC overhead. Comparing chain conditions (with all these overheads) against a local monolithic would measure "Kubernetes + chain overhead" conflated together. The K8s monolithic 1-service baseline isolates the effect of additional service boundaries by keeping the deployment context constant.

The frozen local monolithic results remain available for cross-stage discussion in the thesis, but they are not the primary RQ1.4 baseline.

### Alternative D: Too Many Configurations

**Description:** Add configurations with different split-point combinations at the same service count (e.g., multiple 3-service options).

**Why rejected:** RQ1.4's independent variable is service count. Testing multiple partition choices at the same service count would turn it into another split-selection study. One architecturally natural choice per service count is sufficient and keeps the experiment interpretable.

### Alternative E: Combined Kubernetes + Azure Stage

**Description:** Run RQ1.4 and RQ1.5 as a single combined experiment.

**Why rejected:** The proposal separates these into distinct sub-questions. RQ1.4 is "in-cluster Kubernetes." RQ1.5 is "Azure AKS validation." Combining them would bloat scope, delay results, and conflate local-cluster findings with cloud-specific effects.

### Alternative F: Adding Security Mechanisms

**Description:** Introduce mTLS or encryption in RQ1.4.

**Why rejected:** Security is RQ2's concern. RQ1.4 measures baseline partitioning overhead without security. This provides the clean non-secure baseline that RQ2 will later compare against.

### Alternative G: Local-Cluster-Specific Shortcuts

**Description:** Use Minikube tunnels, localhost port-forwarding, or kind-specific networking to simplify RQ1.4.

**Why rejected:** These create refactoring pain when migrating to AKS for RQ1.5. The design should use standard Kubernetes patterns (ClusterIP Services, DNS-based discovery, in-cluster client) that work identically on any conformant Kubernetes cluster.

### Alternative H: Reopening Local Subprocess Comparisons

**Description:** Re-run local subprocess-based split experiments for comparison.

**Why rejected:** The local stage is frozen. RQ1.4 is the Kubernetes stage. Cross-stage comparison (local vs K8s) uses the frozen results directly and is handled as thesis discussion, not a new experiment.

### Alternative I: Helm / Kustomize / Complex Deployment Tooling

**Description:** Use Helm charts or Kustomize overlays for deployment management.

**Why rejected for day one:** Adds tooling complexity without immediate experimental value. Plain YAML manifests with a simple generation script are sufficient for 5 configurations. If RQ1.5 needs more sophisticated deployment management, it can be added then. The manifests should be structured so that Kustomize overlays or Helm templating can be added later without restructuring.

---

## 10. Implementation Roadmap

### Phase 1: N-Way Model Segmentation

**Goal:** Extend `resnet_splits.py` with `get_chain_segments()` that produces N+1 model segments from N split points.

**Validation:** Local test that chaining all segments produces identical output to `get_full_model()` for all 5 RQ1.4 configurations.

**Deliverable:** `ModelSegment` class, `get_chain_segments()` function, local validation test.

### Phase 2: Proto Extension

**Goal:** Add `HopTiming` message to `inference.proto`. Regenerate Python stubs.

**Validation:** Verify that existing RQ1.1/RQ1.2 code still works (backward-compatible field addition).

**Deliverable:** Updated `inference.proto`, regenerated `inference_pb2.py` and `inference_pb2_grpc.py`.

### Phase 3: Chain Service Implementation

**Goal:** Implement `ChainServicer` — a generic gRPC service that loads a model segment, computes, and optionally forwards to the next service.

**Validation:** Test locally with 2+ processes mimicking a chain (before Kubernetes).

**Deliverable:** `src/services/chain_service.py`, `src/services/chain_service_runner.py`.

### Phase 4: Chain Client Implementation

**Goal:** Implement `ChainClient` that sends input to Service 1 and extracts per-hop timing from the response.

**Validation:** Test locally against the multi-process chain from Phase 3.

**Deliverable:** `src/client/chain_client.py`.

### Phase 5: Config Extension

**Goal:** Extend `ConditionConfig` to support `type="chain"` with `chain_split_points`. Create RQ1.4 config YAML files.

**Deliverable:** Updated `src/benchmark/config.py`, `configs/rq1/1.4/rq1_4_smoke.yaml`, `configs/rq1/1.4/rq1_4_full.yaml`.

### Phase 6: Local Multi-Process Smoke Test

**Goal:** Run the full chain pipeline locally (multiple processes, localhost gRPC) before introducing Kubernetes. Validate parity, warmup, and metric collection.

**Deliverable:** Confirmed correct CSV output from a local multi-process chain run.

### Phase 7: K8s Benchmark Runner

**Goal:** Implement `K8sBenchmarkRunner` that assumes pre-deployed pods and runs the same round×condition measurement loop.

**Deliverable:** `src/benchmark/k8s_runner.py`, `run_k8s_experiment.py`.

### Phase 8: Containerisation

**Goal:** Create `Dockerfile` for a single image that can run any model segment based on CLI args.

**Validation:** `docker build` + `docker run` with segment args.

**Deliverable:** `Dockerfile`, `docker-compose.yml` or build script (optional).

### Phase 9: K8s Manifests

**Goal:** Create Deployment + Service YAML for each RQ1.4 configuration. Ensure portability and migration-friendly structure.

**Directory structure:** Manifests are organised with a base/environment split to support later AKS migration without restructuring:

```
k8s/
  base/          # Shared Deployment/Service templates, configmaps
  local/         # Local-cluster overrides (resource sizes, image pull policy, etc.)
  aks/           # (Added later for RQ1.5) AKS-specific overrides
```

On day one, `base/` contains the canonical manifests and `local/` contains only the minimal overrides needed for the local cluster. No Helm or Kustomize tooling is required — plain YAML with a simple generation script is sufficient. The structure is chosen so that Kustomize overlays can be adopted later without restructuring.

**Deliverable:** `k8s/base/` and `k8s/local/` directories with manifests.

### Phase 10: K8s Smoke Test

**Goal:** Deploy to local K8s (Minikube or kind), run parity validation, run 1-round smoke experiment.

**Validation:** CSV output matches expected schema, parity passes, metrics are sensible.

### Phase 11: Full RQ1.4 Experiment

**Goal:** Run the thesis-facing experiment: 5 rounds × 200 iterations × 5 conditions on the target K8s cluster.

**Deliverable:** Frozen `raw_iterations.csv`, analysis artifacts, report.

---

## 11. Design Decision Record

| #   | Decision                                                                    | Rationale                                                                                                            | Status   |
| --- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------- |
| D1  | Service-side forwarding (not client-side chaining)                          | Matches proposal wording; models real pipelines; cleaner measurement                                                 | Accepted |
| D2  | K8s monolithic 1-service baseline (not local in-process)                    | Isolates service-boundary effect from container/network effect                                                       | Accepted |
| D3  | Deploy/teardown outside measured loop; simultaneous pre-deploy not required | Avoids startup noise in measurements; reduces cluster resource pressure                                              | Revised  |
| D4  | 5 conditions (1+2+3+4+5 services)                                           | Maximum clean progression at coarse granularity                                                                      | Accepted |
| D5  | Same repetition structure as RQ1.1 (5×200)                                  | Preserves comparability and statistical power                                                                        | Accepted |
| D6  | Single container image for all segments                                     | Simplifies build/deploy; segment selected at runtime                                                                 | Accepted |
| D7  | `non_compute_overhead_ms` naming (not "boundary crossing")                  | Honest: the residual includes more than just communication                                                           | Accepted |
| D8  | No Helm/Kustomize on day one                                                | Reduces tooling complexity; plain YAML is sufficient for 5 configs                                                   | Accepted |
| D9  | Config-driven service discovery (DNS, not hardcoded IPs)                    | Portability for RQ1.5 AKS migration                                                                                  | Accepted |
| D10 | Client runs inside the cluster                                              | All conditions share the same network context                                                                        | Accepted |
| D11 | Experiment code is cluster-agnostic                                         | Python runner relies only on K8s DNS, config, and standard APIs; no cluster-distribution-specific logic in core code | Accepted |
| D12 | Manifest structure supports future AKS overlays                             | `k8s/base/` + `k8s/local/` split; no Helm/Kustomize day one but migration-friendly layout                            | Accepted |
