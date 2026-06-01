# F1 / Phase 0 — Locked RQ Structure (reference for Phases 1–6)

**Decision (locked 2026-06-01):** Two top-level research questions (resolves C1). RQ2.3
folds under RQ2 as the trade-off/recommendation (resolves C8). Evaluation environments
become **sub-stages**, not research questions. Stage labels use an **environment-coded**
scheme (chosen over keeping old IDs / pure descriptive).

Do **not** delete any experiment or data — this is relabel + regroup only.

---

## New top-level RQs

- **RQ1 — Architectural split & deployment behaviour.** Which architectural split of
  ResNet-18 yields a credible two-part microservice decomposition, and how does its
  latency and boundary-crossing overhead behave across the three evaluation
  environments (controlled local → local Kubernetes → Azure AKS)?
- **RQ2 — Security hardening.** What performance and operational overhead does security
  hardening (communication-level identity+mTLS+authz, then selective confidential-VM
  execution) add to the selected AKS split deployment, and which configuration is the
  most defensible trade-off?

---

## Stage map (old → new)

### RQ1 — three evaluation environments

| New stage | Environment | Scope | Absorbs (old) |
|-----------|-------------|-------|---------------|
| **Stage L1** | Controlled local | Coarse architectural-stage split selection | RQ1.1 |
| **Stage L2** | Controlled local | Fine-grained (block-level) refinement | RQ1.2 |
| **Stage L3** | Controlled local | Activation-transfer + compute-distribution synthesis (explanatory) | RQ1.3 |
| **Stage K**  | Local Kubernetes | Service-chain scaling (1→5 services). **Base case = default placement**; **alternative = forced cross-node** | RQ1.4 (base), RQ1.4b (alternative) |
| **Stage C**  | Azure AKS | Cloud transfer of the coarse-stage chain. **Base case = single-node**; **alternative = forced multi-node** | RQ1.5 (base), RQ1.5b (alternative) |

### RQ2 — security hardening of the selected AKS path

| New stage | Scope | Absorbs (old) |
|-----------|-------|---------------|
| **Stage H1** | Communication hardening: service identity + mutual TLS + inter-service authz. **Base case = plain AKS chain.** | RQ2.1 (+ RQ2.1b if present, as an alternative config — verify in Ch.4/5) |
| **Stage H2** | VM-level confidential execution (AMD SEV-SNP) for the downstream protected service | RQ2.2 |
| **Trade-off / recommendation** | Most defensible hardening configuration across performance, operational complexity, protection scope | RQ2.3 |

---

## Base-case ↔ alternative framing (F2)

- **Stage K:** base = same-node / default scheduling; alternative = forced cross-node (old `1.4b`).
- **Stage C:** base = single-node placement; alternative = forced multi-node (old `1.5b`).
- Drop the bare `b` suffix in prose; state "base case" and "alternative" explicitly.

## Carried decisions tied to F1

- **F14 (RQ1.4b promotion):** Stage K alternative moves from appendix into the main RQ1
  evaluation, **retaining the single-host caveat** (kind workers share one kernel → measures
  CNI-bridge cost, not true cross-host; the genuine cross-host penalty is Stage C alternative on AKS).
- **F3 (RQ2.3):** retained under RQ2 as the trade-off contribution (not standalone).

---

## Propagation order (Phases 1–6)

1. **Phase 1 — §1.3 + §1.4** (introduction.tex): rewrite RQ list + Approach paragraph.
2. **Phase 2 — §4.7** (methods.tex): relabel stage-specific method subsections.
3. **Phase 3 — Chapter 5** (experiments/*.tex): section headers + per-stage intro lines.
4. **Phase 4 — Chapter 6** (analysis/*.tex): section headers + synthesis cross-refs.
5. **Phase 5 — §7.1 + Abstract**: summary narrative.
6. **Phase 6 — Sweep**: grep stray `RQ1.4`, `RQ1.5b`, etc.; fix `\label`/`\ref` + captions.

### \label convention (apply in Phase 6 / as touched)
- `stage:l1-local-coarse`, `stage:l2-local-fine`, `stage:l3-local-synthesis`
- `stage:k-k8s` (+ `stage:k-altcrossnode`), `stage:c-aks` (+ `stage:c-altmultinode`)
- `stage:h1-comms`, `stage:h2-confidential`, `stage:tradeoff`
- Keep old `\label`s aliased where a clean rename is risky; resolve in Phase 6 sweep.
