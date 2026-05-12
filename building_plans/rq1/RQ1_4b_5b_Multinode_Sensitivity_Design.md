# RQ1.4b / RQ1.5b Experimental Design

## Multi-Node Sensitivity Validation of the Chain Family

---

## Design Recommendation — Sensitivity Stage, Not Replacement

**Decision: RQ1.4b and RQ1.5b are *additional* sensitivity stages. They do not replace the frozen RQ1.4 (kind, single-node) or RQ1.5 (AKS, single-node) primary results.**

The frozen single-node runs remain the thesis-facing primary numbers because RQ1.4 and RQ1.5 were framed as directional-transfer studies under controlled topology. Replacing them would invalidate the existing chapter and the RQ2 paired baselines that depend on them.

The role of 1.4b and 1.5b is narrower and self-contained: **measure, in milliseconds, the inter-node penalty that the single-node design intentionally hides.** This converts the "single-node deployment" threat in the evaluation chapter from "unknown magnitude" into a bounded, measured number, paired condition-by-condition with its single-node counterpart.

### Why a sensitivity stage and not a redesign

- **Frozen results stay valid.** The thesis-facing RQ1.4 and RQ1.5 numbers, the cross-stage transfer table in [azure.tex](../../thesis/chapters/experiments/azure.tex), and the RQ2 paired comparisons are untouched.
- **The threat-section claim sharpens from negative to positive.** Instead of "we cannot rule out an inter-node penalty," the thesis can write "the inter-node penalty was measured at +X.X ms / +Y.Y pp at chain_5svc and is consistent with [kind / AKS] platform behaviour."
- **Cost is bounded.** RQ1.5b runs on 6 × Standard_D8s_v3 (48 vCPUs) for ~70 minutes per execution, with auto-teardown on success and failure. Approximate compute cost: **\$5–8 per run**. RQ1.4b on kind is free.

---

## 1. Research Question

> **RQ1.4b / RQ1.5b:** When every chain hop is forced across a node boundary, how much additional end-to-end latency does the inter-node network path add, relative to the same-node baseline measured in RQ1.4 / RQ1.5?

### Operative phrases

- **"every chain hop is forced across a node boundary"** — placement is enforced by pod anti-affinity rules. Compliance is verified post-deployment via `validate_multi_node_placement()` in [src/benchmark/deployment_metadata.py](../../src/benchmark/deployment_metadata.py); a single pair of co-located service pods aborts the run with a per-condition error message.
- **"relative to the same-node baseline"** — the comparison metric is per-condition delta, not absolute latency. The RQ1.4b numbers are subtracted from the corresponding frozen RQ1.4 numbers, condition by condition; same for RQ1.5b/RQ1.5.

### What 1.4b/1.5b are NOT

- **Not a multi-region study.** All pods stay in one region (kind's local docker network for 1.4b; westeurope for 1.5b).
- **Not a network optimisation study.** No CNI tuning, no QoS, no node SKU search. Same `Standard_D8s_v3` SKU as RQ1.5 by design.
- **Not a multi-zone study.** All AKS nodes are in the same node pool, same VNet, no availability-zone spread.
- **Not a replacement for RQ1.4 or RQ1.5.** The frozen primaries remain frozen.

---

## 2. Dependency on Earlier Stages

| Stage   | Status | Role in 1.4b / 1.5b |
|---------|--------|---------------------|
| RQ1.1   | Frozen | Defines the coarse split-point vocabulary used by the chain family. Carried unchanged. |
| RQ1.2   | Frozen | Confirms coarse boundaries are sufficient. Block-level boundaries are not introduced here. |
| RQ1.3   | Frozen | Provides the activation-transfer-size and compute-distribution lens used to interpret the inter-node penalty per condition. |
| RQ1.4   | Frozen | Direct parent of RQ1.4b. Defines conditions, image, runner, parity contract. The RQ1.4b artifact is compared to it pair-wise. |
| RQ1.5   | Frozen | Direct parent of RQ1.5b. Same relationship. |

### Inherited unchanged

- Five conditions (`monolithic_k8s_1svc`, `chain_2svc`, `chain_3svc`, `chain_4svc`, `chain_5svc`) and their split points
- Container image (`thesis-inference:latest`), proto schema, `K8sBenchmarkRunner`, `ChainClient`
- Repetition structure (5 rounds × 200 iterations)
- Warmup contract (50 iterations, CV calibration window=10, threshold=0.02, max_extra=0)
- Parity validation (atol=1e-5, num_inputs=5, fail-closed at both local-segment and live-chain layers)
- Single-threaded CPU stabilisation profile (1 thread per pod, 1 physical core pinned, SMT avoided)
- Per-pod resource profile (see §5)

### Not reopened

- Frozen RQ1.4/RQ1.5 datasets — used as the comparison reference, not re-derived.
- Carry-forward selection — already complete in RQ1.1/RQ1.2.

---

## 3. Configuration Set (Carried Forward Unchanged)

| Condition             | Services | Boundaries | Split Points                     | Service Graph                                                       |
|-----------------------|----------|------------|----------------------------------|---------------------------------------------------------------------|
| `monolithic_k8s_1svc` | 1        | 0          | —                                | `[stem → layer1 → layer2 → layer3 → layer4 → tail]`                 |
| `chain_2svc`          | 2        | 1          | `layer2`                         | `[stem → layer1 → layer2]` → `[layer3 → layer4 → tail]`             |
| `chain_3svc`          | 3        | 2          | `layer1, layer3`                 | `[stem → layer1]` → `[layer2 → layer3]` → `[layer4 → tail]`         |
| `chain_4svc`          | 4        | 3          | `layer1, layer2, layer3`         | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4 → tail]`     |
| `chain_5svc`          | 5        | 4          | `layer1, layer2, layer3, layer4` | `[stem → layer1]` → `[layer2]` → `[layer3]` → `[layer4]` → `[tail]` |

The full chain family is included rather than only `chain_5svc`. Reasons:

- **Per-condition delta is the headline metric.** A single point cannot show whether the inter-node penalty grows with hop count, dominates one specific boundary, or stays roughly flat. Five points let the thesis make a precise statement.
- **Condition cost is small.** Each rolling condition takes ~10 minutes of in-cluster time; the full family takes ~50 minutes per multi-node run. The per-condition cost is dominated by AKS provisioning and pod scheduling, not by extra benchmark seconds.
- **chain_2svc is informative on its own.** RQ1.5b empirical data (see §10) already shows chain_2svc receives the largest single→multi-node penalty, which is a finding only visible when 1→5 are all measured.

---

## 4. Execution Architecture

### Single-node baseline (recap)

In RQ1.4 / RQ1.5, all service pods plus the benchmark client are scheduled on the same node by Kubernetes pod affinity:

```
podAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          experiment-condition: <condition-name>
      topologyKey: kubernetes.io/hostname
```

Every gRPC hop is therefore intra-node loopback / cgroup-network-namespace traffic.

### Multi-node enforcement (this stage)

Each chain segment must land on a distinct node, AND the benchmark client must land on yet another distinct node. The placement strategy is `multi_node_anti_affinity` (added in [src/benchmark/config.py](../../src/benchmark/config.py)). The AKS manifest generator emits two anti-affinity terms per service deployment:

```
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          experiment-condition: <condition-name>
          workload-role: service
      topologyKey: kubernetes.io/hostname
    - labelSelector:
        matchLabels:
          workload-role: client
      topologyKey: kubernetes.io/hostname
```

The first term forces every service pod of the same condition onto a distinct node. The second term forces services to avoid the benchmark client's node. The benchmark client gets a mirror anti-affinity rule against `workload-role: service`. Both rules are evaluated at scheduling time and the result is verified after deployment by `validate_multi_node_placement()`.

### Cluster size

| Stage | Cluster | Worker nodes | vCPUs |
|---|---|---|---|
| RQ1.4b | kind (local) | 6 | host-bound |
| RQ1.5b | AKS (westeurope) | 6 × Standard_D8s_v3 | 48 |

Six worker nodes is the minimum to host `chain_5svc` (5 services + 1 dedicated client = 6 distinct nodes). For smaller conditions (`chain_2svc` with 3 pods total) the spare nodes sit idle; cluster size is fixed across conditions to keep the platform constant within a run.

### Forwarding model and image

Identical to RQ1.4 / RQ1.5. Same `thesis-inference:latest` image, same `K8sBenchmarkRunner`, same `ChainClient`, same chain service runner CLI. The only behavioural difference between same-node and multi-node mode is the affinity rule emitted by the manifest generator.

---

## 5. Resource Profile

### Why memory differs between 1.4 and 1.5 (and why 1.4b/1.5b inherit it)

| Stage  | Service memory | Client memory | Reason |
|--------|---------------|---------------|--------|
| RQ1.4  | 512Mi         | 1Gi           | kind nodes are docker containers on the developer host; 512Mi reflects the smallest memory budget that comfortably holds PyTorch (~250–350MB working set) plus headroom. |
| RQ1.5  | 1Gi           | 1Gi           | AKS managed nodes reserve ~1Gi for system daemons; 1Gi service memory is the practical floor on `Standard_D8s_v3`. |
| RQ1.4b | **512Mi**     | **1Gi**       | Inherits RQ1.4's profile so the within-environment multi-node delta is clean. |
| RQ1.5b | **1Gi**       | **1Gi**       | Inherits RQ1.5's profile so the within-environment multi-node delta is clean. |

The 1.4↔1.5 memory difference is a per-platform choice and does not contaminate either of the two within-environment comparisons (1.4↔1.4b, 1.5↔1.5b), which hold memory constant. This is documented in §3 of the thesis methods chapter. **The actual working set is ~300 MB; both 512Mi and 1Gi sit safely above it, so timing is not sensitive to which limit is configured.**

### CPU profile (uniform across 1.4, 1.4b, 1.5, 1.5b)

- 1 vCPU request == 1 vCPU limit (Guaranteed QoS)
- 1 PyTorch intra-op thread, 1 inter-op, OMP/MKL/OpenBLAS = 1
- CPU affinity to one physical core, SMT avoided (best-effort: applied where the runtime allows)
- Process priority `nice -5` requested (best-effort: AKS rejects, kind allows)

### Client placement

The client pod also requests 1 vCPU and 1Gi memory in both 1.4b and 1.5b. The client's anti-affinity rule (against `workload-role: service`) ensures it lands on a node that has no service pods of any condition, so the client→service1 hop also crosses a node boundary.

---

## 6. Pod Placement Illustration

The `chain_5svc` placement pattern under `multi_node_anti_affinity` is illustrated in [thesis/figures/tikz/background/rq15b_chain5_multinode_placement.tex](../../thesis/figures/tikz/background/rq15b_chain5_multinode_placement.tex). The figure shows the contrast with the RQ1.4 single-node placement ([rq14_chain5_kubernetes_placement.tex](../../thesis/figures/tikz/background/rq14_chain5_kubernetes_placement.tex)):

- RQ1.4 / RQ1.5: one cluster, one node, six pods inside, all gRPC arrows internal to the node.
- RQ1.4b / RQ1.5b: one cluster, six nodes, one pod per node, all gRPC arrows crossing node boundaries.

The visual contrast is intentional — every hop that was loopback in the single-node figure becomes an inter-node arrow in the multi-node figure.

---

## 7. Azure Quota and Cost (RQ1.5b only)

### vCPU footprint

6 × Standard_D8s_v3 = **48 vCPUs** for the duration of the AKS run.

### Quota dimensions to verify

```
az vm list-usage -l westeurope -o table | grep -E "Total Regional vCPUs|Standard DSv3"
```

| Quota                          | Required |
|--------------------------------|---------:|
| `Total Regional vCPUs`         | ≥ 48     |
| `Standard DSv3 Family vCPUs`   | ≥ 48     |

Subscriptions raised to ~64 vCPUs in both dimensions have ~30% headroom and will not block. The orchestrator's [azure_quota_preflight](../../scripts/run_rq15_fully_controlled.py) (in [scripts/run_rq15_fully_controlled.py](../../scripts/run_rq15_fully_controlled.py)) checks both quotas before provisioning; a quota miss aborts before any resource is created.

### Cost estimate

`6 × D8s_v3 × ~70 minutes` (provision ~10 min + 5 conditions × ~10 min + teardown ~5 min) at standard pay-as-you-go pricing in westeurope ≈ **\$5–8 per run** plus ACR + load balancer pennies.

### Auto-teardown

Both `--delete-resource-group-on-success` and `--delete-resource-group-on-failure` are passed by the wrapper. The AKS resource group is destroyed via Terraform on either path; no idle infrastructure persists after a run.

---

## 8. Validation Contract

The following gates are fail-closed in order; any miss aborts the run.

1. **Quota preflight** — checked before provisioning starts (RQ1.5b only).
2. **Local segment parity** — `_validate_chain_segments_local` in [run_k8s_experiment.py](../../run_k8s_experiment.py); `max_abs_diff = 0.0` against monolithic for all five conditions.
3. **Live chain gRPC parity** — `_validate_chain_parity` in [src/benchmark/k8s_runner.py](../../src/benchmark/k8s_runner.py); same tolerance, end-to-end through the deployed chain.
4. **Disjoint-node placement** — `validate_multi_node_placement` in [src/benchmark/deployment_metadata.py](../../src/benchmark/deployment_metadata.py). Aborts the rolling merge if any pair of service pods of the same condition share a node, or if the client co-located with any service.
5. **Cross-round consistency** — round-CV reported for each condition; not a hard gate but documented in `round_consistency.json` and the report.

### Recorded artifacts

- `raw_iterations.csv` — 5,000 rows (5 rounds × 200 iterations × 5 conditions) with full per-hop timing breakdown
- `condition_summaries.csv`, `cross_condition.csv`, `round_consistency.json`, `effect_sizes.csv`
- `parity_validation.json` (local + gRPC) and `warmup_calibration.json`
- `deployment_metadata.json` — per-condition node placement, pod IPs, image digest, QoS class
- `environment.json` — full execution environment plus a new `multi_node_validation` block when applicable
- `report.md` — auto-generated markdown summary

---

## 9. Run Procedure

### RQ1.4b (kind, local)

```pwsh
kind create cluster --name thesis-rq14b --config k8s/kind/kind-multi-node.yaml
kind load docker-image thesis-inference:latest --name thesis-rq14b

python k8s/aks/generate_aks_manifests.py `
  --config configs/rq1/1.4/rq1_4b_multinode.yaml `
  --nodepool ""
kubectl apply -f k8s/aks/generated/
kubectl wait --for=condition=Ready pod/benchmark-client -n rq14b --timeout=180s

kubectl exec -n rq14b benchmark-client -- `
  python run_k8s_experiment.py `
  --config configs/rq1/1.4/rq1_4b_multinode.yaml --run-analysis

kubectl cp rq14b/benchmark-client:/app/results/ ./results/rq1_4b_<ts>/
kind delete cluster --name thesis-rq14b
```

The AKS manifest generator is reused (with `--nodepool ""` to suppress the AKS-only `agentpool` selector) because it knows `multi_node_anti_affinity`. The local generator does not.

### RQ1.5b (AKS, westeurope)

```pwsh
python scripts/run_rq15_fully_controlled.py `
  --config configs/rq1/1.5/rq1_5b_multinode.yaml `
  --resource-group rg-thesis-rq15b `
  --cluster-name thesis-rq15b `
  --nodepool rq15bpool `
  --node-count 6 `
  --provision --push --build `
  --acr-name <your-acr> `
  --delete-resource-group-on-success `
  --delete-resource-group-on-failure
```

The orchestrator detects `placement.strategy == multi_node_anti_affinity` from the config and:
- Defaults to 6 nodes if `--node-count` is not overridden (read from `placement.min_nodes`).
- Switches the post-deployment validation from "all on one node" to "all on distinct nodes + dedicated client".
- Records the validation outcome under `environment.deployment.multi_node_validation`.

### One-shot wrapper (recommended)

```pwsh
python scripts/run_all_rq1.py --acr-name <your-acr> --only rq1_4b,rq1_5b
```

---

## 10. Threats to Validity (Stage-Specific)

1. **Same-zone, single-region.** All AKS nodes live in one node pool, one VNet, no availability-zone spread. The measured penalty is the *intra-zone* inter-node penalty. Cross-AZ or cross-region cost is not measured and is acknowledged as a future-work boundary.
2. **kind multi-node is virtual.** kind "nodes" are docker containers on the same physical host; the inter-"node" path is docker bridge networking, not real network. RQ1.4b therefore measures a *minimum* inter-node penalty — it isolates the K8s and CNI overhead component but does not capture wire latency. RQ1.5b is the AKS-side ground truth.
3. **Cluster size held constant across conditions.** All conditions run on a 6-node cluster, even when only 2 nodes are used (e.g. `monolithic_k8s_1svc`). Idle nodes consume scheduler bookkeeping but do not consume CPU on the busy nodes; this is the standard rolling-mode design used in RQ1.5.
4. **Anti-affinity is enforced at scheduling time only.** Pods that survive a node failure could in principle be re-scheduled to violate the constraint; the post-deployment validator catches this and aborts the merge. No silent drift is possible.
5. **westeurope cloud noise.** Empirically, westeurope shows higher round-to-round CV than swedencentral did in the frozen RQ1.5 era. This is documented in the evaluation chapter and does not invalidate within-environment multi-node deltas because both 1.5 and 1.5b are measured on the same region in the same period.

---

## 11. Reporting in the Thesis

The thesis evaluation chapter receives one new subsection per stage (RQ1.4b inside the Kubernetes chapter, RQ1.5b inside the Azure chapter), each containing:

1. A pointer to the placement figure (§6).
2. A per-condition table: single-node mean, multi-node mean, absolute delta, percentage delta.
3. A short interpretation paragraph: which boundary received the largest penalty, whether the trend is monotonic with hop count, whether the explanatory model from RQ1.3 (activation-transfer size + compute distribution) is consistent with the observed inter-node deltas.
4. A line in the threats-to-validity section that quotes the measured chain_5svc inter-node penalty as the bound on what RQ1.4 / RQ1.5 underestimates.

That converts the existing single-node limitation from a hedging sentence into a measured cost.
