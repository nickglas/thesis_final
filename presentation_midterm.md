# Microservice-Based Neural Network Inference

## Across Architectural Splits, Cloud Deployment, and Security Hardening

A Staged Empirical Evaluation of ResNet-18 on Azure Kubernetes Service

**Nick Glas** — MSc Software Engineering, University of Amsterdam — Midterm Presentation

Academic supervisor: Dr. Ana Maria Oprescu (CCI, UvA) · Second reviewer: Dr. Thomas L. van Binsbergen (CCI, UvA) · Daily supervisor: Dr. Damian Frölich (CCI, UvA) · External supervisor: Dennis Bijlsma (SIG)

---

# Context & Problem

- Neural-network inference is increasingly embedded in cloud-native systems; most production deployments still run it as a **monolithic** component
- A **microservice** decomposition offers modularity, independent deployment, and clearer security boundaries — but every boundary forces activations to cross a service interface (serialisation, transport, scheduling)
- Prior split-inference work (Neurosurgeon, DNNSplit, DeeperThings) treats split-point selection as a computation–communication trade-off, not a depth choice
- The deployment environment (Kubernetes, managed cloud) and security mesh add their own scheduling, networking, and virtualisation effects
- mTLS terminates at the pod boundary — activations remain exposed; an untrusted partition can reconstruct the input, motivating confidential execution

**Central problem:** *where to split, where to deploy, and how to harden — together, not in isolation*

---

# Research Questions

**RQ1 — Architecture & Deployment**

- **RQ1.1** Which coarse two-part ResNet-18 boundaries are suitable under controlled local execution?
- **RQ1.2** Does finer-grained refinement within the carried-forward region change the picture?
- **RQ1.3** How do activation-transfer size and compute distribution explain the observed behaviour?
- **RQ1.4** How does chain depth affect end-to-end cost under local Kubernetes?
- **RQ1.5 / 1.5b** Does the pattern transfer to managed AKS, and what is the inter-node penalty?

**RQ2 — Security Hardening**

- **RQ2.1** Cost of service identity + managed-Istio mTLS + AuthZ on the selected AKS path?
- **RQ2.2** Incremental cost of AMD SEV-SNP confidential VM execution on top of mTLS?
- **RQ2.3** Which configuration is the most defensible trade-off between performance, operational complexity, and protection scope?

---

# Approach & Progress

**Staged experimental pipeline** — fix the model (ResNet-18, FP32, CPU, batch one), the timing protocol, and the functional-parity contract; change only **one system layer at a time** so cross-stage deltas are interpretable

| Stage | Substrate | RQs |
|---|---|---|
| 1 | Local CPU, loopback gRPC | RQ1.1–1.3 |
| 2 | Local Kubernetes (`kind`) | RQ1.4 |
| 3 | Managed AKS (+ multi-node) | RQ1.5, 1.5b |
| 4 | mTLS hardening (+ multi-node) | RQ2.1, 2.1b |
| 5 | SEV-SNP confidential VM | RQ2.2 |
| 6 | Delta-space synthesis | RQ2.3 |

**Progress:** all RQ1 and RQ2 measurements complete. Frozen evidence set — ACR-digest-pinned, paired, parity-validated (`max_abs_diff = 0.0`) across every condition. All thesis chapters drafted; currently in writing/revision phase.

---

# RQ1.1–1.3 — Split Selection (Local CPU)

**RQ1.1 — Coarse sweep, ResNet-18 on CPU FP32, gRPC over localhost:**

| Condition | Mean (ms) | Overhead | Activation | Note |
|---|---|---|---|---|
| Monolithic | 77.24 | — | — | Baseline |
| Split after `layer1` | 80.88 | **+4.7%** | 784 KiB | Activation > raw input (expansion) |
| Split after `layer2` | 80.12 | +3.7% | 392 KiB | Reference candidate |
| Split after `layer3` ✓ | 79.08 | **+2.4%** | 196 KiB | Carry-forward main |
| Split after `layer4` | 79.58 | +3.0% | 98 KiB | Compute-degenerate (0.62% downstream) |

- All splits slower than monolithic — **diagnostic**, not optimisation
- Earliest penalised by **activation expansion**, latest by **compute degeneracy**

**RQ1.2 — Block-level refinement:** three refined splits cluster in a **0.235 ms band** (flat valley, not a peak). Controlled contrast at equal 196 KiB transfer — `split_after_layer3_block0` vs. `split_after_layer3` differ by **7.81 ms** boundary-crossing — attributable to per-block compute placement, not transport.

**RQ1.3 — Two-dimensional account:** activation transfer dominates at the coarse level; compute placement is **independently observable** at the refined level. The mid-to-late band is the only region where both are tolerable.

---

# RQ1.4–1.5b — Deployment Transfer (Local k8s → AKS)

| Chain depth | Local `kind` | AKS | Local overhead | AKS overhead |
|---|---|---|---|---|
| `monolithic_1svc` | 81.07 ms | 70.80 ms | — | — |
| `chain_2svc` | 83.39 ms | 73.44 ms | +2.9% | +3.7% |
| `chain_3svc` | 87.73 ms | 75.41 ms | +8.2% | +6.5% |
| `chain_4svc` | 90.57 ms | 78.29 ms | +11.7% | +10.6% |
| `chain_5svc` | 92.54 ms | 80.52 ms | **+14.1%** | **+13.7%** |

- **Architectural ordering preserved** across three substrates (loopback → local k8s → AKS), within a **1.7 pp band** at any condition
- **Last hop is smaller** (+1.96 ms local, +2.23 ms AKS) — it moves only the 98 KiB `layer4` output
- Total compute approximately flat across chained conditions — **added cost is platform-side** (gRPC, kube-proxy, pod network). Non-compute overhead grows 6.2 → 13.6 ms
- **RQ1.5b — multi-node penalty envelope:** +2.13 to +4.09 ms across chained conditions, +2.31 ms on monolithic. Ordering still preserved.

---

# RQ2.1 — mTLS, Service Identity, AuthZ on AKS

**Paired AKS benchmark, `chain_2svc`:**

- Mean: 75.56 → 79.05 ms — **+3.49 ms / +4.62%**
- p95: **+3.62 ms / +4.53%**; every per-pass mTLS delta strictly positive (2.22–5.23 ms)

**Where the cost lives — ablation:**

- Plain → mesh-default sidecar: **+2.57 ms** of the +2.84 ms full delta
- Strict mTLS and AuthorizationPolicy each within pass-level noise
- **Most overhead is entry into the sidecar data path**, not crypto or policy in isolation

**Depth sensitivity at `chain_5svc`:** +8.84 ms / **+10.74%** — roughly 2.5× the `chain_2svc` cost

**Operational footprint:** +5 to +14 Kubernetes objects, 34.7–87.6 mCPU sidecar, 82–224 MiB memory, 6.3–6.8 s schedule-to-ready delta

**What mTLS protects (and doesn't):** hardens the inter-service network path via service-account identity and encryption. **Still trusted:** managed-Istio control plane, local CA, and the sidecar→application loopback inside each pod after TLS termination.

---

# RQ2.2 + RQ2.3 — SEV-SNP & Trade-off Synthesis

**RQ2.2 — Paired benchmark, mTLS contract fixed, `service2` on AMD SEV-SNP:**

| Metric | Standard | Confidential | Delta |
|---|---|---|---|
| Mean | 58.49 ms | 60.35 ms | **+1.85 ms / +3.17%** |
| Median | 58.29 ms | 59.76 ms | +1.47 ms / +2.52% |
| p95 | 60.26 ms | 63.86 ms | **+3.60 ms / +5.98%** |

- **Tail amplified ~1.9× vs. mean** — TEE cost is tail-concentrated
- SEV-SNP removes the cloud host/hypervisor from the TCB of the protected service
- **Honest scope:** defends against the host platform, *not* the malicious-remote-service threat model from the activation-inversion literature

**RQ2.3 — The three layers are composable, not substitutable.** For the selected `chain_2svc`:

1. **mTLS + identity + AuthZ** — most defensible default (symmetric cost across the distribution)
2. **Selective SEV-SNP** on the downstream service — next step *only* when threat model includes the host platform
3. **Plain AKS** — fastest, weakest protection

Recommendation is specific to `chain_2svc`; cost grows with chain depth. No adversarial security evaluation performed.

---

# Headline Findings & What's Left

**Headline findings**

1. Coarse split boundaries are not interchangeable — activation expansion vs. compute degeneracy
2. Refinement reveals a **flat band**; compute placement is independently observable at equal transfer
3. Architectural ordering transfers across **three substrates** within 1.7 pp
4. Most chain overhead is **platform-side**, not compute; marginal cost depends on the tensor moved
5. mTLS overhead is bounded but grows with protected chain depth — mostly sidecar entry cost
6. Selective SEV-SNP is bounded with tail amplified ~1.9× vs. mean
7. Three hardening layers are composable, not substitutable

**Remaining work** — analysis-chapter prose polish, cross-RQ synthesis tightening, consolidated limitations & threats to validity, front-matter polish, references pass

**Future work (out of scope, pointers only)** — larger / transformer models, GPU + mixed precision, activation compression at the boundary, concurrent load, full two-service TEE, adversarial CVM security evaluation

---

# Where I'd Like Peer Feedback

- **Thesis structure** — does the RQ1-architecture / RQ1-deployment / RQ2-security split read cleanly, or should I collapse RQ1 into one strand?
- **Evaluation framing** — is "delta-on-paired-baseline + ranking-preserving, not millisecond-equivalent" defensible, or should I push harder on cross-environment absolutes?
- **Scope honesty** — am I being too cautious about what the security claims do and don't cover for a measurement thesis?
- **Generalisability** — how strongly should I emphasise that the numbers are ResNet-18-specific, CPU-only, FP32, batch-one?

---

**Thank you — questions & discussion**

Nick Glas — nickglas53@gmail.com
University of Amsterdam — Complex Cyber Infrastructure
In collaboration with Software Improvement Group (SIG)
