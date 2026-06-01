# Feedback Analysis & Revision Roadmap

**Thesis:** *Microservice-Based Neural Network Inference Across Architectural Splits, Cloud Deployment, and Security Hardening* (Nick Glas, MSc Software Engineering, UvA, May 2026)
**Source of feedback:** Recording_5.m4a transcript — a supervision/feedback session. **Speaker 1 = supervisor** (Dr. Oprescu, the examiner/chair); **Speaker 2 = you (the author).**

A reading note before the detail: this was a *positive* session. The supervisor's repeated message is that the research content is sound and that no further core experiments are required — the work needed is **structural and editorial**, driven by one big change (refactoring the research questions). Most items below are about *presentation and framing*, not validity. Two items (RQ refactor, AI disclosure) are the load-bearing ones.

---

## Progress Tracker

**Status legend:** ☐ = not started · ◐ = in progress · ✅ = done. Replace the box as you go. In your Git repo the `- [ ]` boxes render as clickable checkboxes.

**Active now — F1 research-question refactor (full plan in §5A):**

- [x] **Phase 0** — Lock the new RQ structure *(Opus high)* — **DONE 2026-06-01**; 2 RQs, environment-coded stages. See `_rq_refactor_phase0_lock.md`.
- [x] **Phase 1** — §1.3 + §1.4 — **DONE 2026-06-01**; rewrote RQ list to 2 RQs + stage paragraphs, updated Approach + Outline (`introduction.tex`).
- [x] **Phase 2** — §4.7 — **DONE 2026-06-01**; relabeled all of `methods.tex` (§4.1 overview + §4.7 stage subsections + inline refs) to L1/L2/L3/K/C/H1/H2 + trade-off. Compiles clean (148 pp, no undefined refs). `\label` keys kept for Phase 6.
- [x] **Phase 3** — Chapter 5 — **DONE 2026-06-01**; relabeled all 6 experiment files (coarse/fine/timing/kubernetes/azure/security) to the stage scheme; "Research Question" subsections → "Stage Objective"; frozen-artifact paths + `\label` keys preserved. Compiles clean (148 pp, no undefined refs).
- [x] **Phase 4** — Chapter 6 — **DONE 2026-06-01**; relabeled all analysis files (split/deployment/security per-stage + synthesis + validation + threats + evaluation). Per-stage "Answer to RQ1.x" → "Stage~Lx outcome" etc.; RQ2.3→"Trade-off Synthesis". Compiles clean (150 pp, no undefined refs).
- [x] **Phase 5** — §7.1 + Abstract — **DONE 2026-06-01**; conclusion §7.1/Contributions/Limitations relabeled to stage scheme (RQ1/RQ2 strands kept top-level; RQ2.3→trade-off synthesis). Abstract already narrative (no RQ IDs). Compiles clean (150 pp).
- [x] **Phase 6** — Sweep cross-refs / `\label` / captions — **DONE 2026-06-01**; relabeled `related_work.tex`, `background.tex`, `appendix.tex`, and all `figures/tikz/background/*` figure node-text + comments. Whole repo now has **zero** stray sub-IDs except one intentional comment in `appendix.tex:7` referencing the external evidence-manifest row `"RQ1.4b"` (preserved like a frozen-artifact key). `\label`/`\cref` keys left intact. Final compile: 152 pp, no undefined refs/citations. **F1 COMPLETE.**

**✅ Full F1 audit re-verified 2026-06-01** (source-level, not just trusted from prior notes):
- Repo-wide grep `RQ\d\.\d`: **0** stray sub-IDs (only intentional `appendix.tex:7` manifest-row reference remains).
- `Answer to RQ` / `sub-research question` / `\subsection{Research Question}`: **0** remaining (all reframed to "Stage … outcome." / "Stage Objective").
- Replacement-corruption check (`Stage~Kb`/`Stage~Cb`/…): **0**.
- All §4.7 method subsections, all Ch.5 section headers, all Ch.6 per-stage subsections, the appendix section, and 6 TikZ figures carry the new stage labels (verified by header grep).
- Intro carries the 2-RQ `description` list (`\label{rq:rq1/rq2}`) + "Stages of RQ1/RQ2" paragraphs; all 9 analysis stages carry "Stage … outcome." headers.
- No stray `RQ3+` or residual `b`-suffix tokens.
- Final build: **main.pdf 152 pp**, log has **no undefined/multiply-defined references or citations** (only pre-existing benign small-caps font-shape warnings).

Per-item progress for everything else is tracked in the **Done** column of §6.

---

## 1. Extracted Feedback (master list)

Each item has an ID used throughout. "Explicit" = stated directly; "Inferred" = implied by the conversation or by a praise/concern that carries an action.

| ID | Feedback (summary) | Type | Importance |
|----|--------------------|------|------------|
| **F1** | Refactor/"fold" the 9+ research questions (RQ1.1–RQ1.5b, RQ2.1–RQ2.3) into ~2–3 conceptual research questions; separate the *conceptual changes to the system/environment* from the *evaluation environments* (local / Kubernetes / cloud), which are not themselves RQs. | Explicit | **Critical** |
| **F2** | The `b`-suffixed variants (RQ1.5b, RQ2.1b; also RQ1.4b) should be framed as **alternatives to a clearly stated base case**, not as standalone questions. The non-`b` (single-node) is the baseline; the `b` (multi-node) is the alternative. | Explicit | Important |
| **F3** | Keep RQ2.3 (the security trade-off / recommendation) — it is a valuable *conceptual contribution* and a "discussion-type" question. (Supervisor initially said make it standalone, then agreed it can sit under RQ2 because it also covers performance/operational cost.) | Explicit | Important |
| **F4** | Add an **AI-usage disclosure** (a section in the Discussion/Conclusion or a reflection), explaining to what extent AI was used; optionally include a **sample prompt in an annex**. | Explicit | **Critical** |
| **F5** | **Verify every reference is real** and not AI-fabricated/"translated". | Explicit | **Critical** |
| **F6** | Add a **reflection in the Discussion on generalisability** of the method/framework to other neural networks and transformer/secure-transformer inference — *reflect on impact*, not run new experiments. | Explicit | Important |
| **F7** | Add a **reflection on broader impact/significance**: per-layer policy control, layers owned by *different organizations* that choose to interoperate ("digital embassies"), and what this means for the inter-layer API/parameterization you propose. | Explicit | Important |
| **F8** | **Figure text is too small.** Enlarge fonts inside diagrams (rule of thumb: in-figure text ≈ body-text size); make boxes bigger to use the whitespace. | Explicit | Important |
| **F9** | **One figure fills an entire page.** Shrink images, trim content, or place figures side-by-side. (Raised while reviewing the Background chapter.) | Explicit | Minor |
| **F10** | Decide placement of background material: information can be *referenced*, but if it is closely tied to a specific chapter (not conceptual), move it into that chapter. | Explicit | Minor |
| **F11** | Add **error bars / a ±1 SD or 95% CI band** to the latency plots where measurements vary (not deterministic). | Explicit | Important |
| **F12** | **Characterise the shape** of the latency-vs-service-count curve (linear / power-law / logarithmic / exponential) rather than just connecting dots. | Explicit | Important |
| **F13** | **Be able to explain your own statistics** (Mann–Whitney U, normality testing). You could not explain them on the spot; ensure you can justify why each test is used. | Explicit | Important |
| **F14** | Move **RQ1.4b out of the appendix** into the main evaluation — it is one of the deployment environments, and this becomes natural once the RQs are refactored (F1). | Explicit | Important |
| **F15** | Run-settings/config tables: **keep the detail in the appendix but reference the key facts in the body** so the body is not cluttered. | Explicit | Minor |
| **F16** | Add a **table comparing local vs. cloud infrastructure config** (cores, memory) to pre-empt the "you gave the cloud a bigger instance" criticism and show the comparison is fair. | Explicit | Important |
| **F17** | Consider whether the **Validation section should precede the per-RQ observations** in the Analysis chapter (currently 6.4 Validation comes after 6.1–6.3). Left unresolved — depends on the template and on whether validation reuses the observations. | Inferred / open | Minor |
| **F18** | **Keep sourcing tables to the GitHub/frozen artifacts** — supervisor explicitly praised this; continue the practice. | Explicit (praise → keep) | Minor |
| **F19** | **Keep embedding each RQ into the related-work chapter** and consider *highlighting/emphasising* that linkage at the end of the chapter; add the missing references there. | Explicit (praise → keep + small action) | Minor |
| **F20** | Consider retitling the related-work chapter / its positioning section as **"Research Gap Analysis and Scope."** | Explicit (suggestion) | Minor |
| **F21** | *Optional, scope-dependent:* try the chain on **FABRIC** (multi-region, multi-cluster) and/or a **confidential-VM demo** for Supercomputing (Chicago, Nov). Affects only Results/Discussion and the **defense date**, not validity. | Explicit (optional) | Minor (scope) |
| **F22** | Address the author's own **doubt about academic impact** — supervisor strongly pushed back. Not a text edit per se, but it motivates F6/F7 and the framing of Contributions. | Inferred | Important |

---

## 2. Feedback Linked to Thesis Locations

> Format: **Feedback → location(s) → relevant thesis text → reasoning → recommended revision.** Transcript citations are by timestamp; thesis citations by section/page.

### F1 — Refactor the research questions *(Critical, cross-cutting — see also §3.1)*
**Transcript:** 00:04:05 *"those three are basically types of evaluation of the cuts. So they are not per se research questions, but they are stages of formulating an answer to a bigger research question, which is one and two."* / 00:04:40 *"I would reformulate from one to five, fold them so that it's clear what are the conceptual things … the inflicted changes, the environment … And then you have the evaluation flavors."* / 00:05:11 *"fold it up to like 3 … research questions?" — "Yes, that would make sense."*

**Relevant thesis location(s):** §1.3 Research Questions (p. 2–3); and everywhere the RQ scaffold is reused — §4.7 Stage-Specific Methods (p. 24–31), all of Chapter 5 (p. 35–75), all of Chapter 6 (p. 77–116), Abstract (p. vii), §7.1 (p. 117).

**Relevant text (§1.3):** the list "RQ1.1 … RQ1.2 … RQ1.3 … RQ1.4 … RQ1.5 … RQ1.5b … RQ2.1 … RQ2.2 … RQ2.3", followed by the explanatory paragraph: *"RQ1.1 and RQ1.2 form the local split-selection stages. RQ1.3 is an explanatory synthesis … RQ1.4 and RQ1.5 then evaluate the same coarse-stage chain family in local Kubernetes and AKS, while RQ1.5b acts as a sensitivity stage…"*

**Reasoning:** The supervisor's point is that RQ1.1–RQ1.5b conflate two different things: (a) *what you change conceptually* (split granularity, security hardening) and (b) *where you evaluate it* (controlled local → local Kubernetes → Azure). Items (b) are evaluation environments/"flavors", not research questions. The thesis's own explanatory paragraph already concedes this ("RQ1.4 and RQ1.5 then evaluate the same … chain family"), which is exactly the structure the supervisor wants surfaced.

**Recommended revision:** Restructure §1.3 into **two (possibly three) top-level RQs**:
- **RQ1 — Architectural split & distribution:** which split, and its impact on performance, evaluated across the three environments (controlled local, local Kubernetes, Azure). Absorbs RQ1.1–RQ1.5/1.5b.
- **RQ2 — Security hardening of the splits & its impact on performance/operations.** Absorbs RQ2.1, RQ2.2.
- **RQ3 (or RQ2.3 retained under RQ2) — the security-hardening trade-off / recommendation** (discussion-type). See F3.
Then make the current RQ1.1–RQ1.5b into **sub-stages / evaluation environments** under RQ1 rather than numbered research questions. Do not delete the experiments — only re-label and re-group them. **This is the keystone change**; F14, F3, F2 all flow from it (do F1 first).

---

### F2 — Frame the `b`-variants as base-case vs. alternative *(Important)*
**Transcript:** 00:00:40 *"I'm trying to make up my mind whether I like it or not, that you're so specific about … including B. But then it feels weird if you don't have an A."* / 00:02:16 *"absolutely you should keep it … explain it as the baseline."* / 00:02:25 *"the non-B … is what I use as the base case." — "And the B1 is an alternative." — "Yes, an alternative."*

**Relevant location(s):** §1.3 (RQ1.5b, p. 3); §4.7.5 RQ1.4b (p. 26), §4.7.7 RQ1.5b (p. 28), §4.7.11 RQ2.1b (p. 30); §5.5, §5.7, §5.10; §6.2.2, §6.2.4.

**Relevant text (§1.3, RQ1.5b):** *"When every chain hop is forced across a node boundary, how much additional cost is introduced relative to the same-node RQ1.5 baseline?"*

**Reasoning:** The naming (`b` without a labelled `a`) reads as arbitrary. The content is fine — single-node is the baseline, multi-node is the alternative — but the framing must say so explicitly. The thesis already treats single-node as primary ("the same-node RQ1.5 baseline"), so this is a labelling/exposition fix.

**Recommended revision:** Under the refactored RQ1, present single-node placement as the **base case** and multi-node as a named **alternative/sensitivity** condition, in the RQ text, in §4.7, and in the Ch. 6 syntheses. Avoid the bare `b` suffix unless you also define the `a`/base case symmetrically.

---

### F3 — Keep RQ2.3 (trade-off) as a conceptual contribution *(Important; internally contradictory in transcript — see §6)*
**Transcript:** 00:06:31 *"what it says is a trade-off, like giving a recommendation." — "That's very good. That's a conceptual contribution."* / 00:06:56 *"No, I would actually … leave it aside … this is going to be a discussion kind of a question. So I would just make it by itself."* / **then reversed:** 00:08:08 *"maybe you're right … it makes sense to keep it in the line of two."*

**Relevant location(s):** §1.3 (RQ2.3, p. 3); §4.7.13 (p. 31); §5.12 (p. 73); §6.3.3 (p. 106); also surfaced in §6.5 and §7.2 (Contributions/Practical).

**Relevant text (§1.3, RQ2.3):** *"Which security-hardening configuration provides the most appropriate trade-off between performance cost, operational complexity, and protection scope…"*

**Reasoning:** The supervisor values this as a contribution but wavered on placement (standalone discussion question vs. under RQ2). They landed on keeping it within the RQ2 line because it spans performance/operational cost, not only security.

**Recommended revision:** Retain RQ2.3 as the trade-off/recommendation question under RQ2 (or as RQ3 if you adopt a 3-RQ structure). Flag this as a point to confirm with the supervisor (the advice reversed mid-session — see §4 and §6).

---

### F4 — Add an AI-usage disclosure *(Critical)*
**Transcript:** 00:11:46 *"If you used any AI, it's good to mention how you used it … describe it in the discussion or have a section there."* / 00:12:03 *"it has not generated the entire [thesis]"* / 00:12:44 *"you could also give an annex sample prompt that you used … creates a lot of trust between the reader and the thesis."*

**Relevant location(s):** **Currently missing.** Closest existing section is §4.10 Ethical Considerations (p. 33), which states *"This thesis does not involve human participants, personal data, or biological material"* — i.e. it does **not** mention AI use. Natural homes: a new subsection in Chapter 6/7 (Discussion/Conclusion) and/or an extension of §4.10; sample prompt in Appendix A.

**Reasoning:** A full-text search of the thesis found **no** disclosure of AI/LLM use anywhere. The supervisor (the examiner) explicitly expects one. This is a compliance/integrity item, hence Critical.

**Recommended revision:** Add a short, honest disclosure stating *to what extent* AI was used (e.g., drafting, editing, code, figure generation, literature triage) and what it was **not** used for. Add a representative prompt to Appendix A. Confirm with the program (Martin) whether model name/date is required — see §4.

---

### F5 — Verify all references are genuine *(Critical)*
**Transcript:** 00:12:10 *"Make sure that all the references are actually references." — "They are not translated."* (in the context of AI use)

**Relevant location(s):** References (p. 125 ff.); all in-text citations.

**Reasoning:** This pairs with F4: if any AI tooling touched the bibliography, fabricated or mistranslated references are a known failure mode. The reference list looks real on inspection (DOIs present for [1], [2], [4], [5], [6], [7] etc.), but the supervisor is asking for an explicit verification pass.

**Recommended revision:** Check every entry against its DOI/source; confirm authors, venue, year, and that each in-text `[n]` resolves to a real, on-topic source. Low intellectual effort but should be done before submission.

---

### F6 — Reflect on generalisability to other models / transformers *(Important)*
**Transcript:** 00:15:53 *"you should have in the discussion a reflection on the extent to which the methodology you developed … is applicable to other neural networks or even transformers."* / 00:16:38 *"there's also secure transformer inference … I would not suggest that you also do this … but try to reflect in your discussion on what kind of impact you think this has."* / 00:19:31 *"to what extent would your way of identifying the splits, doing the measurements, would have to change if instead of a ResNet-18, we would have a different neural network or a transformer model?"*

**Relevant location(s):** §6.6 External validity (p. 115); §7.3 Limitations (p. 121); §7.4 Future Work (p. 122).

**Relevant existing text (§7.3):** *"the headline numbers may not transfer quantitatively to GPU execution, mixed precision, larger or transformer-based models…"* and (§7.4) *"The same staged method could be applied to larger and more diverse models, including transformer inference workloads…"*

**Reasoning:** The thesis already mentions transformers — but only as a *limitation* and a *future-work line item*. The supervisor is asking for something stronger and different: a **reflective discussion of what would have to change in your method** (split identification, activation-size reasoning, compute-distribution analysis) for a different architecture family, framed as impact rather than as a caveat.

**Recommended revision:** Add a dedicated reflection (Discussion) that walks through how each stage of your *method* would adapt to a transformer/other CNN (e.g., split candidates become attention-block boundaries rather than residual stages; activation-transfer reasoning still applies; compute-distribution analysis generalises). Distinguish this from the existing limitation/future-work sentences (don't just repeat them).

---

### F7 — Reflect on broader impact / significance *(Important; ties to F22)*
**Transcript:** 00:18:35 *"these layers could be even owned by different organizations that can decide to allow them to exist or not."* / 00:18:56 *"taking a monolith, [splitting it into] microservices, has no impact. Is that true? … scientifically, that is not true."* / 00:20:33 *"having policy controlling every layer. What kind of level of control that opens?"* / 00:31:44 *"reflect on this impact … the potential it now opens with policy, with controlling every layer … layers actually produced by different organizations … what does it mean for the parameterization between layers, the API that you're proposing?"* / 00:34:28 *"digital embassies … combining layers from different [organizations]."*

**Relevant location(s):** §6.2.5 / §6.3.4 syntheses; §6.5 Evaluation (p. 111); §7.2 Contributions (p. 120); a Discussion subsection.

**Relevant existing text (§6.5):** *"the contribution of the system is not raw-latency optimisation; it is a bounded overhead budget for the architectural, deployment, and security properties the monolithic baseline does not provide."*

**Reasoning:** The thesis frames its contribution defensively (overhead budgets, bounded claims). The supervisor wants you to articulate the *upside*: decomposition opens per-layer policy/governance control and cross-organisational model composition — a genuinely new research direction. This directly answers your own impact-doubt (F22).

**Recommended revision:** Add a Discussion reflection on significance: (i) per-layer policy/governance enforcement enabled by service boundaries; (ii) the "digital embassies" scenario where layers are owned by different organisations; (iii) implications for the inter-layer API / activation parameterization you propose. Keep claims reflective, not over-stated.

---

### F8 — Enlarge in-figure fonts *(Important)*
**Transcript:** 00:09:21 *"You need to make the font … larger … If you make the boxes bigger, you can make the font bigger."* / 00:09:36 *"text in images should be more or less the same font size as the text outside of images."*

**Relevant location(s):** Background figures, esp. Figs 2.1–2.13 (p. 5–13) — discussed during the Background-chapter review (≈09:04–11:26). Likely also the result figures.

**Reasoning:** Several Background diagrams (drawn with the TikZ/`tikz` package — *"It's using the text package"*, 00:09:19) have small labels and large whitespace. Reviewers must be able to read figure text at body size.

**Recommended revision:** Increase font sizes in the TikZ figures so in-figure text ≈ body text; expand boxes to absorb whitespace. Prioritise the architecture/security diagrams (Figs 2.1–2.13).

---

### F9 — A figure fills a whole page; shrink/rearrange *(Minor)*
**Transcript:** 00:11:04 *"try to make it a bit smaller. The images, especially this one, just takes a whole page by itself."* / 00:11:20 *"making the images smaller so they can [sit] side by side."*

**Relevant location(s):** A Background figure. Most likely **Fig 2.5** (detailed ResNet-18 BasicBlock structure, p. 7) — the most space-consuming diagram — or one of the large security diagrams Figs 2.10–2.13 (p. 10–13). *(Deictic "this one" — confirm which; see §4.)*

**Reasoning:** A single full-page figure disrupts flow.

**Recommended revision:** Reduce the figure's footprint or place related figures side-by-side; consider trimming detail that is reproduced elsewhere.

---

### F10 — Decide background-material placement *(Minor)*
**Transcript:** 00:09:59 *"should I include them in the chapters as well. Or should I reference them?" — "No, you can reference the information. But if the information is very related to what is in the chapter and not so much conceptual, then you might just place it in that chapter."*

**Relevant location(s):** Chapter 2 Background (p. 5–13), relative to Chapters 4–5.

**Reasoning:** Conceptual material belongs in Background and can be cross-referenced; chapter-specific material is better placed in the chapter that uses it.

**Recommended revision:** Audit Chapter 2: keep conceptual content (split inference, RPC cost, protection boundaries) in Background; move any narrowly experiment-specific material into the relevant Methods/Results subsection or reference it from there.

---

### F11 — Add error bars / variability bands to latency plots *(Important)*
**Transcript:** 00:21:27 *"if there's any variation, you can have a corridor of error."* / 00:22:03 *"when there is variation and the numbers are not just … deterministic … you have … a blurred interval around it … the plus minus for the standard deviation … an error bar, but it's also nice if you just do it with a separate line."*

**Relevant location(s):** Figs 5.1, 5.3, 5.4, 5.6, 5.7 (p. 40, 55, 59, 61, 69). The underlying dispersion exists in the data — e.g. Table 5.9 reports `Std (ms)` and the text reports per-iteration 95% CIs (`ci95_lower_ms`/`ci95_upper_ms`).

**Relevant text (Table 5.2 caption):** *"descriptive within-run per-iteration 95% confidence interval on the mean … reported from the … ci95_lower_ms / ci95_upper_ms columns."*

**Reasoning:** The CI/SD data is already computed and tabulated but the bar/line figures appear to show means only. Plots of varying measurements should display the variability.

**Recommended revision:** Add ±1 SD error bars or a 95% CI band/line to the latency figures, sourced from the same frozen CSVs you already cite. Mention briefly in captions which dispersion measure is shown.

---

### F12 — Characterise the latency curve's functional shape *(Important)*
**Transcript:** 00:23:02 *"the latency as a function of the number of instances."* / 00:23:24 *"the latency is increasing with the number of[?] in what shape? Is it … a power law? … exponential? … logarithm? … seems to be more or less the first bisector … identity function … grow linearly."*

**Relevant location(s):** Fig 5.3 (RQ1.4 latency vs service count, p. 55) and Fig 5.4 (RQ1.5 normalised overhead, p. 59); analysis §6.2.1 (p. 87) and §6.2.5 (p. 99).

**Relevant text (§6.2.1 / §7.1):** *"end-to-end latency grows monotonically … and the marginal cost of an added boundary is shaped by the tensor transferred at it rather than by a constant per-hop surcharge."* The data (Table 5.9: 81.07 → 83.39 → 87.73 → 90.57 → 92.54 ms) and Abstract's *"bounded and non-linear"* claim are relevant.

**Reasoning:** The thesis describes the trend qualitatively ("monotonic", "bounded and non-linear") but does not name a functional form. The supervisor wants an explicit characterisation (and notes connecting dots without a function is a pitfall — here it *is* a function of service count, which is fine).

**Recommended revision:** State the observed shape explicitly (e.g., approximately linear in service count but with marginal cost modulated by per-hop activation size). If you claim "non-linear", support it (a brief fit or a per-hop-delta argument). Reconcile the wording between Abstract ("non-linear"), §6.2.1 ("monotonic"), and the figure.

---

### F13 — Be able to explain your own statistics *(Important)*
**Transcript:** 00:23:44 *"we tested abnormality here with the … one[?]" — "To be honest, I have no clue what this is."* / 00:24:15 *"Can you explain … what it is or what the interpretation means…?"* / 00:24:22 supervisor: *"I don't know why you tested it on…"* then explains p-values, Mann–Whitney one-sidedness, and normality/central-limit assumptions.

**Relevant location(s):** §4.5.3 Effect Size and Significance Tests (p. 24); the "Methodological note" paragraphs in §5.4.4 (p. 54) and §6.4 (p. 110); any normality/Mann–Whitney reporting (incl. appendix RQ1.4b).

**Relevant text (§4.5.3):** *"Cohen's d is computed from pooled per-iteration data and the Mann-Whitney U test is reported for completeness. These statistics are descriptive diagnostics rather than the main decision rule."*

**Reasoning:** This is a **defense-readiness** concern, not necessarily a text change: you must be able to justify, in the viva, *why* you ran a normality test and Mann–Whitney U, what they mean at N=1,000, and why you down-weight p-values in favour of Cohen's d and cross-round CV. The thesis text actually states a defensible rationale; the gap is your ability to articulate it.

**Recommended revision:** (a) Confirm the §4.5.3 rationale is complete and that every test reported is justified there; (b) prepare a viva-ready explanation; (c) if any test (e.g. a normality test in the appendix) is not actually used in a decision, either justify it in one sentence or remove it.

---

### F14 — Promote RQ1.4b out of the appendix into evaluation *(Important; depends on F1)*
**Transcript:** 00:27:07 *"Why do you put it in appendix only?" — "Because I wasn't sure if I should." — "No, this is going to become part of the evaluation … it's one of the three types of environment. This will become clear once you restructure … the research questions."*

**Relevant location(s):** §5.5 (RQ1.4b appendix-only, p. 56), Appendix A.1 + Tables A.1–A.3 (p. 121–122); §4.7.5 (p. 26); §6.2.2 (p. 90).

**Relevant text (Appendix A.1):** *"RQ1.4b is reported as supporting sensitivity evidence only, not as a primary thesis-facing number: kind's worker 'nodes' are Docker containers sharing one host kernel…"*

**Reasoning:** The supervisor sees the kind multi-worker stage as one of the *evaluation environments*, so it belongs in the main evaluation narrative once RQs are reorganised by environment (F1). **Caveat/tension:** the thesis gives a real technical reason it is appendix-only — kind workers share one kernel, so it measures CNI-bridge cost, not true cross-host networking (the genuine multi-host penalty is RQ1.5b on AKS). This is worth raising with the supervisor (see §4), because the appendix placement was a *deliberate methodological* choice, not an oversight.

**Recommended revision:** After F1, fold RQ1.4b into the main evaluation as a named environment/sensitivity condition under RQ1, but **retain the explicit scope caveat** (kind = single-host CNI-bridge proxy, not real cross-host). Do not silently elevate it to a primary number.

---

### F15 — Config tables: detail in appendix, key facts in body *(Minor)*
**Transcript:** 00:27:42 *"should this be in the appendix? These are the settings that I use for the run." — "No, you have the source for that … put it in the appendix and mention this particular thing in the text as well."* / 00:28:10 *"Because now it gets cluttered."*

**Relevant location(s):** Benchmark-config tables: Table 5.1 (p. 37), 5.3 (p. 43), 5.8 (p. 53), 5.13 (p. 63), and the AKS deployment metadata.

**Reasoning:** Full run settings clutter the body; the body should carry only the salient values, with full detail in the appendix (and you already source them to frozen artifacts).

**Recommended revision:** Move verbose per-run settings to the appendix; in the body keep a compact statement of the parameters that matter for interpretation, with a cross-reference.

---

### F16 — Local-vs-cloud infrastructure comparison table *(Important)*
**Transcript:** 00:28:26 *"have a table about the infrastructure details between this and what you use locally."* / 00:28:50 *"maybe you gave the cloud the super large instance, of course it's going to be faster … " — "I tried to keep it the same." — "Exactly. So … show that with the table … local configuration and cloud configuration."*

**Relevant location(s):** §4.2/§4.7.6 (RQ1.5 setup, p. 27); §5.6.2 + Table 5.13 (AKS config, p. 63); local-execution setup in §4.2–4.4.

**Reasoning:** A reviewer will suspect the cloud was given more resources. A side-by-side cores/memory table forecloses that objection and demonstrates a fair comparison.

**Recommended revision:** Add one table: rows = {cores, memory, SKU, CPU controls}, columns = {local config, cloud/AKS config}, with the rest of the detail in the annex. State explicitly that resources were matched.

---

### F17 — Validation vs. observations ordering *(Minor; open)*
**Transcript:** 00:29:56 *"Didn't it make sense to have validation before these observations?" — "I tried to follow the exact template that was provided." — "But … they don't say that you need to have these observations before the validation, right? … If it's there, fine."* / 00:30:26 *"Maybe your validation is also using to some extent these observations, so that's fine."*

**Relevant location(s):** Chapter 6 ordering — §6.1–6.3 (per-RQ observations) precede §6.4 Validation (p. 110) and §6.5 Evaluation (p. 111).

**Relevant text (§6.4/§6.5):** §6.5 states it *"does not repeat the per-RQ 'Evaluation.' paragraphs in sections 6.1 to 6.3 … the credibility of the underlying measurements is consolidated separately in section 6.4."*

**Reasoning:** The supervisor raised, then largely self-resolved, this — the order may be fine if validation depends on the observations, or if the template dictates it. **Genuinely unresolved.**

**Recommended revision:** Confirm against the program template whether validation should precede observations. If the template is silent and your validation consumes the observations, keep current order and add one sentence justifying it. (See §4.)

---

### F18 — Keep sourcing tables to GitHub/frozen artifacts *(Minor; praise → continue)*
**Transcript:** 00:24:02 *"this is something I really like. Please continue doing this. You source your table with your GitHub."*

**Relevant location(s):** Table captions throughout Chapter 5 (e.g. *"Source: condition_summaries.csv in rq1_1_20260515_111428"*); §4.8 Artifact Freezing and Reproducibility (p. 32).

**Reasoning/Recommendation:** No change needed — maintain this practice; it underpins the Reproducibility contribution (§7.2).

---

### F19 — Keep RQ-to-related-work linkage; highlight it; add references *(Minor; praise → small action)*
**Transcript:** 00:15:05 *"you … link it to your research questions … you can even highlight it … at the end."* / 00:15:25 *"I need to put in references."* / 00:36:52 / 00:40:50 *"I really liked the way that you embed for every research question in the related work."*

**Relevant location(s):** Chapter 3, esp. §3.2 (*"RQ1.1 evaluates residual-stage boundaries … RQ1.2 adds a block-level boundary"*) and §3.5 Positioning (p. 17).

**Reasoning:** Strongly praised and identified as a "big plus point". Two small actions: consider visually emphasising the RQ linkage at the chapter's end, and fill the noted missing references.

**Recommended revision:** Keep the per-RQ embedding; add a short highlighted summary linking each RQ to its gap at the end of Chapter 3; insert the missing citations.

---

### F20 — Consider retitling related work as "Research Gap Analysis and Scope" *(Minor)*
**Transcript:** 00:00:02 *"in this chapter[,] related work … position of this thesis could actually be called research gap analysis." — "That could work quite well … research gap analysis and scope."*

**Relevant location(s):** Chapter 3 title "Related Work" (p. 15); §3.5 "Positioning of This Thesis" (p. 17).

**Reasoning:** The chapter already does gap analysis (§3.5 positioning). A retitle better signals that function.

**Recommended revision:** Optionally rename Chapter 3 (or §3.5) to "Research Gap Analysis and Scope." Low priority, low effort.

---

### F21 — Optional FABRIC / confidential-VM demo *(Minor; scope/defense-timing)*
**Transcript:** 00:32:06 *"a chain of the five services distributed in different regions … I can help you with that with Fabric."* / 00:33:30 *"a security company … hardware security … deploy this in the confidential VMs … Super Computing … Chicago in November."* / 00:36:19 *"that's going to take a bit of time extra, but I don't see it modifying anything but the results and discussion."*

**Relevant location(s):** Would extend Chapter 5 (Results) and Chapter 6 (Discussion); also §7.4 Future Work already lists *"cross-region placement"* and extending TEE to both services.

**Reasoning:** Explicitly **optional** and **does not gate the defense**. Affects only Results/Discussion. Decision is coupled to the defense-date choice (§5/§4).

**Recommended revision:** Treat as a *go/no-go* decision, not a required revision. If pursued, it pushes the defense to ~Aug 17 and adds a multi-region results subsection; if not, the thesis is complete after F1–F20.

---

### F22 — Address impact doubt (motivational, shapes framing) *(Important)*
**Transcript:** 00:16:59 *"the longer I'm working on it, the less I feel that this actually has impact … it's just measuring and measuring."* / Supervisor pushes back: 00:18:47 *"the decomposition … like saying in software, taking a monolith [into] microservices, has no impact. Is that true? … scientifically, that is not true."*

**Relevant location(s):** Framing of §7.2 Contributions (p. 120) and the Discussion (F7).

**Reasoning:** Not a defect in the text, but the supervisor wants the *significance* surfaced rather than hidden behind cautious framing. Directly addressed by implementing F7.

**Recommended revision:** Ensure Contributions and Discussion state the forward-looking significance (per-layer governance, cross-org composition) confidently but within evidence limits. Implementing F7 resolves this.

---

## 3. Cross-Cutting Issues

### 3.1 Research-question architecture *(the dominant cross-cutting issue)*
**Problem:** The RQ scaffold conflates *conceptual variables* with *evaluation environments*, producing 9+ numbered questions where ~2–3 exist conceptually. This scaffold is reused as the organising spine of five chapters, so the framing problem propagates everywhere.
**Affected sections:** Abstract (p. vii); §1.3 (p. 2–3); §1.4 Approach (p. 3); §4.7 (p. 24–31); all of Chapter 5; all of Chapter 6; §7.1 (p. 117).
**Coordinated strategy:** Do **F1 first**. Fix §1.3, then propagate the new numbering/grouping outward in this order: §1.4 → Chapter 4 stage map → Chapter 5 section headers → Chapter 6 section headers → §7.1 → Abstract. Keep all experiments; only re-label/re-group. F2 (base/alternative), F3 (RQ2.3 placement), and F14 (RQ1.4b promotion) are sub-decisions that resolve naturally once the spine is fixed — do not start them before F1.

### 3.2 Contribution & significance framing
**Problem:** The thesis frames its value defensively (bounded overhead, scope caveats) and the author doubts its impact; the supervisor wants the upside articulated.
**Affected sections:** §6.5 (p. 111); §6.2.5/§6.3.4; §7.2 (p. 120); Discussion.
**Coordinated strategy:** Implement F6 + F7 + F22 together as one "Significance & Generalisability" reflection in the Discussion, cross-referenced from Contributions. Keep claims evidence-bounded.

### 3.3 Figure quality & placement
**Problem:** Small in-figure fonts, one page-filling figure, and unsettled background-material placement.
**Affected sections:** Figs 2.1–2.13 (p. 5–13); result figures Ch. 5; Chapter 2 vs Chapters 4–5.
**Coordinated strategy:** One figure-pass: enlarge fonts (F8), shrink/rearrange the oversized figure (F9), add variability bands to result plots (F11), and during the same pass decide background placement (F10).

### 3.4 Evidence presentation & statistical rigor
**Problem:** Variability not shown on plots; curve shape unnamed; author cannot yet explain the statistics; config tables clutter the body; no fairness table for local-vs-cloud.
**Affected sections:** §4.5.3; Ch. 5 figures/tables; §6.2; §6.4.
**Coordinated strategy:** Group F11, F12, F13, F15, F16 into a single "results presentation + methods-clarity" pass. F18 (keep artifact sourcing) is the positive anchor of this cluster.

### 3.5 Integrity & compliance
**Problem:** No AI disclosure; references not yet verified.
**Affected sections:** §4.10; References; new Discussion/Conclusion subsection; Appendix.
**Coordinated strategy:** Implement F4 + F5 together (both stem from AI-use disclosure). Confirm program requirements with Martin (see §4).

---

## 4. Clarifications Needed From Reviewers

> These are points where the transcript is ambiguous, deictic ("this one"), or left unresolved. **Be conservative — confirm before acting.**

**C1 — How many research questions: two or three?**
*Feedback:* 00:05:11 *"fold it up to like 3 … research questions?" — "Yes"*; but also 00:05:49 *"fold into either two or three."*
*Why ambiguous:* The supervisor says both "three" and "two or three"; the final RQ2.3 placement (F3) determines whether security is one RQ or two.
*Interpretations:* (a) 2 RQs (split; security incl. trade-off); (b) 3 RQs (split; security; trade-off/recommendation); (c) 2 RQs + named sub-stages for environments.
*Ask:* "Do you want exactly two top-level RQs (split, security) with the trade-off folded into RQ2, or three with the trade-off as RQ3? Should the three evaluation environments be sub-questions or just labelled stages?"

**C2 — Which specific figure 'takes a whole page'?**
*Feedback:* 00:11:04 *"especially this one, just takes a whole page by itself."*
*Why ambiguous:* "this one" is deictic (pointing at the screen); no figure number is named.
*Interpretations:* (a) Fig 2.5 (detailed BasicBlock structure); (b) one of Figs 2.10–2.13 (security diagrams); (c) a result figure.
*Ask:* "Which figure were you pointing at as the full-page one — Fig 2.5, or one of the security diagrams?"

**C3 — Scope of the AI disclosure.**
*Feedback:* 00:12:38 *"To what extent do you need to explain … which model, date, do you have to add that info?" — "Maybe not to that extent."*
*Why ambiguous:* The supervisor is unsure whether model/version/date must be reported; defers to program rules (Martin).
*Interpretations:* (a) narrative description only; (b) + a sample prompt in the annex; (c) + model names/dates.
*Ask (to Martin/program):* "Does the AI-disclosure requirement need model names and dates, or a high-level description plus a sample prompt?"
*Handled 2026-06-01 (safe superset, pending program confirmation):* wrote a narrative disclosure that names the tool families (Claude 4.7/4.8, ChatGPT GPT-5.5, Perplexity, Consensus) and their specific uses, states what AI did NOT do, records two integrity safeguards, and includes sample prompts in the annex. If Martin says less detail is required, the tool names/prompts can be trimmed without restructuring.

**C4 — RQ1.4b: promote to main text despite the single-host caveat?**
*Feedback:* 00:27:13 *"this is going to become part of the evaluation."* vs. thesis's deliberate appendix placement (kind = single-host CNI proxy).
*Why ambiguous:* The supervisor may not have registered the methodological reason it was placed in the appendix.
*Interpretations:* (a) move the full stage into the body, caveat retained; (b) move only a summary into the body, data stays in appendix; (c) keep in appendix but reference more prominently from the body.
*Ask:* "RQ1.4b is appendix-only because kind workers share one kernel, so it measures CNI-bridge cost rather than true cross-host networking (the real multi-host penalty is RQ1.5b on AKS). Do you still want it in the main evaluation, and at what level of detail given that caveat?"
*Resolved 2026-06-01 → option (b):* a compact summary of the Stage~K cross-node alternative now appears in the Ch.5 deployment evaluation (`kubernetes.tex`), with the full data tables kept in the appendix and the single-host CNI-bridge caveat retained prominently. Not promoted to a primary number, since that would overclaim against the genuine cross-host AKS measurement (Stage~C multi-node). Flag for supervisor confirmation at next meeting.

**C5 — Validation before observations?**
*Feedback:* 00:29:56 question raised, then 00:30:26 *"that's fine."*
*Why ambiguous:* Raised and softened but never definitively resolved; turns on the template.
*Interpretations:* (a) reorder so Validation (6.4) precedes per-RQ observations; (b) keep order, add a justifying sentence; (c) order is template-mandated — no change.
*Ask:* "Does the program template require Validation before the per-RQ observations, or is the current order acceptable since validation draws on those observations?"

**C6 — Which figures need error bars/variability bands — all or only some?**
*Feedback:* 00:21:27 / 00:22:03 (general principle, no figure list).
*Interpretations:* (a) all latency figures; (b) only those with material variance; (c) a representative subset.
*Ask:* "Should every latency figure carry error bars, or only the ones with non-trivial variance?"

**C7 — Defense window.**
*Feedback:* 00:37:33 *"two windows … before the 8th or the week after the 15th of July"*; 00:38:03 *"the 17th"*; 00:40:07 *"with Fabric … 17th of August."*
*Why ambiguous:* The dates are inconsistent in the transcript (8th/13th/15th/17th July vs 17 Aug) and depend on the FABRIC go/no-go.
*Interpretations:* (a) early July (no FABRIC); (b) mid/late July online; (c) 17 Aug (with FABRIC).
*Ask:* "Can we pin the exact July dates, and confirm: writing-only → July, FABRIC included → 17 August?"

**C8 — RQ2.3 placement (records the mid-session reversal).**
*Feedback:* standalone (00:06:56) → under RQ2 (00:08:08).
*Ask:* "Final call on RQ2.3: a standalone discussion question, or kept under RQ2 since it also covers performance/operational cost?"

---

## 5. Revision Roadmap (prioritised)

### Critical revisions — affect acceptance / examiner expectations / integrity
1. ✅ **F1** — Refactor research questions into ~2–3 conceptual RQs; separate conceptual variables from evaluation environments. *(Do this first; everything else re-aligns to it — broken into Phase 0–6 in §5A.)* — confirm count via **C1/C8**. — **DONE 2026-06-01 (2 RQs; environment-coded stages; Phases 0–6 complete).**
2. ✅ **F4** — Add AI-usage disclosure (+ sample prompt in annex). — confirm scope via **C3**. — **DONE 2026-06-01. C3 handled as the safe superset (narrative disclosure + named tools + sample prompts in annex); model families named so it is trivially trimmable if the program (Martin) wants less. NB: the disclosure asserts every reference was verified against its primary source — that assertion is made true by completing item #7 (F5).**
3. ☐ **F5** — Verify every reference is genuine and correctly cited.

### Important revisions — improve rigor, clarity, coherence
4. ✅ **F14** — Promote RQ1.4b into the main evaluation (after F1), keeping its scope caveat — confirm via **C4**. — **DONE 2026-06-01 (C4 resolved as option (b): summary in body, full tables in appendix, caveat retained).**
5. ✅ **F2** — Frame `b`-variants as base-case vs. alternative. — **DONE (folded into F1).**
6. ✅ **F3** — Keep RQ2.3 as the trade-off contribution under RQ2 — confirm via **C8**. — **DONE (folded into F1; retained as "Trade-off Synthesis").**
7. ☐ **F6 + F7 + F22** — Add a Discussion reflection on generalisability (transformers/other NNs) and broader impact (per-layer policy, cross-org "digital embassies", inter-layer API).
8. ☐ **F16** — Add local-vs-cloud infrastructure comparison table.
9. ☐ **F11** — Add error bars / variability bands to latency figures — confirm scope via **C6**.
10. ☐ **F12** — Name the latency-vs-service-count functional shape; reconcile "monotonic"/"non-linear" wording.
11. ☐ **F13** — Ensure you can explain (and the text justifies) the statistical tests; prune any unused test.
12. ☐ **F8** — Enlarge in-figure fonts (Background diagrams first).

### Minor revisions — editorial / formatting / structure
13. ☐ **F15** — Move verbose run-config to appendix; reference key facts in body.
14. ☐ **F9** — Shrink/rearrange the full-page figure — confirm which via **C2**.
15. ☐ **F10** — Decide background-material placement.
16. ☐ **F17** — Resolve Validation-vs-observations ordering — confirm via **C5**.
17. ☐ **F19** — Highlight RQ↔related-work linkage at chapter end; add missing references.
18. ☐ **F20** — Optionally retitle Chapter 3 as "Research Gap Analysis and Scope."
19. ☐ **F18** — Continue sourcing tables to frozen artifacts (no change; maintain).

### Scope decision (separate track)
20. ☐ **F21** — FABRIC multi-region / confidential-VM demo: go/no-go, coupled to defense date (**C7**). Affects only Results/Discussion; does not gate the defense.

---

## 5A. F1 Execution Plan — Research-Question Refactor (step-by-step)

F1 is the keystone item and is large enough to hit model rate limits if done in one pass. The fix is to separate the one-time **decision** (Phase 0, needs Opus high) from the **mechanical relabeling** (Phases 1–6, fine on a lighter model). Lock Phase 0 first; do not touch prose until the mapping table is settled.

### Phase 0 — Lock the structure once  ✅ (2026-06-01 — 2 RQs, environment-coded stages; see `_rq_refactor_phase0_lock.md`)
The supervisor's framing: separate *conceptual changes* from *evaluation environments*.
- **Conceptual changes (these become the RQs):** split granularity → security hardening.
- **Evaluation environments (these become stages, NOT RQs):** controlled local → local Kubernetes → Azure AKS, with single-node as base case and multi-node as the alternative.

| New | Question | Absorbs (old) |
|-----|----------|---------------|
| **RQ1** | Which architectural split of ResNet-18 gives a credible two-part decomposition, and how does its latency/overhead behave across the three evaluation environments? | RQ1.1, RQ1.2, RQ1.3 (split selection) + RQ1.4, RQ1.5 (as *environments*); RQ1.4b / RQ1.5b as base-vs-alternative |
| **RQ2** | What performance and operational overhead does security hardening (identity + mTLS + authz, then selective confidential VM) add to the selected split deployment? | RQ2.1, RQ2.1b, RQ2.2 |
| **RQ2.3** *(keep under RQ2; promotable to RQ3)* | Which hardening configuration is the most defensible trade-off across performance, operational complexity, and protection scope? | RQ2.3 |

This works whether the supervisor lands on "two" or "three" RQs (**C1**) — RQ2.3 just detaches into RQ3 if needed.

### Phases 1–6 — Apply mechanically (one section per message)
Propagate the locked table outward in dependency order. Each is a separate, short request; none needs Opus high — they're relabeling, not reasoning.

- [x] **Phase 1 — §1.3 + §1.4.** Rewrite the RQ list and the Approach paragraph. *(Highest leverage; do first.)* — **DONE 2026-06-01.**
- [x] **Phase 2 — §4.7.** Relabel the stage-specific method subsections to the new scheme. — **DONE 2026-06-01** (whole `methods.tex` relabeled; verified by grep + clean compile).
- [x] **Phase 3 — Chapter 5.** Section headers + the one-line intro per stage. — **DONE 2026-06-01** (all 6 files; verified by grep + clean compile).
- [x] **Phase 4 — Chapter 6.** Section headers + the synthesis cross-references. — **DONE 2026-06-01** (all analysis files; verified by grep + clean compile).
- [x] **Phase 5 — §7.1 + Abstract.** Update the summary narrative. — **DONE 2026-06-01** (conclusion relabeled; abstract had no RQ IDs; clean compile).
- [x] **Phase 6 — Sweep.** grep the source for stray `RQ1.4`, `RQ1.5b`, etc.; fix `\label` / `\ref` cross-references and figure captions. — **DONE 2026-06-01** (Ch.2/3, appendix, tikz figures; zero stray sub-IDs repo-wide except the intentional manifest reference; clean 152 pp compile).

### Rate-limit strategy
- **Model split:** Opus high for **Phase 0 only**; **Sonnet 4.6** (or Opus without extended thinking) for Phases 1–6 — mechanical edits don't need the reasoning budget and won't drain the Opus limit. Paste only the section being edited, never the whole thesis.
- **Better: Claude Code on the repo.** The thesis is LaTeX sourced to GitHub; re-pasting `.tex` into chat each turn is what burns tokens. Claude Code edits the source files directly and rebuilds the PDF — hand it the Phase 0 table and say "apply Phase 1 to `introduction.tex`." This is what fixes the "thesis isn't being updated" problem, since it writes to the actual files.
- **Note:** from the PDF alone the edits can't be applied for you in chat; paste the relevant `.tex` section and a ready-to-paste per-phase edit packet can be produced inline.

---

## 6. Implementation Checklist

| Done | # | Task | Thesis section(s) | Reason for change | Effort | Dependencies |
|:----:|---|------|-------------------|-------------------|--------|--------------|
| ✅ | 1 | Restructure RQs into 2–3 conceptual questions; demote environments to sub-stages *(see §5A, Phase 0–6)* | §1.3; propagate to §1.4, §4.7, Ch.5, Ch.6, §7.1, Abstract | Examiner says environments aren't RQs (F1) | **High** | Resolve C1, C8 first — **DONE 2026-06-01 (C1=2 RQs, C8=RQ2.3 under RQ2). Phases 0–6 all complete; 152pp clean compile.** |
| ✅ | 2 | Reframe single-node as base case, multi-node as alternative | §1.3, §4.7.5/.7/.11, §5.5/5.7/5.10, §6.2.2/6.2.4 | "B without A" reads oddly (F2) | Low | After #1 — **DONE; folded into F1: base case vs. "Stage K/C/H1 (cross-node/multi-node) alternative" used throughout.** |
| ✅ | 3 | Keep RQ2.3 as trade-off contribution under RQ2 | §1.3, §4.7.13, §5.12, §6.3.3 | Valued conceptual contribution (F3) | Low | After #1; C8 — **DONE; retained as "Trade-off Synthesis" under RQ2 (not standalone).** |
| ✅ | 4 | Promote RQ1.4b to main evaluation, retain single-host caveat | §5.5, Appendix A.1, §4.7.5, §6.2.2 | One of the evaluation environments (F14) | Medium | After #1; C4 — **DONE 2026-06-01. C4 → option (b): compact summary promoted into Ch.5 main eval (`kubernetes.tex` Stage~K cross-node §, headline numbers + per-condition penalty envelope inline), full tables retained in appendix, single-host caveat kept. Methods/appendix lead-ins re-aligned. Clean compile (152 pp).** |
| ✅ | 5 | Write AI-usage disclosure section | New subsection in Ch.6/7; extend §4.10 | Required disclosure (F4) | Medium | C3 — **DONE 2026-06-01. New ToC-visible `\section{Use of Generative AI Tools}` (`sec:methods-ai`) after §4.10 Ethics: discloses Claude 4.7/4.8 (language editing), Perplexity + Consensus (lit discovery), ChatGPT 5.5 + Claude 4.7 (locating/triaging evidence in papers); states what AI did NOT do (no results/figures/analysis generated); two integrity safeguards (refs + data verified against primary sources). Clean compile (154 pp).** |
| ✅ | 6 | Add sample AI prompt to annex | Appendix A | Builds reader trust (F4) | Low | #5; C3 — **DONE 2026-06-01. `\section{Sample Generative AI Prompts}` (`sec:appendix-ai-prompts`) with 3 representative prompts (language edit / lit discovery / locating evidence) + verification note.** |
| ☐ | 7 | Verify all references / citations | References (p.125+); in-text | Guard against fabricated refs (F5) | Medium | Pairs with #5 |
| ☐ | 8 | Add generalisability + impact reflection (transformers, per-layer policy, digital embassies, inter-layer API) | Discussion (Ch.6); cross-ref §7.2 | Reflect on applicability & significance (F6/F7/F22) | Medium | Independent |
| ☐ | 9 | Add local-vs-cloud infrastructure comparison table | §4.2/§5.6.2 (Table 5.13 area) | Pre-empt "bigger cloud instance" critique (F16) | Low | Independent |
| ☐ | 10 | Add error bars / CI bands to latency figures | Figs 5.1, 5.3, 5.4, 5.6, 5.7 | Show measurement variability (F11) | Medium | C6; data already in CSVs |
| ☐ | 11 | Characterise latency curve shape; reconcile wording | Figs 5.3/5.4; §6.2.1, §6.2.5, Abstract | Name the function, not just "non-linear" (F12) | Low–Medium | Pairs with #10 |
| ☐ | 12 | Confirm/justify statistical tests; prepare viva explanation; prune unused tests | §4.5.3; §5.4.4, §6.4 notes; appendix | Defense readiness + rigor (F13) | Low–Medium | Independent |
| ☐ | 13 | Enlarge in-figure fonts; expand boxes | Figs 2.1–2.13 (then result figs) | Readability (F8) | Medium | Independent |
| ☐ | 14 | Shrink/rearrange the full-page figure | Likely Fig 2.5 or 2.10–2.13 | Flow (F9) | Low | C2 |
| ☐ | 15 | Move verbose run-config to appendix; reference in body | Tables 5.1/5.3/5.8/5.13 | Declutter body (F15) | Low | Independent |
| ☐ | 16 | Decide & apply background-material placement | Ch.2 vs Ch.4–5 | Conceptual vs chapter-specific (F10) | Low | Do during figure pass |
| ☐ | 17 | Resolve Validation-vs-observations order | §6.4 vs §6.1–6.3 | Possible reorder (F17) | Low | C5 |
| ☐ | 18 | Highlight RQ↔related-work links; add missing refs | §3.2, §3.5 | Praised; strengthen (F19) | Low | Independent |
| ☐ | 19 | Optional: retitle Chapter 3 | Ch.3 title / §3.5 | Signals gap analysis (F20) | Low | Independent |
| ☐ | 20 | Maintain artifact sourcing in table captions | Ch.5 captions; §4.8 | Praised; keep (F18) | None | — |
| ☐ | 21 | Decide FABRIC / confidential-VM demo | Ch.5/Ch.6 (if pursued) | Optional, defense-coupled (F21) | High (if yes) | C7 |

**Non-thesis action items from the session (logistics):** email Alexandros Koufakis (CC supervisor) for a June 3 chat on FABRIC; talk to Agalos about FABRIC availability; respond on the defense window (C7); follow up on the hardware-security company / Supercomputing demo.

---

## 7. Contradictions & Tensions in the Feedback

1. **RQ2.3 placement reversed mid-session.** Standalone "discussion … by itself" (00:06:56) → "keep it in the line of two" (00:08:08). *Resolution in transcript:* under RQ2. **Confirm (C8).**
2. **"Two or three" RQs.** "like 3 … research questions" (00:05:11) vs "fold into either two or three" (00:05:49). **Confirm (C1).**
3. **RQ1.4b appendix placement.** Supervisor: move into evaluation (00:27:13). Thesis: deliberately appendix-only for a sound methodological reason (kind = single-host). Not a flat contradiction, but the instruction may not account for the rationale. **Confirm (C4).**
4. **Defense dates inconsistent.** July 8 / 13 / 15 / 17 vs August 17 (00:37:33–00:40:12). **Confirm (C7).**
5. **Impact, you vs supervisor.** You doubt the work's impact (00:17:00–00:18:07); the supervisor strongly disagrees (00:18:47+). Resolve by *writing* the significance (F7/F22), not by leaving the doubt in the text.

---

## 8. Unanswered Questions to Resolve Before Revising

1. **How many top-level RQs — 2 or 3?** (C1) — gates the entire restructure.
2. **Final RQ2.3 placement** — under RQ2 or standalone? (C8)
3. **AI-disclosure scope** — narrative only, +sample prompt, or +model/date? Ask Martin/program. (C3)
4. **RQ1.4b** — promote to body despite the single-host caveat, and at what detail? (C4)
5. **Validation ordering** — does the template mandate the current order? (C5)
6. **Which figure is the full-page one?** (C2)
7. **Error bars on which figures — all or only high-variance ones?** (C6)
8. **Defense window** — exact July dates, and the August-17 fallback if FABRIC is pursued. (C7)
9. **FABRIC / confidential-VM demo** — in or out? Determines whether Results/Discussion expand and which defense date applies. (F21/C7)
10. **Curve characterisation** — is a fitted/quantitative form expected, or a qualitative "approximately linear, modulated by activation size" sufficient? (relates to F12)

---

*Prepared from the feedback transcript (Recording_5) and the thesis PDF. Every feedback item is anchored to a transcript timestamp and a thesis section/page so each link can be checked against the sources. No thesis text has been rewritten; recommendations are scoped to interpretation and planning, and uncertain points are flagged for reviewer confirmation rather than guessed.*
