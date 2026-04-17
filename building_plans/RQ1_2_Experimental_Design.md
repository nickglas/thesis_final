# RQ1.2 Experimental Design

## Fine-Grained Refinement Within the Carried-Forward Coarse Region

---

## 1. Research Question

> **RQ1.2:** Within the coarse late-stage region carried forward from RQ1.1 (layer2–layer3), does splitting at a finer block-level architectural boundary reveal latency or overhead differences not visible at stage-level granularity, and how do these differences relate to compute-balance shifts versus activation-transfer effects?

### Justification

RQ1.1 performed a coarse-boundary screening across all four ResNet-18 stage boundaries and carried forward two candidates:

- **`split_after_layer2`** (selected main, 33.741 ms mean end-to-end latency)
- **`split_after_layer3`** (selected reference, 33.938 ms mean end-to-end latency)

These two boundaries are adjacent coarse stages. RQ1.2 asks: **is the coarse stage granularity sufficient, or does within-stage refinement expose meaningful differences?**

This is a natural thesis progression:

1. **RQ1.1** selected a coarse region.
2. **RQ1.2** refines within that region at block-level granularity.
3. **RQ1.3** (future) will provide explanatory analysis.

RQ1.2 is deliberately scoped to test a single intermediate block-level split point — `layer3.0` — which sits architecturally between the two carried-forward coarse anchors. This creates a controlled three-point refinement within the selected region.

### Why `layer3.0` Is the Only New Split Point

ResNet-18's `layer3` contains exactly **2 BasicBlocks** (`layer3[0]` and `layer3[1]`). This means:

- `layer3.0` = split after block 0 of layer3 (i.e., after one block has executed)
- `layer3` = split after both blocks of layer3 (the full coarse stage)

There is only **one** valid intermediate split point within layer3. This is not a design choice — it is an architectural constraint.

### The Natural Experiment: Compute Balance vs. Activation Transfer

The `layer3.0` and `layer3` split points share a critical property: **they produce identical intermediate activation sizes.**

| Split Point | Intermediate Shape | Intermediate Size      |
| ----------- | ------------------ | ---------------------- |
| `layer3.0`  | (1, 256, 14, 14)   | 50,176 floats ≈ 196 KB |
| `layer3`    | (1, 256, 14, 14)   | 50,176 floats ≈ 196 KB |

This happens because both block 0 and block 1 of layer3 have the same output dimensions (BasicBlock preserves spatial and channel dimensions after the first block's downsampling). The downsampling occurs inside `layer3[0]` (stride-2 convolution + shortcut projection), so the output of block 0 already has the 256 × 14 × 14 shape.

This creates a natural experiment:

- **Activation-transfer burden is held constant** (196 KB in both cases).
- **Serialization cost is held constant** (same tensor shape).
- **Only compute balance changes**: `layer3.0` shifts one BasicBlock of computation from Service A to Service B compared to `layer3`.

Any observed latency difference between `layer3.0` and `layer3` is therefore attributable to **compute-balance effects alone**, not to activation-transfer or serialization differences. This is an unusually clean isolation of a single variable.

---

## 2. Dependency on RQ1.1

RQ1.2 depends on the RQ1.1 carry-forward decision:

- **`selected_main`**: `split_after_layer2` (33.741 ms)
- **`selected_reference`**: `split_after_layer3` (33.938 ms)
- **Rejected**: `split_after_layer1`, `split_after_layer4`
- **Fallback used**: No

The RQ1.1 carry-forward artifact (`carry_forward.json`) from run `rq1_1_20260416_093656` provides the authoritative selection. RQ1.2 includes both carried-forward splits as **coarse anchors** for direct comparison.

### RQ1.1 Is Frozen

The RQ1.1 experiment, its design document, and its results are frozen. RQ1.2 does not redesign or rerun RQ1.1. It extends the codebase with minimal changes to support one additional block-level split point.

---

## 3. Experiment Design

### Design Type: Controlled Within-Region Block-Level Refinement

The experiment is a **single-factor repeated-measures design**, identical in structure to RQ1.1:

- **Independent variable:** Inference configuration (**4 levels**)
- **Dependent variable:** End-to-end inference latency
- **Within-subjects:** All conditions tested on the same hardware with the same inputs

### Conditions

**Condition 0 — Monolithic Baseline**
Full ResNet-18 as a direct in-process function call. Same as RQ1.1 Condition 0.

**Condition 1 — Split after layer2 (coarse anchor, carried forward as `selected_main`)**

- Service A: initial block + layer1 + layer2
- Service B: layer3 through fc
- Intermediate tensor: 128 × 28 × 28 = 100,352 floats ≈ 392 KB
- Compute balance: moderately balanced
- **Role:** Upper bound of the refinement region. Direct comparability with RQ1.1.

**Condition 2 — Split after layer3.0 (new fine-grained point)**

- Service A: initial block + layer1 + layer2 + layer3[0]
- Service B: layer3[1] + layer4 + avgpool + fc
- Intermediate tensor: 256 × 14 × 14 = 50,176 floats ≈ 196 KB
- Compute balance: Service A now includes one additional BasicBlock vs. Condition 3
- **Role:** The fine-grained refinement point. Tests whether within-stage granularity matters.

**Condition 3 — Split after layer3 (coarse anchor, carried forward as `selected_reference`)**

- Service A: initial block + layer1 + layer2 + layer3 (full)
- Service B: layer4 + avgpool + fc
- Intermediate tensor: 256 × 14 × 14 = 50,176 floats ≈ 196 KB
- Compute balance: more work shifted to A, lighter B
- **Role:** Lower bound of the refinement region. Direct comparability with RQ1.1.

### Why These 4 Conditions

1. **Monolithic** provides the absolute baseline, ensuring overhead measurements are consistent with RQ1.1.
2. **layer2** and **layer3** are the RQ1.1 carry-forward anchors. Including them provides:
   - direct replication of RQ1.1 measurements under identical conditions
   - anchoring for the new fine-grained point
   - cross-experiment consistency validation
3. **layer3.0** is the only valid intermediate block-level point in the carried-forward region.

### Why NOT Include Other Split Points

- **`layer1`** was rejected by RQ1.1 carry-forward (not in the near-best non-degenerate set for refinement purposes; including it would broaden the experiment beyond the carried-forward region).
- **`layer4`** was flagged as compute-degenerate in RQ1.1 and rejected.
- **`layer2.0`**, **`layer2.1`**, **`layer4.0`**: These are outside the carried-forward refinement region. Including them would turn RQ1.2 into a second exhaustive sweep rather than a focused refinement.
- **`layer1.0`**, **`layer1.1`**: Same reasoning — outside the region of interest.

---

## 4. Measurement Contract

### Identical to RQ1.1

The measurement contract is unchanged from RQ1.1:

- **Primary metric:** Mean end-to-end inference latency (ms), measured with `time.perf_counter()`
- **Secondary metrics:** Median, p95, std, activation-transfer burden, compute per side, overhead ratio
- **Boundary-crossing metric:** `boundary_crossing_ms` (compound client-side interval)
- **Diagnostic metrics:** Same sub-timing decomposition as RQ1.1
- **Functional equivalence check:** Mandatory parity validation before measurement (same protocol)

### Additional Analytical Focus

RQ1.2 introduces one additional analytical lens:

**Compute-balance isolation:** Because `layer3.0` and `layer3` have identical activation sizes, the comparison between these two conditions isolates compute-balance effects from activation-transfer effects. The report should explicitly highlight:

- Whether `service_a_compute_ms` and `service_b_compute_ms` shift as expected when one BasicBlock moves between services
- Whether the end-to-end latency difference (if any) is consistent with the observed compute shift
- Whether the boundary-crossing interval changes despite identical activation sizes

This analysis uses the same metrics already recorded by the benchmark infrastructure. No new instrumentation is needed.

---

## 5. Benchmark Process

### Identical Core Protocol

All benchmark parameters match the RQ1.1 fully controlled profile:

| Parameter           | Value                                                 | Note |
| ------------------- | ----------------------------------------------------- | ---- |
| Model               | ResNet-18 (torchvision, pretrained)                   | Same |
| Input shape         | (1, 3, 224, 224), FP32                                | Same |
| Input data          | Fixed deterministic tensor (seed 42)                  | Same |
| Batch size          | 1                                                     | Same |
| Device              | CPU                                                   | Same |
| Communication       | gRPC, localhost, 127.0.0.1:50051                      | Same |
| Rounds              | 5                                                     | Same |
| Warmup iterations   | 50 per condition per round                            | Same |
| Measured iterations | 200 per condition per round                           | Same |
| Cooldown            | 5 seconds between conditions                          | Same |
| CPU stabilisation   | Fully controlled (1 thread, 1 core, SMT off, nice=-5) | Same |
| Parity validation   | 5 inputs, atol = 1e-5                                 | Same |
| Warmup calibration  | window=10, CV threshold=0.02                          | Same |

### Repetition Structure

Same nested structure as RQ1.1:

```
For each round r in 1..5:
    Generate condition-order permutation π_r (seeded: Random(42 + r))
    For each condition c in π_r:
        Start Service B subprocess (if split condition)
        Wait for gRPC channel ready (if split condition)
        Run gRPC parity validation (split conditions, round 1 only)
        Run 50 warmup iterations with calibration check (discarded)
        Run 200 measured iterations (recorded to raw_iterations.csv)
        Shut down Service B (if split condition)
        Cooldown pause: 5 seconds
```

### Per Condition Total

- 5 rounds × 200 = **1,000 measured iterations per condition**
- 4 conditions × 1,000 = **4,000 total measured iterations**

### Ordering, Fairness, and Reproducibility

Same as RQ1.1: seeded random permutation per round, same hardware/software/model weights, same CPU stabilisation, same cooldown, fixed seeds.

---

## 6. Statistical Reporting

### Same Framework as RQ1.1

All statistical outputs match the RQ1.1 analysis pipeline:

- **Per condition:** Mean, median, std, p5/p25/p75/p95/p99, min, max, 95% CI, secondary metric means
- **Per round × condition:** Mean, median, std, p95
- **Cross-round consistency:** Std of round means, range, CV → `round_consistency.json`
- **Cross-condition comparisons:** Overhead vs. monolithic, effect sizes (Cohen's d)
- **Significance testing:** Mann-Whitney U reported but de-emphasised (same caveats as RQ1.1)

### Visualization

Same plot suite as RQ1.1:

- `latency_boxplot.png` — box plot per condition
- `latency_violin.png` — violin plot with means and medians
- `overhead_vs_activation.png` — scatter: activation KB vs overhead ms
- `stationarity.png` — per-iteration time series per condition

### Additional RQ1.2-Specific Analysis (in report narrative)

The report narrative should address:

1. **Replication check:** Do the layer2 and layer3 conditions produce latency results consistent with RQ1.1? (Not a formal statistical test, but a sanity comparison of means and CIs.)

2. **Fine-grained comparison:** Is `layer3.0` latency distinguishable from `layer3`? From `layer2`? Where does it fall in the ordering?

3. **Compute-balance isolation:** Given identical activation sizes for `layer3.0` and `layer3`:
   - How do `service_a_compute_ms` and `service_b_compute_ms` differ?
   - Is the end-to-end difference (if any) consistent with the compute shift direction?
   - Does `boundary_crossing_ms` change despite identical serialization payload?

4. **Granularity verdict:** Does block-level refinement within this region reveal differences that coarse stage boundaries missed?

---

## 7. Carry-Forward Rule

### Informational Execution

The carry-forward rule from RQ1.1 is applied to RQ1.2 results **informationally**. It runs with the same logic and parameters:

- **Primary criterion:** Minimize `end_to_end_latency_ms_mean`
- **Near-best window:** 5% around the best observed split mean
- **Degeneracy filter:** Minor side < 10% of total split compute
- **Tie-break:** Lower `activation_bytes_mean`

The rule output is recorded in `carry_forward.json` for completeness and consistency.

### Why Informational

RQ1.2's primary purpose is **refinement characterization**, not a second selection stage. The thesis dependency chain is:

- **RQ1.1** → selects coarse region → carries forward to **RQ1.2**
- **RQ1.2** → characterizes fine-grained differences within that region → informs **RQ1.3** explanatory analysis

RQ1.2 does not need to produce a new carry-forward decision to feed a subsequent experiment. The carry-forward rule runs to maintain methodological consistency and to document what would have been selected, but the results are not consumed by a downstream stage that depends on them.

---

## 8. Rejected Alternatives

### Alternative A: Sweep All Possible Block-Level Splits

**Design:** Test every block boundary in all four stages.

**Why rejected:** This would produce ~8+ conditions spanning the entire model, turning RQ1.2 into a second exhaustive sweep. It contradicts the purpose of a focused within-region refinement.

### Alternative B: Include layer1 and layer4 Anchors

**Design:** Add the rejected RQ1.1 splits as additional anchors.

**Why rejected:** These were explicitly rejected or filtered by the RQ1.1 carry-forward rule. Including them in RQ1.2 would undermine the carry-forward dependency chain.

### Alternative C: Multiple Block-Level Points per Stage

**Design:** Split within layer2 and layer4 as well as layer3.

**Why rejected:** The refinement region is defined by the RQ1.1 carry-forward. Only the layer2–layer3 region was selected. Within that region, layer3 has only 2 blocks, yielding exactly 1 intermediate point. Layer2 also has 2 blocks but splitting within layer2 would produce a point architecturally below the selected main — not a refinement within the region.

### Alternative D: Skip the Monolithic Baseline

**Design:** Only test the three split conditions, using RQ1.1 monolithic results.

**Why rejected:** Including the monolithic baseline costs only 1 additional condition and provides:

- direct overhead calculation without cross-experiment assumptions
- a built-in consistency check against RQ1.1

### Alternative E: Vary Benchmark Parameters

**Design:** Change rounds, iterations, or stabilisation settings from RQ1.1.

**Why rejected:** Keeping parameters identical ensures cross-experiment comparability. If RQ1.2 used different repetition counts, any observed differences could be attributed to experimental methodology rather than the split point.

---

## 9. Thesis Interpretation

### What This Experiment Supports Claiming

- Block-level granularity within the carried-forward coarse region either does or does not reveal latency differences beyond what coarse stage boundaries show.
- When activation sizes are held constant (layer3.0 vs. layer3), any observed latency difference is attributable to compute-balance effects rather than transfer-burden effects.
- The boundary-crossing interval either does or does not change when only compute balance shifts.
- The coarse stage granularity from RQ1.1 either is or is not sufficient for characterizing the selected region.

### What This Experiment Does NOT Support Claiming

- That block-level refinement generalises across all stages or all models.
- That one additional split point constitutes a comprehensive fine-grained sweep.
- Production-optimal deployment recommendations.
- GPU, cloud, or network inference results.

### Threats to Validity

**Internal validity:**

- Same as RQ1.1 (localhost, OS scheduling, Python/runtime effects).
- The single new split point limits the strength of generalization claims about "fine-grained" boundaries.

**External validity:**

- Single model, single protocol, CPU-only, batch size 1 (same as RQ1.1).
- Layer3 having exactly 2 BasicBlocks is specific to ResNet-18's architecture.

**Construct validity:**

- The claim of "compute-balance isolation" depends on serialization cost being truly determined by tensor size alone. If framework overhead scales with some other property, the isolation is imperfect.

**Conclusion validity:**

- Strong repetition (1,000 iterations per condition) reduces risk.
- The two coarse anchors provide built-in replication checks against RQ1.1.

---

## 10. Implementation Notes

### Codebase Changes (Minimal)

RQ1.2 reuses the existing benchmark infrastructure with minimal extensions:

1. **`src/models/resnet_splits.py`**: Extended to support block-level split notation (`layer3.0`). `PartA` and `PartB` now handle dot-notation split points, building partial stage modules. `ALL_SPLIT_POINTS` includes both coarse and block-level points. Backward-compatible `SPLIT_POINTS` alias preserved for RQ1.1.

2. **`src/services/service_b_runner.py`**: CLI `--split-after` choices updated to `ALL_SPLIT_POINTS`.

3. **`src/benchmark/runner.py`**: Output directory prefix derived from `config.experiment_name` instead of hardcoded `rq1_1_`.

4. **`run_analysis.py`**: Report title derived from `config.experiment_name` instead of hardcoded "RQ1.1".

5. **Config files**: `configs/rq1/1.2/rq1_2_fully_controlled.yaml` and `configs/rq1/1.2/rq1_2_experimental.yaml`.

No changes to: `src/benchmark/config.py`, `src/client/split_client.py`, `src/services/service_b.py`, `src/analysis/statistics.py`, `src/analysis/plots.py`, `src/models/validation.py`, `run_experiment.py`.

### Execution Commands

**Smoke test:**

```bash
python run_experiment.py configs/rq1/1.2/rq1_2_experimental.yaml
python run_analysis.py results/rq1_2_<timestamp>/
```

**Full thesis run:**

```bash
python run_experiment.py configs/rq1/1.2/rq1_2_fully_controlled.yaml
python run_analysis.py results/rq1_2_<timestamp>/
```

### Project Structure (RQ1.2 additions)

```
configs/
  rq1/
    1.2/
      rq1_2_fully_controlled.yaml    ← thesis-facing benchmark
      rq1_2_experimental.yaml        ← smoke test
```

All results will be written to `results/rq1_2_<timestamp>/` with the same artifact structure as RQ1.1.

---

## Appendix A: Activation Size Verification

The claim that `layer3.0` and `layer3` produce identical intermediate activation shapes was verified empirically:

```python
import torch
import torchvision

m = torchvision.models.resnet18()
x = torch.randn(1, 128, 28, 28)   # output of layer2

y0 = m.layer3[0](x)   # After block 0
y1 = m.layer3[1](y0)  # After block 1 (= full layer3)

print(y0.shape)  # torch.Size([1, 256, 14, 14])
print(y1.shape)  # torch.Size([1, 256, 14, 14])
print(y0.numel() * 4)  # 200704 bytes = 196 KB
print(y1.numel() * 4)  # 200704 bytes = 196 KB
```

The downsampling (stride-2 convolution + channel expansion 128→256) occurs entirely within `layer3[0]`. Block 1 preserves the dimensions. Both outputs are 256 × 14 × 14 = 50,176 floats = 196 KB.

---

## Appendix B: RQ1.1 Carry-Forward Summary

Source: `results/rq1_1_20260416_093656/carry_forward.json`

| Field                 | Value                            |
| --------------------- | -------------------------------- |
| Raw fastest           | `split_after_layer2` (33.741 ms) |
| Near-best window      | 5% → threshold 35.428 ms         |
| Near-best candidates  | layer1, layer2, layer3, layer4   |
| Degenerate candidates | layer4                           |
| Selected main         | `split_after_layer2` (33.741 ms) |
| Selected reference    | `split_after_layer3` (33.938 ms) |
| Rejected              | layer1, layer4                   |
| Fallback used         | No                               |

---

## Appendix C: Design Decision Record

| Decision                    | Choice                            | Alternative           | Rationale                                                                                         |
| --------------------------- | --------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- |
| Number of new split points  | 1 (layer3.0)                      | Sweep all blocks      | Only 1 valid intermediate point in layer3; sweeping beyond region contradicts carry-forward logic |
| Include monolithic baseline | Yes                               | Reuse RQ1.1 numbers   | Low cost, provides consistency check and direct overhead calculation                              |
| Include layer2 and layer3   | Yes, as anchors                   | Only test new point   | Enables cross-experiment replication and anchors the refinement                                   |
| Benchmark parameters        | Identical to RQ1.1                | Different repetitions | Cross-experiment comparability                                                                    |
| Carry-forward rule          | Informational                     | Binding selection     | RQ1.2 is refinement, not a second selection stage                                                 |
| Activation-size identity    | Highlighted as natural experiment | Treat as coincidence  | Too clean an isolation to ignore; strengthens thesis claims                                       |
