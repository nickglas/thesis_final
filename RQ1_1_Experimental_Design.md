# RQ1.1 Experimental Design

## From First Principles

---

## 1. Recommended RQ1.1

### Research Question

> **RQ1.1:** Which coarse architectural stage boundaries provide the most suitable two-part microservice decompositions of ResNet-18 under controlled local execution, and how do their latency and boundary-crossing costs compare to monolithic inference?

### Justification

This is a **coarse-boundary selection question**, not only an overhead-characterization question. It asks:

1. **How do coarse two-part decompositions compare against monolithic inference?**
2. **How do latency and boundary-crossing costs vary across coarse architectural boundaries?**
3. **Which boundaries are most suitable to carry forward into later thesis stages?**

This framing is stronger for the thesis than a pure "single boundary overhead" characterization because:

- It preserves **RQ1.1 as a selection stage**, which is necessary for later carry-forward logic.
- It still quantifies the cost of a single microservice boundary under controlled conditions.
- It compares **architecturally meaningful coarse boundaries** rather than a single arbitrary split.
- It supports a later dependency chain in which selected boundaries feed refinement and multi-microservice stages.

The question is deliberately scoped to:

- a single model (**ResNet-18**),
- a single communication protocol (**gRPC**),
- single-request inference (**batch size 1**),
- and localhost communication under a controlled local setup.

These constraints are deliberate. They eliminate unnecessary confounds and make the results interpretable while preserving thesis relevance.

---

## 2. Recommended Experiment Design

### Design Type: Controlled Coarse-Boundary Screening

The experiment is a **single-factor repeated-measures design**:

- **Independent variable:** Inference configuration (**5 levels: 1 monolithic baseline + 4 coarse architectural split points**)
- **Dependent variable:** End-to-end inference latency
- **Within-subjects:** All conditions tested on the same hardware with the same inputs

This is the strongest design because:

- it keeps the main experiment focused on **coarse architectural boundary selection**
- it avoids confounding multiple variables at once
- it maintains a clean comparison against monolithic execution
- it supports later thesis stages by yielding a carry-forward decision rather than only a descriptive characterization

### Conditions

**Condition 0 — Monolithic Baseline**
Full ResNet-18 executes as a direct in-process function call. No networking, no serialization, no process boundary. This is the gold-standard reference: the minimum possible inference latency with zero distribution overhead.

**Condition 1 — Split after layer1**
- Service A: initial block + layer1
- Service B: layer2 through fc
- Intermediate tensor: 64 × 56 × 56 = 200,704 floats ≈ 784 KB
- Compute balance: early-side light, later-side heavy

**Condition 2 — Split after layer2**
- Service A: initial block + layer1 + layer2
- Service B: layer3 through fc
- Intermediate tensor: 128 × 28 × 28 = 100,352 floats ≈ 392 KB
- Compute balance: moderately balanced

**Condition 3 — Split after layer3**
- Service A: initial block + layer1–layer3
- Service B: layer4 + avgpool + fc
- Intermediate tensor: 256 × 14 × 14 = 50,176 floats ≈ 196 KB
- Compute balance: later stage still meaningful, but more work shifted to A

**Condition 4 — Split after layer4 (before avgpool + fc)**
- Service A: initial block + layer1–layer4
- Service B: avgpool + fc
- Intermediate tensor: 512 × 7 × 7 = 25,088 floats ≈ 98 KB
- Compute balance: highly late split, likely degenerate on compute balance

### Why These 4 Split Points

These are the thesis-facing **coarse architectural stage boundaries** in ResNet-18. They correspond to meaningful named module groups and provide a clean stage-level sweep.

This scope is preferred over adding the earliest stem split because:

- the main purpose of RQ1.1 is **coarse screening and selection**
- mid- and late-stage boundaries are the more meaningful coarse candidates for later thesis stages
- the earliest split risks dominating figures in a trivial way due to very large activations and poor balance
- including it in the main sweep would make the story look more like an exhaustive characterization exercise than a thesis-guided selection stage

If the stem split is studied at all, it should be treated only as:

- appendix material,
- preliminary calibration,
- or an exploratory sensitivity point not part of the main RQ1.1 thesis-facing sweep.

### Execution Architecture

**Monolithic (Condition 0):**

```text
[Client Process]
  input_tensor → model(input_tensor) → output_tensor
  ↑ timing start              ↑ timing stop
```

**Split (Conditions 1–4):**

```text
[Client/Service A Process]          [Service B Process]
  input_tensor → part_A(input)
                    ↓
              serialize(intermediate)
                    ↓
              ──── gRPC call ────→   deserialize(intermediate)
                                     part_B(intermediate)
                                     serialize(output)
              ←─── gRPC response ──
              deserialize(output)
                    ↓
              output_tensor

  ↑ timing start                     ↑ timing stop (after deserialize)
```

### Key Design Decisions

**Service B is a separate OS process**, not a thread or in-process mock. This represents a real microservice boundary with true process isolation.

**Communication is via gRPC over localhost (127.0.0.1).** This removes real-network variability while preserving:

- real serialization,
- real RPC framing,
- real process-boundary overhead,
- and real inter-process communication.

Localhost therefore gives a lower-bound environment for boundary-related overhead.

**The monolithic baseline uses no gRPC.** It is a direct `model(input)` call. This is intentional: RQ1.1 asks what the total cost of introducing a microservice boundary is, compared to having no boundary at all. A gRPC-wrapped monolith would answer a different question.

**Timing is measured at the client/orchestrator.** This captures the full end-to-end latency seen by a caller, including compute, serialization, framework overhead, process-boundary crossing, and response reconstruction.

### Why gRPC

gRPC with Protocol Buffers is an appropriate default because it is:

- efficient and binary
- widely used in microservice systems
- based on a well-known transport stack
- supported well in Python
- a defensible choice for a thesis that wants microservice relevance without turning protocol choice into a separate experiment

### Hardware and Software

- **CPU inference only** for RQ1.1. GPU inference introduces additional confounds such as kernel launches, host-device transfers, and scheduling artifacts.
- **Single machine, localhost communication.** Real network effects are outside the scope of this first stage.
- **PyTorch in eval mode, `torch.no_grad()`.**
- **FP32 precision.**
- **Batch size 1.**
- **Fixed deterministic input tensor** for the main benchmark. This reduces variance and keeps the experiment focused on boundary effects rather than input heterogeneity.

### CPU-Behaviour Stabilisation Controls

To reduce run-to-run variance and improve measurement reproducibility, the benchmark applies environment-aware CPU-behaviour controls before any measurement begins. These follow standard practice in performance benchmarking literature (Beyer, Löwe & Wendler, "Reliable benchmarking: requirements and solutions", STTT 2019; LLVM Benchmarking Tips; Cui & Pericas, "Characterizing and Mitigating Performance Variability in Parallel Applications on Modern HPC multicore Systems", ICS 2025).

**Applied controls:**

| Control | Setting | Rationale |
|---|---|---|
| PyTorch intra-op threads | Fixed at 4 | Prevents non-deterministic thread pool sizing across runs. Matches the number of pinned physical cores. |
| PyTorch inter-op threads | Fixed at 1 | Single-input sequential inference; no benefit from graph-level parallelism. Eliminates inter-op scheduling variance. |
| OMP\_NUM\_THREADS / MKL\_NUM\_THREADS | Set to 4 | Ensures underlying BLAS and OpenMP libraries respect the same thread count. Propagated to Service B via environment. |
| CPU affinity (core pinning) | Pinned to 4 physical cores (SMT siblings excluded) | Avoids OS migration across cores, eliminates L1/L2 cache thrashing from migration, and avoids SMT contention. Applied via `os.sched_setaffinity()`. |
| Service B thread settings | Mirrors parent process | Thread-count environment variables are propagated to the Service B subprocess. Service B reads `OMP_NUM_THREADS` and calls `torch.set_num_threads()` accordingly. Ensures fairness: both monolithic and split conditions use identical thread configurations. |

**Reported but unavailable controls (WSL2/Hyper-V):**

| Control | Status | Note |
|---|---|---|
| CPU frequency governor | Unavailable | `cpufreq` sysfs is not exposed inside WSL2. CPU frequency is managed by the Windows host power plan. Users should set the Windows power plan to "High Performance" before running experiments. |
| Turbo boost disable | Unavailable | Neither `intel_pstate` nor `cpufreq/boost` sysfs entries are exposed inside WSL2. Boost behaviour is controlled by Windows. Note: on the AMD Ryzen 7 7800X3D, the 3D V-Cache design exhibits less frequency-induced variance than typical desktop CPUs, but this should be acknowledged as a limitation. |
| Process priority (nice) | Not elevated | Requires root privileges. The benchmark runs at default priority (nice=0). This is acceptable for a single-workload machine with no competing processes. |
| ASLR | Detected (full) | Address space layout randomisation is enabled (randomize\_va\_space=2). Disabling requires root. Impact on this benchmark is negligible since we measure wall-clock inference latency, not instruction counts. |

**Fairness guarantee:** All controls are applied symmetrically to all conditions. Thread counts, affinity, and environment variables are identical for monolithic and split configurations. The stabilisation layer runs once at benchmark startup, before any condition is executed.

**Metadata recording:** All applied and skipped controls are recorded in `environment.json` under the `cpu_stabilisation` key, ensuring full auditability and reproducibility.

---

## 3. Rejected Alternatives

### Alternative A: Single Representative Split Point

**Design:** Pick one split point, compare monolithic vs. split.

**Why rejected:** This does not answer the thesis-facing RQ1.1, because it does not perform a coarse architectural screening and cannot support a carry-forward boundary decision.

### Alternative B: Exhaustive Layer-by-Layer Sweep

**Design:** Test every possible layer as a split point.

**Why rejected:** This is too fine-grained for the purpose of RQ1.1. Many split points would be architecturally unhelpful, hard to interpret, or redundant. It would weaken the thesis story by making the experiment look like a blind exhaustive search rather than an architecturally grounded screening stage.

### Alternative C: Include Stem / Initial-Block Split in the Main Sweep

**Design:** Add a split after the stem / initial block.

**Why rejected for the main sweep:** Although defensible as an extreme sensitivity point, it is not the strongest thesis-facing default because it risks:

- trivially large activation-transfer burden
- poor compute balance
- visually dominating plots
- pulling the study toward characterization rather than selection

It may be retained only as appendix or exploratory material.

### Alternative D: Multiple Decomposition Paradigms

**Design:** Compare layer partitioning against tensor parallelism, pipeline parallelism, or other paradigms.

**Why rejected:** This broadens the thesis beyond what RQ1.1 needs and makes fair comparison much harder. RQ1.1 should stay focused on coarse sequential two-part decomposition.

### Alternative E: Multiple Communication Protocols

**Design:** Cross architectural boundary with protocol choice.

**Why rejected:** Protocol comparison is a separate concern. RQ1.1 should fix the protocol and study boundary choice.

### Alternative F: Include Containerization or Kubernetes

**Design:** Run RQ1.1 in Docker or Kubernetes.

**Why rejected:** RQ1.1 should isolate decomposition and boundary effects under controlled local execution. Container and orchestration effects belong later.

---

## 4. Measurement Contract

### Primary Metric

**Mean end-to-end inference latency (wall-clock time, milliseconds)**

- **Definition:** Time from the moment the input tensor is available in client memory to the moment the output tensor is available in client memory.
- **Timing instrument:** `time.perf_counter()`
- **Monolithic timing boundary:** Immediately before `model(input)` to immediately after return.
- **Split timing boundary:** Immediately before `part_A(input)` to immediately after client-side response deserialization.
- **Inclusions:** All computation, all serialization/deserialization, all gRPC overhead, all inter-process communication.
- **Exclusions:** Model loading, service startup, and channel establishment.

**Why this is primary:** RQ1.1 is a carry-forward selection stage. The selection decision should be based on the average per-request cost under repeated controlled trials. Mean end-to-end latency is therefore the most appropriate primary ranking metric.

### Secondary Metrics

**Median end-to-end latency** — Robust central-tendency companion to the mean.

**p95 end-to-end latency** — Captures tail behavior.

**Standard deviation of end-to-end latency** — Captures variability.

**Activation-transfer burden** — `activation_bytes_mean`: captures how much intermediate data is handed off across the boundary.

**Compute time per side** — `service_a_compute_ms_mean` and `service_b_compute_ms_mean`.

**Overhead ratio** — `(split_mean - monolith_mean) / monolith_mean × 100%`

### Boundary-Crossing Metric

Use:

```
boundary_crossing_interval_ms
```

not the looser phrase *communication overhead*, unless explicitly clarified.

**Definition:** Wall-clock interval from the start of serializing the intermediate tensor on Service A / caller side to the completion of response deserialization on the caller side.

**Purpose:** This metric captures the compound cost of crossing the service boundary. It may include:

- serialization
- deserialization
- gRPC framework overhead
- process-boundary transfer effects
- RPC-related waiting

It should not be described as a pure transport-only communication metric.

### Diagnostic-Only Metrics (Not for Main Claims)

These may be recorded but should remain diagnostic:

- request serialization time
- request deserialization time
- response serialization time
- response deserialization time
- gRPC round-trip time
- Service B internal timing
- CPU utilization
- memory usage
- system timestamp

### Why Diagnostic Metrics Are Separate

These sub-timings are useful for diagnosis and interpretation, but they may overlap or fail to sum cleanly. Thesis claims should therefore rest primarily on:

- end-to-end latency,
- activation-transfer burden,
- compute distribution,
- and the compound boundary-crossing interval.

### Functional Equivalence Check

Before any performance measurement, verify that:

- monolithic and split configurations produce numerically equivalent outputs for the same inputs
- all configurations use identical weights
- outputs match on a small set of test inputs

This is a precondition, not a performance result.

---

## 5. Benchmark Process

### Benchmark Conditions

| Parameter | Value | Justification |
|---|---|---|
| Model | ResNet-18 (torchvision, pretrained) | Standard, interpretable, manageable on CPU |
| Input shape | (1, 3, 224, 224), FP32 | Standard ImageNet shape |
| Input data | Fixed deterministic tensor | Reduces variance |
| Batch size | 1 | Measures per-request latency |
| Device | CPU | Avoids GPU confounds |
| Inference mode | `model.eval()`, `torch.no_grad()` | Standard inference |
| Communication | gRPC, localhost, unary RPC | Appropriate microservice baseline |
| Serialization | Protocol Buffers or equivalent raw-bytes tensor payload | Efficient and standard |
| Service deployment | Separate OS processes | Real process boundary |
| OS power profile | High performance if possible | Reduces frequency-scaling variance |
| CPU frequency | Pinned if possible | Reduces thermal and scaling artifacts |
| PyTorch threads (intra-op) | Fixed at 4 | Prevents non-deterministic thread pool sizing |
| PyTorch threads (inter-op) | Fixed at 1 | No graph parallelism needed for single-input inference |
| CPU affinity | 4 physical cores, SMT excluded | Avoids OS migration and L1/L2 cache thrashing |

### Warmup Policy

Warmup should remain explicit and condition-specific.

**Protocol:**

1. Before each condition in each round, run W = 50 warmup iterations initially.
2. Use a preliminary calibration run to verify stabilization.
3. Increase warmup count if required.
4. Exclude all warmup iterations from summaries.

### Measured-Run Policy

- **Per condition per round:** M = 200 measured iterations
- **Per condition total:** 5 rounds × 200 = 1,000 measured iterations

This is intentionally ambitious and should be kept.

### Repetition Structure

**Design:** Nested repetition with R = 5 independent rounds.

```
For each round r in 1..R:
    Generate condition-order permutation π_r
    For each condition c in π_r:
        Start/restart Service B (if applicable)
        Wait for service readiness
        Run W warmup iterations (discarded)
        Run M measured iterations (recorded)
        Record per-round summary statistics
        Shut down Service B (if applicable)
        Cooldown pause: 5 seconds
```

### Why Keep This Strong Repetition Structure

The proposed structure is operationally ambitious, but it should be preserved because it gives:

- strong statistical stability
- tight confidence intervals
- visibility into variance and distribution shape
- better protection against temporal and thermal drift
- more defensible thesis reporting

This is one of the strongest parts of the design and worth keeping.

### Ordering Strategy

**Within each round:** Conditions are tested in a randomized order using fixed seeds. This avoids fixed-order bias while keeping each condition in a clean measurement block.

### Fairness Controls

- Same model weights across all conditions
- Same input tensor across all conditions
- Same hardware
- Same software environment
- Same inference mode
- Same precision
- No concurrent benchmark workload
- Cooldown between conditions
- No condition-specific optimization path

### Process Asymmetry Note

In split conditions, Service A and Service B run in separate processes. Monolithic runs in a single process. This asymmetry is intentional. The benchmark is supposed to measure the full cost of introducing a real service boundary, not a process-symmetric toy comparison.

### Reproducibility Controls

- Fixed seeds
- Full environment recording
- System-state recording
- Raw per-iteration artifact preservation
- Code version recording
- Single config file determining all benchmark behavior

### Statistical Reporting

**Per condition:**
- Mean latency (primary)
- Median latency
- Standard deviation
- p5, p25, p75, p95, p99
- Min, max
- 95% confidence intervals

**Cross-condition comparisons:**
- `split_mean - monolith_mean`
- relative overhead ratio
- effect sizes
- non-parametric significance testing if appropriate

**Visualization:**
- box or violin plots
- latency distributions
- overhead vs. activation-transfer burden
- per-iteration stationarity checks

---

## 6. Carry-Forward Selection Rule

RQ1.1 must explicitly include a predeclared carry-forward rule.

**Primary criterion:** Minimize `end_to_end_latency_ms_mean`

**Near-best window:** Define a near-best window around the best observed split mean.

**Degeneracy filter:** Mark candidates as compute-degenerate if one side contributes too little to split compute subtotal.

**Tie-break:** Among valid near-best non-degenerate candidates, prefer lower `activation_bytes_mean`.

**Output categories:** The report must clearly distinguish:

- raw fastest boundary
- selected main candidate
- selected reference candidate
- rejected candidates

This is essential because RQ1.1 is not only descriptive; it is a selection stage for later thesis steps.

---

## 7. Thesis Interpretation

### What This Experiment Supports Claiming

- Coarse architectural boundaries differ in end-to-end latency penalty relative to monolithic inference.
- Coarse boundaries differ in activation-transfer burden and compute distribution.
- A raw fastest boundary is not automatically the best thesis-facing carry-forward boundary if it is compute-degenerate or otherwise excluded by the predeclared selection rule.
- The measured boundary-crossing interval provides a lower-bound view of service-boundary cost under localhost execution.
- The results support a coarse local carry-forward decision for later thesis stages.

### What This Experiment Does NOT Support Claiming

- A universal best partitioning strategy
- A production-optimal deployment recommendation
- A cloud deployment result
- Proof that distributed inference improves latency
- Generalization to GPU inference
- Generalization to all model families
- A pure communication-transport decomposition unless that is separately and cleanly isolated

### Threats to Validity

**Internal validity:**
- Localhost is not a real distributed network
- OS scheduling can introduce variance
- Python/runtime effects can introduce noise

**External validity:**
- Single model, single protocol, CPU-only, batch size 1

**Construct validity:**
- The benchmark measures the full cost of introducing a service boundary, not the marginal cost of an additional hop

**Conclusion validity:**
- Strong repetition reduces risk of weak conclusions
- Multiple comparisons should still be acknowledged

---

## 8. Implementation Roadmap

### Phase 0: Project Structure

```
opus/
├── proto/
│   └── inference.proto
├── src/
│   ├── models/
│   │   ├── resnet_splits.py
│   │   └── validation.py
│   ├── services/
│   │   ├── service_b.py
│   │   └── service_b_runner.py
│   ├── benchmark/
│   │   ├── config.py
│   │   ├── timer.py
│   │   ├── runner.py
│   │   ├── warmup.py
│   │   └── logging.py
│   ├── analysis/
│   │   ├── statistics.py
│   │   └── plots.py
│   └── client/
│       ├── monolithic.py
│       └── split_client.py
├── configs/
│   └── rq1_1.yaml
├── results/
├── requirements.txt
└── README.md
```

### Phase 1: Model Splitting Infrastructure

1. Define split points for the 4 coarse boundaries.
2. Validate functional equivalence.
3. Record intermediate tensor shapes and sizes.

### Phase 2: gRPC Communication Layer

1. Define proto schema.
2. Implement Service B.
3. Implement split client.
4. Validate end-to-end correctness for all 4 split points.

### Phase 3: Timing Instrumentation

Implement timing for:

- end-to-end latency
- Service A compute
- `boundary_crossing_interval_ms`
- Service B compute

Validate that intervals are sensible and non-negative.

### Phase 4: Benchmark Orchestrator

- Config loading
- Process management
- Warmup handling
- Measurement loop
- 5-round structure
- Randomized ordering
- Environment metadata capture

### Phase 5: Warmup Calibration

- Run calibration
- Determine stabilization point
- Set warmup count conservatively

### Phase 6: Main Experiment Execution

- Run R = 5, M = 200, plus warmup
- Spot-check raw data after rounds
- Do not change parameters after seeing results unless a full rerun is justified and documented

### Phase 7: Analysis and Reporting

- Compute summary statistics
- Compute overhead relative to monolith
- Apply carry-forward rule
- Generate plots
- Generate thesis-facing report

### Implementation Constraints

- Minimal dependencies
- Deterministic config-driven behavior
- No premature optimization
- Incremental validation before scaling up

---

## Appendix A: Literature Grounding

### Distributed / Partitioned DNN Inference

**Kang et al. (2017), "Neurosurgeon":** Relevant because it shows that split-point choice depends on both compute cost and intermediate data transfer.

**Jeong et al. (2018), "IONN":** Relevant because it highlights that communication-related costs are not always cleanly linear and may include framework effects.

**Hu & Krishnamachari (2020), "DADS":** Relevant because it emphasizes the need to distinguish compute balance and transfer burden when evaluating split points.

### Systems Benchmarking Methodology

**Jain (1991), "The Art of Computer Systems Performance Analysis":** Relevant for controlled-factor design, warmup handling, repeated trials, and statistical reporting.

**Lilja (2000), "Measuring Computer Performance":** Relevant for measurement overhead awareness, distribution-aware statistics, and careful interpretation.

**van der Kouwe et al. (2018), "Benchmarking Crimes":** Relevant for avoiding common experimental failures such as poor warmup, insufficient repetitions, or unfair comparisons.

### Fair Comparison Principles

**Mytkowicz et al. (2009):** Relevant for understanding how environmental factors can bias measurement.

**Curtsinger & Berger (2013), "STABILIZER":** Relevant for highlighting how repeated measurements and robust comparison procedures matter for fair evaluation.

---

## Appendix B: Design Decision Record

| Decision | Choice | Alternative | Rationale |
|---|---|---|---|
| Main split scope | 4 coarse architectural boundaries | 1 split or exhaustive layer sweep | Supports thesis-facing selection without overbroad characterization |
| Stem split | Excluded from main sweep | Included in main sweep | Better thesis story and less trivial domination of results |
| Monolithic baseline | Direct function call | gRPC-wrapped monolith | Measures total boundary introduction cost |
| Communication-adjacent metric | `boundary_crossing_interval_ms` | "communication overhead" | More honest and less ambiguous |
| Primary ranking metric | Mean latency | Median latency | Better aligned with carry-forward selection logic |
| Secondary robustness metrics | Median, p95, std | Mean only | Preserves stability and variability interpretation |
| Compute device | CPU | GPU | Avoids GPU confounds |
| Locality | Localhost | Networked deployment | Isolates boundary effects |
| Batch size | 1 | Larger batches | Measures per-request cost cleanly |
| Repetition structure | 5 rounds × 200 iterations | Smaller benchmark | Stronger statistical discipline |
| Ordering | Randomized per round | Fixed order | Reduces temporal confounds |

---

> **Summary of main changes from prior version:**
> - RQ1.1 is now a **selection study**
> - The main sweep is now **4 coarse boundaries**, not 5
> - "communication overhead" is replaced by **`boundary_crossing_interval_ms`**
> - **Mean** latency is now primary for selection
> - The **strong 5 × 200 repetition structure** stays
