# Internal Timing Mode — Building Plan

## Exploratory Compute-Distribution Profiling for ResNet-18

**Status:** Planning only. No implementation.
**Branch:** Exploratory — does not modify the thesis-facing split benchmark.
**Date:** 2026-04-17

---

## Phase 1 — Codebase Audit for Reuse

### 1.1 Components Reusable Unchanged

| Component          | File                                                               | Reuse Notes                                                                           |
| ------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Model loading      | `src/models/resnet_splits.py` → `get_full_model()`                 | Returns pretrained ResNet-18 in eval mode. No changes needed.                         |
| Timer              | `src/benchmark/timer.py` → `PerfTimer`, `perf_counter_ms()`        | Context manager around `time.perf_counter()`. Directly applicable.                    |
| CPU stabilisation  | `src/benchmark/cpu_stabilisation.py` → `apply_cpu_stabilisation()` | Standalone; call once at startup. Config-driven. Fully reusable.                      |
| Warmup calibration | `src/benchmark/warmup.py` → `run_warmup_calibrated()`              | Generic: accepts any `infer_fn`. Reusable as-is for whole-model warmup.               |
| Artifact logger    | `src/benchmark/logging.py` → `ArtifactLogger`                      | `save_config_copy()`, `save_environment()`, `save_json()`, `save_csv()`. All generic. |
| Config loader      | `src/benchmark/config.py` → `load_config()`                        | YAML loader + dataclass. Needs extension (new fields), not modification.              |

### 1.2 Components Requiring a New Path

| Component         | Why                                                                                                                                                                                                                                                                                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Runner            | `BenchmarkRunner` is coupled to the split/monolithic condition loop with gRPC subprocess management. Internal timing needs its own runner that iterates instrumented forward passes.                                                                                                          |
| Client            | `MonolithicClient` does a plain `model(input)` with one timing boundary. Internal timing needs a client/wrapper that times sub-components.                                                                                                                                                    |
| Analysis          | `statistics.py` computes condition-level summaries keyed on `condition` column. Internal timing produces per-unit timings with a hierarchical naming scheme. New aggregation logic required, though the statistical primitives (mean, median, std, CI, percentiles) are reusable as patterns. |
| Plots             | `plots.py` generates split-benchmark-specific plots (overhead vs activation, stationarity by condition). Internal timing needs different visualisations (ranked bar charts, hierarchy tables). New plot functions required.                                                                   |
| Report generation | Currently embedded in `run_analysis.py`. Internal timing needs its own report template.                                                                                                                                                                                                       |

### 1.3 Model Construction Suitability

The current `get_full_model()` returns a standard `torchvision.models.resnet18()` with the full PyTorch module hierarchy intact:

```
ResNet
├── conv1          Conv2d(3, 64, 7×7, stride=2)
├── bn1            BatchNorm2d(64)
├── relu           ReLU(inplace=True)
├── maxpool        MaxPool2d(3, stride=2)
├── layer1         Sequential
│   ├── [0]        BasicBlock
│   │   ├── conv1, bn1, relu, conv2, bn2
│   └── [1]        BasicBlock
│       ├── conv1, bn1, relu, conv2, bn2
├── layer2         Sequential
│   ├── [0]        BasicBlock (with downsample)
│   │   ├── conv1, bn1, relu, conv2, bn2, downsample
│   └── [1]        BasicBlock
│       ├── conv1, bn1, relu, conv2, bn2
├── layer3         Sequential
│   ├── [0]        BasicBlock (with downsample)
│   │   ├── conv1, bn1, relu, conv2, bn2, downsample
│   └── [1]        BasicBlock
│       ├── conv1, bn1, relu, conv2, bn2
├── layer4         Sequential
│   ├── [0]        BasicBlock (with downsample)
│   │   ├── conv1, bn1, relu, conv2, bn2, downsample
│   └── [1]        BasicBlock
│       ├── conv1, bn1, relu, conv2, bn2
├── avgpool        AdaptiveAvgPool2d(1×1)
└── fc             Linear(512, 1000)
```

All modules are accessible as named attributes. However, two operations inside `BasicBlock.forward()` are **not** registered modules:

1. **Residual addition:** `out += identity` — a raw tensor operation, no module
2. **Final ReLU:** `out = self.relu(out)` — reuses the same `self.relu` module as the mid-block ReLU

The `downsample` submodule (1×1 conv + batchnorm) is a registered `nn.Sequential` and is accessible.

**Conclusion:** Module-level hooks can cover all registered operations (conv, bn, relu, downsample). The residual add requires explicit instrumentation because it is not a module. The shared relu module means hooks cannot distinguish mid-block relu from post-add relu without additional logic.

### 1.4 What Must Remain Completely Separate

| Boundary                               | Rationale                                                      |
| -------------------------------------- | -------------------------------------------------------------- |
| `run_experiment.py`                    | Must not be modified. Entry point for thesis-facing benchmark. |
| `run_analysis.py`                      | Must not be modified. Entry point for thesis-facing analysis.  |
| `src/benchmark/runner.py`              | Must not be modified. Orchestrates gRPC split benchmarks.      |
| `src/client/split_client.py`           | Must not be modified. gRPC client for split conditions.        |
| `src/services/`                        | Must not be modified. Service B infrastructure.                |
| `configs/rq1/1.1/`, `configs/rq1/1.2/` | Must not be modified. Thesis-facing configs.                   |
| All existing results                   | Must not be touched.                                           |

The internal timing mode lives in its own files, its own config directory, its own entry point.

---

## Phase 2 — Profiling/Timing Hierarchy

### 2.1 Hierarchy Levels

The profiling hierarchy has four levels:

| Level             | Granularity                    | Example Names                     | Count  |
| ----------------- | ------------------------------ | --------------------------------- | ------ |
| **L0: Model**     | Whole forward pass             | `model`                           | 1      |
| **L1: Stage**     | Named top-level regions        | `stem`, `layer1`–`layer4`, `head` | 7      |
| **L2: Block**     | Individual BasicBlocks         | `layer3.0`, `layer3.1`            | 8      |
| **L3: Operation** | Operations inside a BasicBlock | `layer3.0.conv1`, `layer3.0.add`  | varies |

### 2.2 Stage-Level Decomposition (L1)

The model forward pass decomposes into 7 stages:

| Stage Name | Modules Covered                      | Notes                                                                       |
| ---------- | ------------------------------------ | --------------------------------------------------------------------------- |
| `stem`     | `conv1` → `bn1` → `relu` → `maxpool` | Initial feature extraction. Grouped because these always execute as a unit. |
| `layer1`   | `layer1[0]` + `layer1[1]`            | First residual stage. No spatial downsampling.                              |
| `layer2`   | `layer2[0]` + `layer2[1]`            | Stride-2 downsampling at block 0.                                           |
| `layer3`   | `layer3[0]` + `layer3[1]`            | Stride-2 downsampling at block 0.                                           |
| `layer4`   | `layer4[0]` + `layer4[1]`            | Stride-2 downsampling at block 0.                                           |
| `avgpool`  | `avgpool`                            | Global average pooling to 1×1.                                              |
| `fc`       | `flatten` + `fc`                     | Classification head. Includes the flatten operation.                        |

**Why `stem` and not separate `conv1`, `bn1`, `relu`, `maxpool`:**
The stem operations are trivially fast individually and always execute as an inseparable prefix. Grouping them as `stem` at L1 keeps the stage-level table clean. Their internals are still available at L3 if needed.

**Why `avgpool` and `fc` are separate stages:**
They are architecturally distinct operations (spatial aggregation vs classification). Keeping them separate at L1 allows the user to see whether the classifier head is a meaningful compute region.

### 2.3 Block-Level Decomposition (L2)

Each stage (layer1–layer4) expands into its constituent BasicBlocks:

| Block Name | Parent Stage | Has Downsample?          |
| ---------- | ------------ | ------------------------ |
| `layer1.0` | `layer1`     | No                       |
| `layer1.1` | `layer1`     | No                       |
| `layer2.0` | `layer2`     | Yes (stride-2 conv + bn) |
| `layer2.1` | `layer2`     | No                       |
| `layer3.0` | `layer3`     | Yes (stride-2 conv + bn) |
| `layer3.1` | `layer3`     | No                       |
| `layer4.0` | `layer4`     | Yes (stride-2 conv + bn) |
| `layer4.1` | `layer4`     | No                       |

`stem`, `avgpool`, and `fc` do not have block-level children. Their L1 timing is their finest standard granularity. (Stem internals are available as L3 operations.)

### 2.4 Operation-Level Decomposition (L3)

Inside each BasicBlock, the forward path executes this operation sequence:

```
identity = x                          (not timed — trivial assignment)
out = self.conv1(x)                   → {block}.conv1
out = self.bn1(out)                   → {block}.bn1
out = self.relu(out)                  → {block}.relu1        ← first relu call
out = self.conv2(out)                 → {block}.conv2
out = self.bn2(out)                   → {block}.bn2
if self.downsample is not None:
    identity = self.downsample(x)     → {block}.downsample   ← only in blocks with stride change
out += identity                       → {block}.add          ← not a module
out = self.relu(out)                  → {block}.relu2        ← second relu call (same module)
```

**Operation naming convention:**

| Operation          | Timing Name          | Module? | Notes                                                                       |
| ------------------ | -------------------- | ------- | --------------------------------------------------------------------------- |
| First convolution  | `{block}.conv1`      | Yes     | `nn.Conv2d`                                                                 |
| First batchnorm    | `{block}.bn1`        | Yes     | `nn.BatchNorm2d`                                                            |
| Mid-block ReLU     | `{block}.relu1`      | Yes\*   | `nn.ReLU`. \*Same module as relu2.                                          |
| Second convolution | `{block}.conv2`      | Yes     | `nn.Conv2d`                                                                 |
| Second batchnorm   | `{block}.bn2`        | Yes     | `nn.BatchNorm2d`                                                            |
| Downsample path    | `{block}.downsample` | Yes     | `nn.Sequential(Conv2d, BatchNorm2d)`. Only on blocks 2.0, 3.0, 4.0.         |
| Residual addition  | `{block}.add`        | **No**  | Raw `out += identity`. Must be explicitly timed.                            |
| Post-add ReLU      | `{block}.relu2`      | Yes\*   | Same `self.relu` module. Cannot be distinguished from relu1 by hooks alone. |

**Stem operations (L3, optional):**

| Operation         | Timing Name    | Module? |
| ----------------- | -------------- | ------- |
| Initial conv      | `stem.conv1`   | Yes     |
| Initial batchnorm | `stem.bn1`     | Yes     |
| Initial ReLU      | `stem.relu`    | Yes     |
| Max pooling       | `stem.maxpool` | Yes     |

### 2.5 Naming Convention Summary

The naming scheme is hierarchical dot-separated:

```
model                         L0  whole forward pass
├── stem                      L1  stage
│   ├── stem.conv1            L3  operation
│   ├── stem.bn1              L3
│   ├── stem.relu             L3
│   └── stem.maxpool          L3
├── layer1                    L1  stage
│   ├── layer1.0              L2  block
│   │   ├── layer1.0.conv1    L3  operation
│   │   ├── layer1.0.bn1      L3
│   │   ├── layer1.0.relu1    L3
│   │   ├── layer1.0.conv2    L3
│   │   ├── layer1.0.bn2      L3
│   │   ├── layer1.0.add      L3
│   │   └── layer1.0.relu2    L3
│   └── layer1.1              L2
│       └── ...
├── layer2                    L1
│   ├── layer2.0              L2
│   │   ├── ...
│   │   ├── layer2.0.downsample  L3  (present on .0 blocks of layer2–4)
│   │   └── ...
│   └── layer2.1              L2
├── layer3                    L1
│   └── ...
├── layer4                    L1
│   └── ...
├── avgpool                   L1  stage (no L2/L3 children)
└── fc                        L1  stage (no L2/L3 children)
```

---

## Phase 3 — Instrumentation Approach

### 3.1 Approaches Evaluated

#### Approach A: PyTorch Forward Hooks

Register `register_forward_pre_hook()` and `register_forward_hook()` on selected modules. Capture `time.perf_counter()` in each hook.

**Advantages:**

- Non-intrusive — works with unmodified model
- Automatically tracks all registered modules
- Easy to enable/disable at runtime
- No code duplication of the forward path

**Limitations:**

- Cannot time non-module operations (residual `+=`, `torch.flatten`)
- Shared `self.relu` module in BasicBlock — a single hook fires for both relu1 and relu2. Disambiguating requires tracking call order per iteration.
- Hook overhead: two Python function calls per timed module per forward pass. For operation-level timing of the full network (~50+ hook pairs), this adds measurable overhead.
- Hooks fire inside `torch.no_grad()` context — fine for timing, no gradient concern.

#### Approach B: Custom Instrumented Forward Methods

Write a custom `InstrumentedResNet` wrapper that replaces the `forward()` and BasicBlock `forward()` with versions containing explicit `perf_counter()` calls between operations.

**Advantages:**

- Full control over timing boundaries
- Can time non-module operations (residual add, flatten)
- No hook overhead — timing is inline
- Clearest mapping from code to timing names

**Limitations:**

- Duplicates the forward logic — must be validated against the original
- Must track upstream BasicBlock changes if torchvision is updated
- More code to maintain

#### Approach C: `torch.profiler` / Autograd Profiler

Use PyTorch's built-in profiler (`torch.profiler.profile()` with `record_shapes=True`).

**Advantages:**

- Zero instrumentation code
- Can capture operator-level timings automatically
- Can export chrome traces

**Limitations:**

- Reports operator-level timings (aten ops), not module-level timings — mapping aten ops back to named modules requires extra work
- Profiler overhead is significant and not constant across operations
- Output format (chrome trace / table) is not directly usable for the structured hierarchy we need
- Less control over exactly what is measured and how
- Does not directly support the custom naming hierarchy
- Not designed for repeated-measures statistical reporting

#### Approach D: Hybrid — Hooks for Modules, Explicit Timing for Non-Module Operations

Use forward hooks for all module-boundary timings. For operations that are not modules (residual add, flatten), use an instrumented BasicBlock subclass that overrides only `forward()` to add timing around those specific operations.

**Advantages:**

- Minimal code duplication (only BasicBlock.forward is overridden)
- Hooks handle all module timings automatically
- Explicit timing handles the two non-module operations cleanly
- Moderate overhead

**Limitations:**

- Requires replacing each BasicBlock instance with an instrumented variant (module surgery)
- Still has the shared-relu disambiguation problem unless the override handles it
- More complex than pure Approach B

### 3.2 Recommendation: Approach B — Custom Instrumented Forward

**Approach B is recommended.**

**Rationale:**

1. **Correctness:** Full control over every timing boundary. No ambiguity about what is measured.
2. **Non-module operations:** Residual add and flatten are timed naturally without hooks or workarounds.
3. **Shared relu:** The two relu calls are explicitly timed as `relu1` and `relu2` with no disambiguation logic.
4. **Low overhead:** `time.perf_counter()` calls are inlined. No hook dispatch overhead.
5. **Maintainability:** The instrumented forward is a single class with a clear, auditable mapping from operations to timing names. ResNet-18 is frozen for this thesis — there is no risk of upstream changes.
6. **Compatibility:** The wrapper loads the same pretrained weights from `get_full_model()`. Functional equivalence is verified by comparing outputs before any profiling begins.
7. **Interpretability:** Each timing name maps to exactly one code path. No indirection through hook registrations.

**Why not hooks (Approach A or D):**
The shared-relu problem and the non-module operations (add, flatten) mean hooks alone cannot produce the clean timing hierarchy defined in Phase 2 without workarounds. Those workarounds (call counters, module surgery) add complexity without a clear benefit, since we control the model and it is architecturally frozen for the thesis.

**Why not torch.profiler (Approach C):**
It answers a different question (operator-level kernel timings) and does not support the structured module-level hierarchy, repeated-measures methodology, or custom naming this mode requires.

### 3.3 Instrumentation Architecture

The instrumented model is a wrapper class — `InstrumentedResNet` — that:

1. Receives the pretrained `ResNet` model from `get_full_model()`
2. Holds references to all original modules (no weight copying)
3. Implements `forward()` with `perf_counter()` calls around each timing unit
4. Returns both the output tensor and a `dict[str, float]` of timing measurements
5. Supports a configurable timing level (stage-only, stage+block, full operation)

**The wrapper does NOT modify the original model's modules.** It references them directly. The forward path calls each module explicitly rather than relying on the model's own `forward()`.

**Functional equivalence is validated before any profiling** by comparing the wrapper's output to `model(input)` on the same inputs, with the same tolerance as the existing parity check.

### 3.4 Limitations to Acknowledge

1. **Timing overhead:** Each `time.perf_counter()` call costs ~0.1–0.5 µs on modern CPUs. With ~30 timing points for full operation-level profiling, overhead is ~10–15 µs per forward pass. For a forward pass of ~30 ms, this is <0.05%. Negligible, but should be measured and recorded.
2. **Nested timing consistency:** Parent timings (stage, block) are measured independently with their own start/stop points. The sum of children will not exactly equal the parent because of Python interpreter overhead between calls. This is expected and should be documented, not corrected.
3. **Residual add timing:** The `out += identity` operation is extremely fast (sub-microsecond for small tensors). Its timing may be dominated by `perf_counter()` overhead. This should be reported but is still worth including for completeness.
4. **`torch.no_grad()` scope:** All inference runs under `torch.no_grad()`. The wrapper maintains this.

---

## Phase 4 — Timing Units for Version 1

### 4.1 Version 1 Scope (Include)

**L0 — Model total:**

| Unit          | Name    | Description                                              |
| ------------- | ------- | -------------------------------------------------------- |
| Total forward | `model` | Wall-clock time for the entire instrumented forward pass |

**L1 — Stages (7 units):**

| Unit         | Name      |
| ------------ | --------- |
| Stem         | `stem`    |
| Layer 1      | `layer1`  |
| Layer 2      | `layer2`  |
| Layer 3      | `layer3`  |
| Layer 4      | `layer4`  |
| Average pool | `avgpool` |
| Classifier   | `fc`      |

**L2 — Blocks (8 units):**

| Unit            | Name       |
| --------------- | ---------- |
| Layer 1 Block 0 | `layer1.0` |
| Layer 1 Block 1 | `layer1.1` |
| Layer 2 Block 0 | `layer2.0` |
| Layer 2 Block 1 | `layer2.1` |
| Layer 3 Block 0 | `layer3.0` |
| Layer 3 Block 1 | `layer3.1` |
| Layer 4 Block 0 | `layer4.0` |
| Layer 4 Block 1 | `layer4.1` |

**L3 — Operations (all blocks, version 1):**

Inside each BasicBlock (example for `layer2.0` which has downsample):

| Unit               | Name                  |
| ------------------ | --------------------- |
| Conv 1             | `layer2.0.conv1`      |
| BatchNorm 1        | `layer2.0.bn1`        |
| ReLU 1 (mid-block) | `layer2.0.relu1`      |
| Conv 2             | `layer2.0.conv2`      |
| BatchNorm 2        | `layer2.0.bn2`        |
| Downsample         | `layer2.0.downsample` |
| Residual add       | `layer2.0.add`        |
| ReLU 2 (post-add)  | `layer2.0.relu2`      |

For blocks without downsample (e.g., `layer1.0`), the downsample row is absent.

**Stem operations (L3):**

| Unit        | Name           |
| ----------- | -------------- |
| Conv 1      | `stem.conv1`   |
| BatchNorm 1 | `stem.bn1`     |
| ReLU        | `stem.relu`    |
| Max pool    | `stem.maxpool` |

**Total timing units in V1:**

| Level                                    | Count   |
| ---------------------------------------- | ------- |
| L0 model                                 | 1       |
| L1 stages                                | 7       |
| L2 blocks                                | 8       |
| L3 ops (8 blocks × 7–8 ops + 4 stem ops) | ~60     |
| **Total**                                | **~76** |

### 4.2 Deferred to Later

- Per-operation timing inside the `downsample` submodule (its internal conv + bn). V1 treats `downsample` as an atomic unit.
- Memory profiling (peak memory per stage/block).
- FLOP estimation per unit. This is computable analytically and does not require runtime measurement. Can be added later as a static annotation.

### 4.3 Excluded Entirely

- GPU timing (CUDA events). This mode is CPU-only.
- Gradient-related timing. Inference only.
- Multiple model architectures. ResNet-18 only.
- Batch sizes >1. Single-request profiling only.

---

## Phase 5 — Measurement Methodology

### 5.1 Execution Structure

Reuse the same nested-repetition philosophy as the split benchmark, scaled appropriately:

| Parameter           | Internal Timing Default                              | Rationale                                                                                                                      |
| ------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Rounds              | 3                                                    | Sufficient for cross-round consistency. Internal timing has less process-level variance than gRPC benchmarks.                  |
| Warmup iterations   | 30                                                   | Same warmup philosophy. Empirical stabilisation check retained.                                                                |
| Measured iterations | 100                                                  | Each iteration produces ~76 timing measurements. 3 × 100 = 300 observations per timing unit. Sufficient for robust statistics. |
| Cooldown            | 0 seconds                                            | No condition switching — single model runs continuously. No cooldown needed.                                                   |
| Seed                | 42                                                   | Same fixed deterministic input tensor.                                                                                         |
| Input               | Fixed tensor (seed 42), shape (1, 3, 224, 224), FP32 | Same as split benchmark.                                                                                                       |

**Why fewer rounds/iterations than the split benchmark:**
The split benchmark measures differences between conditions under process-boundary overhead, where variance is higher. Internal timing measures a single model's forward pass decomposition with no process boundary, no gRPC, no serialization. Variance sources are limited to OS scheduling and cache effects. 3 × 100 = 300 samples per unit is ample for robust percentile and CI estimation.

### 5.2 Warmup

Reuse `run_warmup_calibrated()` from `src/benchmark/warmup.py`:

- Run 30 warmup iterations of the full instrumented forward pass
- Monitor trailing-window CV (window=10, threshold=0.02) on the `model`-level total time
- Record calibration evidence
- Discard all warmup iterations

### 5.3 CPU Stabilisation

Reuse `apply_cpu_stabilisation()` from `src/benchmark/cpu_stabilisation.py`:

- Apply threading, affinity, priority controls before measurement
- Record metadata in `environment.json`
- Use the same config structure

**Default profile:** Single-threaded (1 intra-op, 1 inter-op, 1 OMP/MKL/OpenBLAS, 1 core pinned, SMT avoided). This matches the `fully_controlled` profile and ensures internal timing results are directly comparable with the split benchmark's monolithic baseline.

### 5.4 Primary Metrics Per Timing Unit

| Metric         | Definition                                                                     |
| -------------- | ------------------------------------------------------------------------------ |
| `mean_ms`      | Arithmetic mean across all measured iterations (all rounds)                    |
| `median_ms`    | Median                                                                         |
| `std_ms`       | Sample standard deviation (ddof=1)                                             |
| `p95_ms`       | 95th percentile                                                                |
| `min_ms`       | Minimum observed                                                               |
| `max_ms`       | Maximum observed                                                               |
| `pct_of_model` | `(unit_mean_ms / model_mean_ms) × 100` — percentage of total forward-pass time |

**No CI or significance testing.** This is exploratory profiling, not hypothesis testing. The metrics above are sufficient to characterise compute distribution. If cross-round consistency is desired, report `round_cv` (coefficient of variation of per-round means) per unit.

### 5.5 Timing Overhead

Record the total overhead of instrumentation by comparing:

- `model` timing (sum of all `perf_counter()` deltas) vs a plain `model(input)` call timed end-to-end

Report the difference as `instrumentation_overhead_ms` and `instrumentation_overhead_pct` in metadata. This provides transparency about measurement cost.

### 5.6 Nested Timing Consistency

**Do not force children to sum to parent.** Independently measure:

- Each parent (stage-level timing wraps the entire stage forward)
- Each child (block/op timings wrap individual calls)

Report the residual: `parent_mean - sum(children_means)` as `timing_gap_ms`. This represents Python interpreter overhead between timing calls. It should be small (<1% of parent). If it is large, it indicates an instrumentation error.

Document in the report:

> _Parent timings and the sum of their children are measured independently. A small positive residual (the "timing gap") is expected due to Python interpreter overhead between `perf_counter()` calls. This gap does not represent missing compute._

---

## Phase 6 — Output/Report Design

### 6.1 Artifacts Produced

| File                             | Format   | Contents                                                                                                                                         |
| -------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `config.yaml`                    | YAML     | Copy of the timing config                                                                                                                        |
| `environment.json`               | JSON     | Platform, stabilisation metadata, git commit                                                                                                     |
| `raw_timings.csv`                | CSV      | Per-iteration timing for every unit. Columns: `round`, `iteration`, `unit_name`, `level`, `elapsed_ms`                                           |
| `summary.csv`                    | CSV      | Per-unit summary statistics: `unit_name`, `level`, `parent`, `n`, `mean_ms`, `median_ms`, `std_ms`, `p95_ms`, `min_ms`, `max_ms`, `pct_of_model` |
| `round_consistency.csv`          | CSV      | Per-unit per-round mean, plus `round_cv`                                                                                                         |
| `timing_gaps.csv`                | CSV      | Parent vs sum-of-children consistency check                                                                                                      |
| `warmup_calibration.json`        | JSON     | Warmup stabilisation evidence                                                                                                                    |
| `report.md`                      | Markdown | Human-readable report (see below)                                                                                                                |
| `plots/compute_distribution.png` | PNG      | Horizontal bar chart of `pct_of_model` for all L1+L2 units                                                                                       |

### 6.2 CSV Schema: `raw_timings.csv`

```
round,iteration,unit_name,level,elapsed_ms
1,1,model,L0,31.245
1,1,stem,L1,2.134
1,1,layer1,L1,5.678
1,1,layer1.0,L2,2.812
1,1,layer1.0.conv1,L3,0.987
...
```

This flat format is simple to load and filter. The `level` column enables quick grouping. The `unit_name` column is the hierarchical dot-separated name.

### 6.3 CSV Schema: `summary.csv`

```
unit_name,level,parent,n,mean_ms,median_ms,std_ms,p95_ms,min_ms,max_ms,pct_of_model
model,L0,,300,31.24,31.10,0.45,32.01,30.50,33.12,100.00
stem,L1,model,300,2.13,2.10,0.08,2.28,2.00,2.45,6.82
layer1,L1,model,300,5.67,5.65,0.12,5.88,5.40,6.10,18.15
layer1.0,L2,layer1,300,2.81,2.80,0.06,2.92,2.70,3.00,9.00
layer1.0.conv1,L3,layer1.0,300,0.98,0.97,0.03,1.04,0.92,1.10,3.14
...
```

### 6.4 Report Structure (`report.md`)

```markdown
# Internal Timing Report — ResNet-18 Compute Distribution

## Configuration

[config summary]

## Environment

[platform, stabilisation status]

## Warmup

[stabilisation status, final CV]

## Instrumentation Overhead

[overhead_ms, overhead_pct]

## Stage-Level Summary (L1)

[table: 7 stages, sorted by pct_of_model descending]

## Block-Level Summary (L2)

[table: 8 blocks, sorted by pct_of_model descending]

## Operation-Level Summary (L3) — Grouped by Block

[for each block: table of ops sorted by pct_of_model]

## Ranked Operations (Top 20 by Compute Share)

[flat table of top 20 L3 operations by pct_of_model]

## Timing Gap Analysis

[parent vs children consistency table]

## Cross-Round Consistency

[units with highest round_cv]

## Observations

[auto-generated observations, e.g.:

- "layer4 accounts for X% of total compute"
- "conv operations dominate at Y% vs bn at Z%"
- "blocks with downsample are ~W ms slower than non-downsample blocks"]
```

### 6.5 Plots

**Version 1 — One plot:**

`compute_distribution.png` — Horizontal bar chart showing `pct_of_model` for all L1 stages and L2 blocks, grouped and colour-coded by level. This single plot provides the key visual answer to "where is time spent?"

**Deferred:**

- Flame-graph-style visualisation (nice-to-have, not blocking)
- Per-round time-series stationarity plot (only if cross-round consistency is a concern)
- Operation-level breakdown plot per block (useful but not essential for V1)

---

## Phase 7 — Config Design

### 7.1 Config Structure

The internal timing config follows the same YAML structure as the existing benchmark configs where applicable, with a new top-level section for timing-specific settings.

**Top-level sections:**

```yaml
experiment:
  experiment_name: "internal_timing_resnet18"
  experiment_description: "..."

model:
  model_name: "resnet18"
  pretrained: true
  device: "cpu"
  input_shape: [1, 3, 224, 224]
  precision: "fp32"
  seed: 42

timing:
  level: "full" # "stage" | "block" | "operation" | "full"
  include_stem_ops: true # L3 operations inside stem
  include_timing_gaps: true # parent vs children consistency
  measure_overhead: true # compare instrumented vs plain forward

benchmark:
  rounds: 3
  warmup_iterations: 30
  measured_iterations: 100

cpu_stabilisation:
  threading:
    pytorch_intra_op: 1
    pytorch_inter_op: 1
    omp_num_threads: 1
    mkl_num_threads: 1
    openblas_num_threads: 1
  affinity:
    enabled: true
    num_cores: 1
    avoid_smt: true
  priority:
    enabled: true
    nice_value: -5
  governor:
    set_governor: false
  turbo:
    disable_turbo: false
```

### 7.2 Timing Level Semantics

| Level Value   | What is Timed                 | Use Case                                              |
| ------------- | ----------------------------- | ----------------------------------------------------- |
| `"stage"`     | L0 + L1 only (8 units)        | Quick overview of compute distribution across stages  |
| `"block"`     | L0 + L1 + L2 (16 units)       | Block-level decomposition including per-block timings |
| `"operation"` | L0 + L1 + L2 + L3 (~76 units) | Full operation-level breakdown                        |
| `"full"`      | Same as `"operation"`         | Alias for clarity. Default.                           |

**Region filtering (deferred):** A future version could support `region: "layer3"` to restrict operation-level timing to a specific stage. Not needed for V1 — the full network is small enough to profile entirely.

### 7.3 Config Location

```
configs/
└── internal_timing/
    ├── timing_full.yaml              # Full operation-level profiling, strict controls
    ├── timing_stage_only.yaml        # Stage-level only, quick overview
    └── timing_smoke_test.yaml        # Minimal iterations for pipeline validation
```

Completely separate from `configs/rq1/`. No interference with thesis-facing configs.

---

## Phase 8 — Distinction from Split Benchmarking

### 8.1 What This Mode Measures

**Internal timing mode measures local compute distribution within a single-process, monolithic ResNet-18 forward pass.**

It answers:

- Where is compute time concentrated inside the network?
- Which stages, blocks, and operations are most expensive?
- How does compute cost change across the network depth?
- Are there regions that are disproportionately cheap or expensive?

### 8.2 What This Mode Does NOT Measure

| Not Measured                           | Why                                  |
| -------------------------------------- | ------------------------------------ |
| Service-boundary cost                  | No gRPC, no process boundary, no IPC |
| Serialization/deserialization overhead | No tensor serialization              |
| Activation-transfer burden             | No data transfer between processes   |
| Communication latency                  | No network or RPC                    |
| True split-inference performance       | No distributed execution             |
| Multi-process scheduling effects       | Single process only                  |

### 8.3 Relationship to RQ1.1 / RQ1.2

| Aspect               | RQ1.1 / RQ1.2 Split Benchmark                              | Internal Timing Mode                            |
| -------------------- | ---------------------------------------------------------- | ----------------------------------------------- |
| **Purpose**          | Measure boundary-crossing cost of real microservice splits | Measure internal compute distribution           |
| **Execution model**  | Two separate OS processes, gRPC                            | Single process, no RPC                          |
| **Primary metric**   | End-to-end latency including boundary overhead             | Per-unit compute time                           |
| **Comparison basis** | Monolithic vs split conditions                             | No comparison — single model characterization   |
| **Thesis role**      | Carry-forward selection of split points                    | Exploratory analysis to inform future reasoning |
| **Config files**     | `configs/rq1/1.1/`, `configs/rq1/1.2/`                     | `configs/internal_timing/`                      |
| **Entry point**      | `run_experiment.py`                                        | `run_internal_timing.py` (new)                  |
| **Output directory** | `results/rq1_*`                                            | `results/internal_timing_*`                     |

### 8.4 How This Mode Informs Later Work

Internal timing results can inform, but not replace, split-point analysis:

1. **Identifying compute-degenerate splits:** If internal timing shows that layer4 accounts for only 5% of total compute, a split after layer3 leaves almost no compute for Service B. This was already flagged by the RQ1.1 carry-forward degeneracy filter, but internal timing provides the explanatory evidence.

2. **Identifying natural compute boundaries:** If compute is sharply concentrated in certain blocks, those block boundaries may be interesting candidates for finer-grained splits in future research questions.

3. **Understanding overhead proportionality:** If a stage takes 2 ms of compute but the boundary-crossing interval is 5 ms, the boundary cost dominates. Internal timing provides the compute baseline against which boundary overhead can be contextualised.

4. **Supporting thesis narrative:** Internal timing provides the "why" behind the split-benchmark "what". It explains compute concentration rather than just measuring overhead.

**Critical caveat:** Internal timing does NOT predict split performance. A region that looks computationally interesting for splitting may have unfavourable activation shapes, or the boundary-crossing cost may dominate the compute saving. Only the split benchmark answers that question.

---

## Phase 9 — Implementation Plan

### 9.1 Preconditions

- [ ] This plan is approved
- [ ] A clean exploratory branch is created (or work is done on a feature branch)
- [ ] No modifications to existing thesis-facing files

### 9.2 Implementation Sequence

**Step 1: InstrumentedResNet wrapper** (`src/models/instrumented_resnet.py`)

New file. Does not modify `resnet_splits.py`.

- Class `InstrumentedResNet` that wraps a pretrained ResNet-18
- Holds references to all original modules
- Implements `forward(x) → (output, timings_dict)`
- `timings_dict` maps unit names (`str`) to elapsed times (`float`, milliseconds)
- Supports configurable timing level (stage / block / operation)
- Validate: output matches `model(x)` with atol=1e-6

**Validation criterion:** Before any profiling, run 5 inputs through both the wrapper and the original model. All outputs must match within tolerance. Exit if they don't.

**Step 2: Internal timing runner** (`src/benchmark/internal_timing_runner.py`)

New file. Does not modify `runner.py`.

- Loads model and wraps in `InstrumentedResNet`
- Runs warmup (reuse `run_warmup_calibrated`)
- Runs measurement loop: R rounds × M iterations
- Collects all timing dicts into flat rows
- Saves `raw_timings.csv` via `ArtifactLogger`
- Saves `warmup_calibration.json`
- Saves `environment.json` (reuse existing)

**Step 3: Internal timing config** (`src/benchmark/internal_timing_config.py`)

New file, or extend `config.py` with a new dataclass and loader. Decision: **new file** to avoid touching the existing config path.

- `InternalTimingConfig` dataclass
- `load_internal_timing_config(path) → InternalTimingConfig`
- Reuses `CpuStabilisationConfig` from existing `config.py`

**Step 4: Entry point** (`run_internal_timing.py`)

New file at project root. Does not modify `run_experiment.py`.

- `python run_internal_timing.py --config configs/internal_timing/timing_full.yaml`
- Loads config
- Applies CPU stabilisation
- Validates functional equivalence
- Runs internal timing benchmark
- Optionally runs analysis

**Step 5: Analysis** (`src/analysis/internal_timing_analysis.py`)

New file. Does not modify `statistics.py` or `plots.py`.

- `compute_summary(raw_timings_csv) → summary.csv`
- `compute_round_consistency(raw_timings_csv) → round_consistency.csv`
- `compute_timing_gaps(summary_csv) → timing_gaps.csv`
- `generate_report(results_dir) → report.md`
- `plot_compute_distribution(summary_csv) → plots/compute_distribution.png`

**Step 6: Config files**

- `configs/internal_timing/timing_full.yaml`
- `configs/internal_timing/timing_smoke_test.yaml`

**Step 7: Smoke test**

- Run with `timing_smoke_test.yaml` (1 round, 3 warmup, 5 measured)
- Verify: raw CSV is correct, summary computes, report generates, plot renders
- Verify: functional equivalence passes
- Verify: instrumentation overhead is <1%

### 9.3 File Inventory (New Files Only)

| File                                             | Purpose                          |
| ------------------------------------------------ | -------------------------------- |
| `src/models/instrumented_resnet.py`              | InstrumentedResNet wrapper       |
| `src/benchmark/internal_timing_runner.py`        | Measurement loop                 |
| `src/benchmark/internal_timing_config.py`        | Config dataclass and loader      |
| `src/analysis/internal_timing_analysis.py`       | Summary statistics, report, plot |
| `run_internal_timing.py`                         | Entry point                      |
| `configs/internal_timing/timing_full.yaml`       | Full profiling config            |
| `configs/internal_timing/timing_smoke_test.yaml` | Quick validation config          |

### 9.4 Files NOT Modified

| File                                 | Status                        |
| ------------------------------------ | ----------------------------- |
| `src/models/resnet_splits.py`        | Unchanged                     |
| `src/models/validation.py`           | Unchanged                     |
| `src/benchmark/runner.py`            | Unchanged                     |
| `src/benchmark/config.py`            | Unchanged                     |
| `src/benchmark/timer.py`             | Unchanged (imported and used) |
| `src/benchmark/warmup.py`            | Unchanged (imported and used) |
| `src/benchmark/cpu_stabilisation.py` | Unchanged (imported and used) |
| `src/benchmark/logging.py`           | Unchanged (imported and used) |
| `src/client/monolithic.py`           | Unchanged                     |
| `src/client/split_client.py`         | Unchanged                     |
| `src/services/*`                     | Unchanged                     |
| `src/analysis/statistics.py`         | Unchanged                     |
| `src/analysis/plots.py`              | Unchanged                     |
| `run_experiment.py`                  | Unchanged                     |
| `run_analysis.py`                    | Unchanged                     |
| `configs/rq1/*`                      | Unchanged                     |

### 9.5 Risk Assessment

| Risk                                                         | Likelihood | Mitigation                                                                                            |
| ------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------- |
| InstrumentedResNet produces different outputs than original  | Low        | Functional equivalence check is mandatory and fail-closed                                             |
| Timing overhead distorts measurements                        | Low        | Overhead is measured and reported. ~76 `perf_counter()` calls add <15 µs to a ~30 ms forward pass     |
| Contamination of thesis-facing code                          | Zero       | All new files. No existing files modified. Separate config directory. Separate entry point.           |
| Nested timings don't sum to parent                           | Expected   | Timing gaps are measured and reported. This is normal and documented.                                 |
| Very fast operations (add, relu) have high relative variance | Medium     | Report absolute times alongside percentages. Flag units where `std > mean` as unreliable for ranking. |

---

## Design Decisions Requiring Approval

Before implementation begins, the following decisions should be explicitly approved:

1. **Instrumentation approach:** Custom instrumented forward (Approach B), not hooks.
   - _Implication:_ The forward logic of ResNet-18 and BasicBlock is replicated in `InstrumentedResNet`. This is validated against the original model before every profiling run.

2. **Timing hierarchy:** Four levels (L0 model, L1 stage, L2 block, L3 operation) with the naming convention defined in Phase 2.
   - _Implication:_ ~76 timing units in full-operation mode.

3. **Stem grouping:** `stem` is a single L1 stage (conv1 + bn1 + relu + maxpool). Internal stem ops are L3.
   - _Alternative:_ Four separate L1 stages for each stem operation. Rejected because they are trivially fast and always execute together.

4. **Residual add as explicit timing unit:** `{block}.add` is timed even though it is not a module.
   - _Implication:_ This is the main reason hooks alone are insufficient.

5. **Shared relu disambiguation:** Two separate timing names (`relu1`, `relu2`) for the two calls to the same `self.relu` module.
   - _Implication:_ Only achievable with the custom forward approach.

6. **Measurement scale:** 3 rounds × 100 measured iterations = 300 samples per unit.
   - _Alternative:_ 5 × 200 = 1000 (matching split benchmark). Considered excessive for single-process profiling.

7. **No CI or significance testing.** Mean, median, std, p95 only. This is exploratory, not hypothesis-testing.
   - _Implication:_ Simpler reporting. Can always add CIs later if needed.

8. **Single plot in V1:** Horizontal bar chart of compute distribution. No flame graph.
   - _Implication:_ Keeps V1 lean. Flame graph can be added later.

9. **Separate entry point:** `run_internal_timing.py`, completely independent from `run_experiment.py`.
   - _Implication:_ No shared CLI. No risk of accidentally running the wrong mode.

10. **Separate config directory:** `configs/internal_timing/`, not inside `configs/rq1/`.
    - _Implication:_ Clean separation. No confusion about which configs are thesis-facing.
