# Claim Check Against Results

Audit date: 2026-06-15

Scope: Abstract, Introduction, Chapter 5 experiment text, Chapter 6 analysis text, and Chapter 7 conclusion, checked against the frozen result artefacts under `frozen_results/frozen_new/`. No experiments were re-run.

## Overall Verdict

The main numeric claims in the thesis match the frozen result artefacts. I did not find a hard contradiction such as a reported percentage, mean, p95 delta, or condition ordering that is plainly wrong.

The remaining risks are mostly wording risks: a few claims are phrased in a way that could be read as broader than the data supports. The thesis is already unusually careful about limitations, delta-space comparisons, and threat-model boundaries; the main improvement is to make the high-level abstract/conclusion wording as careful as the detailed analysis sections.

## Evidence Snapshot

| Stage | Result check | Source artefact |
|---|---|---|
| Stage L1 | Monolithic is fastest at 77.238 ms. All split conditions add latency. `split_after_layer3` is the raw-fastest non-degenerate split at 79.084 ms; `split_after_layer2` is the reference at 80.118 ms. `split_after_layer1` carries the largest activation, 784 KiB, and the highest boundary-crossing interval, 53.81 ms. `split_after_layer4` carries only 98 KiB but is compute-degenerate. | `rq1_1_20260515_111428/report.md`, `condition_summaries.csv`, `carry_forward.json` |
| Stage L2 | `split_after_layer3_block0`, `split_after_layer3`, and `split_after_layer2` are close in mean latency: 80.157, 80.392, and 80.348 ms. The selected main/reference pair is rule-based rather than a large latency separation. `split_after_layer3_block0` and `split_after_layer3` both transfer 196 KiB; their boundary-crossing gap is about 7.81 ms and aligns with the service-B compute gap. | `rq1_2_20260515_112636/report.md`, `condition_summaries.csv`, `cross_condition.csv` |
| Stage K | Local Kubernetes means increase monotonically: 81.066, 83.387, 87.728, 90.572, 92.535 ms. OLS over the five means gives slope about 3.01 ms/service and R2 about 0.984. Total compute is approximately flat across chained conditions, 77.17-78.90 ms, while non-compute/platform cost grows. | `rq1_4_fully_controlled_20260515_141036/merged_results/report.md`, `condition_summaries.csv` |
| Stage C | AKS means preserve the same ordering: 70.802, 73.437, 75.410, 78.294, 80.519 ms. OLS over the five means gives slope about 2.43 ms/service and R2 about 0.998. Relative overheads track Stage K within 1.7 percentage points. | `rq1_5_fully_controlled_20260515_145954/merged_results/report.md`, `condition_summaries.csv` |
| Stage C multi-node | Multi-node AKS preserves ordering. The single-node to multi-node deltas are +2.305 ms for monolithic and +3.033, +2.131, +3.808, +4.086 ms for chained conditions. The envelope claim is supported; a monotone per-hop claim would not be. | `rq1_5b_multinode_20260515_152628/merged_results/report.md`, `condition_summaries.csv` |
| Stage H1 | Chain-2 mTLS/AuthZ overhead is +3.488 ms / +4.62% mean and +3.623 ms p95. Chain-5 overhead is +8.837 ms / +10.74% mean and +8.983 ms p95. All paired pass deltas are positive. | `rq2_1_paired_20260515_160012/merged/aggregated_results.md`, `rq2_1_paired_20260517_114303/merged/aggregated_results.md` |
| Stage H1 ablation | The ablation supports the "mostly sidecar data path" interpretation, but only internally: C1-C0 is +2.569 ms and C3-C0 is +2.840 ms. It should not be spliced into the frozen two-condition paired result. The thesis mostly respects this. | `rq2_1_ablation_20260516_112348/merged/rq2_1_ablation_summary.md` |
| Stage H1 multi-node | Chain-2 mTLS/AuthZ multi-node sensitivity is +2.712 ms / +3.90% mean, same direction and order of magnitude as the single-node primary result. | `rq2_1b_multinode_20260516_174806/merged/aggregated_results.md` |
| Stage H2 | Selective SEV-SNP on service2 gives standard mean 58.492 ms and confidential mean 60.346 ms: +1.854 ms / +3.17%. p95 increases by +3.601 ms / +5.98%. The standard baseline is not comparable in absolute ms to the Stage H1 cluster. | `rq2_2_confidential_20260516_135726/conditions/*/benchmark/raw_iterations.csv`, `rq22_rolling_summary.json` |

## Supported Claims

These claims are safe as currently framed, or nearly safe:

1. Monolithic execution remains the fastest raw-latency baseline within each directly comparable stage.
2. Early splits are costly because of large activation transfers; very late splits can be compute-degenerate.
3. The L2 fine-grained region is effectively flat for latency at the observed scale, so the carry-forward decision is a rule-based engineering choice rather than a dramatic speed win.
4. Local Kubernetes and AKS preserve the same condition ordering and similar relative-overhead shape, while absolute latencies are environment-specific.
5. Stage C multi-node gives a bounded AKS inter-node penalty envelope, not a single per-hop law.
6. mTLS/AuthZ adds measurable overhead and operational complexity; the primary chain-2 overhead is correctly reported.
7. mTLS overhead is depth-sensitive, but only at the two measured depths.
8. Selective SEV-SNP adds a small mean overhead and a larger tail overhead, and the thesis correctly warns that this is an incremental within-cluster delta.
9. The security discussion correctly avoids claiming end-to-end security or adversarial robustness.

## Claims To Tighten

### 1. "Each added boundary" is too strong for the chain family

Locations:
- `thesis/frontmatter/abstract.tex:5`
- `thesis/chapters/conclusion.tex:51`

Current idea:
The marginal cost of each added boundary is modulated by activation-transfer size.

Why risky:
The adjacent chain conditions are not all nested one-boundary additions. For example, `chain_2svc` uses the `layer2` split, while `chain_3svc` uses `layer1,layer3`; that comparison changes the boundary set rather than simply adding one boundary. The clean "added boundary" interpretation is strongest for `chain_3svc -> chain_4svc` and `chain_4svc -> chain_5svc`.

Safer wording:
"Across the predefined chain family, marginal increments are not constant; the clearest nested increments show that late boundaries moving smaller activations add less cost."

### 2. "Approximately linear" should always say "over the measured one-to-five range"

Locations:
- `thesis/frontmatter/abstract.tex:5`
- `thesis/chapters/conclusion.tex:48`

Current idea:
Latency increases approximately linearly with service count and is bounded rather than super-linear.

Why risky:
The claim is supported by five measured points, not by an extrapolatable scaling model. The detailed analysis says this clearly; the abstract should carry the same boundary.

Safer wording:
"Over the measured one-to-five-service family, latency is well described by an approximately linear trend rather than a super-linear curve."

### 3. "Plain AKS is the fastest evaluated configuration" conflicts with delta-space discipline

Locations:
- `thesis/chapters/analysis/security.tex:517`
- Related wording: `thesis/chapters/experiments/security.tex:561`

Current idea:
Plain AKS remains the fastest evaluated configuration / best option if performance is the only criterion.

Why risky:
The thesis correctly explains that Stage H1 and Stage H2 have different paired baselines. In absolute ms, the Stage H2 standard mTLS baseline is 58.492 ms, lower than the Stage C plain AKS chain-2 mean of 73.437 ms, because region/SKU/session differ. So "fastest evaluated configuration" can be misread as an absolute cross-row statement, which the thesis explicitly says not to do.

Safer wording:
"Plain AKS has zero added hardening overhead relative to its own baseline and is the lowest-cost option in delta space, but it provides the weakest protection set."

### 4. "Removes the inter-service plaintext path" needs the sidecar boundary

Location:
- `thesis/chapters/analysis/security.tex:509`

Current idea:
mTLS/AuthZ removes the inter-service plaintext path.

Why risky:
The thesis elsewhere correctly says sidecar mTLS protects the inter-proxy path, while sidecar-to-application loopback inside the pod remains plaintext. "Inter-service plaintext path" is close, but a strict reader may ask whether the endpoint side is included.

Safer wording:
"It removes plaintext from the proxy-mediated inter-service network path, while leaving sidecar-to-application loopback inside each pod outside the mTLS boundary."

### 5. Separate host-platform exposure from malicious-remote-service activation privacy

Location:
- `thesis/chapters/experiments/security.tex:575`

Current idea:
If the threat model includes host-level exposure, mTLS alone is insufficient, and activation-inversion work shows that an untrusted remote service can recover inputs from features.

Why risky:
Both statements are true, but they are different threat models. SEV-SNP addresses the host/hypervisor adversary, not a malicious service that legitimately receives activations. The analysis chapter handles this well; the experiment synthesis paragraph should avoid even momentary conflation.

Safer wording:
"If the threat model includes host-level exposure of the downstream segment, mTLS alone is insufficient because it protects transport rather than runtime memory. Separately, activation-inversion work motivates why intermediate activations are sensitive, although that work assumes a malicious remote-service adversary rather than the host-platform adversary addressed by SEV-SNP."

### 6. "Same decomposition family" in the abstract is ambiguous

Location:
- `thesis/frontmatter/abstract.tex:3`

Current idea:
After coarse screening and fine refinement, "the same decomposition family" is evaluated in Kubernetes and AKS.

Why risky:
Stage K/C evaluate the predefined coarse-stage chain family, not the exact fine-grained `split_after_layer3_block0` two-part split. The main body says "same coarse-stage chain family" more clearly.

Safer wording:
"The resulting coarse-stage service-chain family is then evaluated in local Kubernetes and Azure Kubernetes Service."

### 7. "Best trade-off" should say "among evaluated configurations"

Locations:
- `thesis/chapters/introduction.tex:20`
- `thesis/chapters/conclusion.tex:150`

Current idea:
Which configuration provides the best trade-off / best supported default?

Why risky:
The actual evaluated set is narrow: plain AKS, mTLS/AuthZ, mTLS/AuthZ plus selective service2-only SEV-SNP; one model, one topology emphasis, one mesh revision, one CVM substrate. The detailed thesis states this, but the RQ wording can be made more robust.

Safer wording:
"Which evaluated configuration provides the best supported trade-off..."

## Suggested Edit Priority

1. High: tighten the delta-space wording around "Plain AKS fastest" (`analysis/security.tex:517`, `experiments/security.tex:561`).
2. High: replace "each added boundary" with "predefined chain-family increments" or the narrower nested-boundary phrasing.
3. Medium: add "over the measured one-to-five-service family" to abstract/conclusion linearity claims.
4. Medium: sharpen the mTLS plaintext-boundary sentence.
5. Medium: separate SEV-SNP host-platform protection from malicious-service activation privacy in the trade-off synthesis prose.
6. Low: replace "same decomposition family" in the abstract with "coarse-stage service-chain family."
7. Low: add "evaluated" before "best trade-off/default" in the RQ/conclusion wording.

## Bottom Line

The thesis does not need new experiments for claim support. It needs a small wording pass so the abstract, RQ wording, and conclusion do not overstate what the detailed analysis already handles correctly.
