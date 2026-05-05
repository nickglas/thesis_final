# Thesis Data Collection Methods

This file describes how data is gathered for the thesis research questions, what is
measured in each stage, why that data is collected, which technologies and platforms are
used, and which metrics are reported.

This document is a working methods inventory for the repository. The thesis chapters in
`thesis/chapters/experiments/*.tex` remain the narrative source of truth. Where the repo
contains multiple configs or runner variants, this file prioritizes the thesis-facing
method described in the chapter text.

## 1. Overall Methodology

The thesis uses a staged experimental pipeline:

- RQ1.1 and RQ1.2 identify suitable ResNet-18 split boundaries under tightly controlled
  local execution.
- RQ1.3 explains those local results using activation-transfer size and internal compute
  distribution.
- RQ1.4 moves the selected decomposition family into local in-cluster Kubernetes.
- RQ1.5 validates whether the same chain family transfers to Azure Kubernetes Service
  (AKS).
- RQ2.1 adds communication-level hardening with service identity, mTLS, and
  authorization policy.
- RQ2.2 adds VM-level confidential execution on top of the RQ2.1 communication-security
  baseline.
- RQ2.3 is a synthesis stage that compares the hardening levels rather than collecting a
  new benchmark stream.

The common design principle is: change one layer of the system at a time, preserve the
model and benchmark contract, and compare against the nearest relevant baseline.

## 2. Shared Benchmark Contract

These settings are reused across most thesis-facing stages unless a section explicitly
states otherwise.

### Fixed subject under test

- Model: ResNet-18.
- Weights: pretrained.
- Device: CPU.
- Precision: FP32.
- Input shape: `1 x 3 x 224 x 224`.
- Communication protocol for split or chained deployments: gRPC.
- gRPC port: `50051`.
- Maximum gRPC message size: `16777216` bytes (16 MiB).

### Shared timing protocol

- Warmup iterations per condition execution: 50.
- Measured iterations per condition execution: 200.
- Cooldown between conditions: 5 seconds.
- Random seed: 42.
- Warmup calibration window: 10 iterations.
- Warmup calibration coefficient-of-variation threshold: 0.02.
- Thesis-facing stages usually aggregate 5 rounds or 5 paired passes, yielding 1,000
  measured iterations per condition.

### Shared functional validation

- Local segment validation is run before timing.
- Live gRPC chain validation is used when a split or Kubernetes chain is deployed.
- Parity tolerance: `atol = 1e-5`.
- Validation inputs: 5.
- Thesis-facing frozen runs report `max_abs_diff = 0.0` for the validated conditions.

### Shared CPU-stabilization philosophy

- PyTorch intra-op threads requested at 1.
- PyTorch inter-op threads requested at 1.
- OpenMP, MKL, and OpenBLAS thread counts requested at 1.
- CPU affinity requested to one physical core with SMT avoided.
- Higher process priority requested with `nice = -5` where the environment allows it.
- CPU governor `performance` and turbo-disable requests are used where the host allows
  them.
- Managed Kubernetes and AKS stages document where these controls cannot be fully
  enforced because of container or cloud restrictions.

### Shared artifact philosophy

- Thesis-facing runs are exported and frozen as artifact sets.
- Rolling or paired executions are merged into one results artifact per stage.
- Analysis is performed from the exported artifact set, not from ad hoc terminal output.

## 3. Metric Glossary

- End-to-end latency: wall-clock time for one full inference request.
- Mean latency: arithmetic mean of measured per-iteration latencies.
- Median latency: 50th percentile latency.
- Std / standard deviation: dispersion of measured per-iteration latencies.
- p95 latency: 95th percentile latency.
- Overhead vs baseline: latency increase relative to the nearest baseline condition.
- Boundary-crossing interval: split-benchmark interval associated with crossing the
  service boundary; in practice this reflects a combination of hand-off cost and the
  work executed on the remote side after the boundary.
- Activation-transfer burden: tensor size at the split boundary or cumulative tensor size
  across all boundaries in a chain. This is derived from model structure, not measured by
  a separate network profiler.
- Inferred non-compute/platform cost: derived residual used in the Kubernetes, AKS, and
  mTLS analyses; this is an analytical estimate, not a directly timed phase.
- Cross-round consistency / round CV: stability of condition means across rounds or
  passes.
- Cohen's d: effect size computed from pooled per-iteration data.
- Mann-Whitney p-value: supplementary significance test; interpreted cautiously because
  `N = 1000` per condition makes even small differences statistically significant.
- Sequential throughput: derived as requests per second from mean latency.
- Resource / operational overhead: sidecar CPU, total pod CPU delta, sidecar memory,
  total pod memory delta, schedule-to-ready delta, and added mesh/security objects.

## 4. Per-RQ Methods

### RQ1.1 Coarse Architectural Boundary Selection

- Goal: screen coarse ResNet-18 stage boundaries and identify which two-service
  decompositions are credible enough to carry forward.
- Why this data is collected: the thesis first needs a defensible split region before it
  moves into Kubernetes, Azure, or security hardening.
- Repo tooling: shared local benchmark runner `run_experiment.py` with the thesis-facing
  config `configs/rq1/1.1/rq1_1_fully_controlled.yaml`. Note that the repo also contains
  Azure-oriented RQ1.1 tooling, but the thesis chapter describes the local fully
  controlled benchmark as the primary method.
- Environment and technologies: local CPU-only inference; PyTorch; pretrained ResNet-18;
  gRPC over localhost; split conditions use a separate Service B OS process on
  `127.0.0.1:50051`.
- Measurement volume: 5 rounds x 200 measured iterations = 1,000 measured iterations per
  condition.
- Independent variable / conditions: `monolithic`; `split_after_layer1`;
  `split_after_layer2`; `split_after_layer3`; `split_after_layer4`.
- Architectural transfer points: after `layer1` about 784 KiB; after `layer2` about 392
  KiB; after `layer3` about 196 KiB; after `layer4` about 98 KiB.
- Data gathered: per-iteration end-to-end latency for each condition; parity results;
  boundary-crossing interval; architecturally derived activation size; round-level
  stability.
- Metrics reported: mean latency; median latency; standard deviation; overhead vs the
  monolithic baseline; boundary-crossing interval; round CV.
- Method rules applied: near-best window 5 percent; compute-degeneracy threshold 10
  percent for the smaller compute side when deciding what can be carried forward.
- Output of the stage: main coarse carry-forward candidate plus one reference candidate
  for later refinement.

### RQ1.2 Fine-Grained Refinement

- Goal: test whether one meaningful block-level split inside the late-stage carry-forward
  region changes the conclusion from RQ1.1.
- Why this data is collected: coarse screening can hide within-stage structure, so the
  thesis needs one tighter comparison before moving to explanation and deployment.
- Repo tooling: shared local benchmark runner plus
  `configs/rq1/1.2/rq1_2_fully_controlled.yaml`.
- Environment and technologies: same local fully controlled CPU-only setup as RQ1.1;
  PyTorch; gRPC over localhost; identical validation and stabilisation philosophy.
- Measurement volume: 5 rounds x 200 measured iterations = 1,000 measured iterations per
  condition.
- Independent variable / conditions: `monolithic`; `split_after_layer2`;
  `split_after_layer3_block0`; `split_after_layer3`.
- Special comparison built into the design: `split_after_layer3_block0` and
  `split_after_layer3` both transfer about 196 KiB, so the design holds activation size
  constant while changing compute placement.
- Data gathered: per-iteration end-to-end latency; parity results; boundary-crossing
  interval; activation-transfer burden; round-level stability.
- Metrics reported: mean latency; median latency; standard deviation; overhead vs
  monolithic; activation size in KiB; boundary-crossing interval; round CV.
- Method logic: this is a targeted refinement, not a new blind search. The coarse
  RQ1.1 anchors (`layer2` and `layer3`) remain in the condition set and one new internal
  boundary is inserted between them.
- Output of the stage: refined main candidate plus a reference candidate, together with
  the explanatory observation that equal activation size does not guarantee equal
  latency.

### RQ1.3 Explanatory Synthesis: Activation-Transfer Size and Compute Distribution

- Goal: explain the RQ1.1 and RQ1.2 latency patterns using activation-transfer burden and
  compute distribution.
- Why this data is collected: the thesis needs an explanatory account of why some
  boundaries perform differently, not only a ranking of benchmark outcomes.
- Stage type: hybrid analytical stage. It is not a new split benchmark.
- Data sources combined:
  - RQ1.1 split-benchmark summaries.
  - RQ1.2 split-benchmark summaries.
  - A separate internal timing experiment on monolithic ResNet-18.
- Repo tooling: `run_internal_timing.py` with `configs/internal_timing/timing_full.yaml`;
  internal timing is explicitly separate from the split benchmark entrypoint.
- Environment and technologies: instrumented monolithic ResNet-18 forward path; CPU-only;
  single-threaded stabilised execution; PyTorch.
- Internal timing protocol: 10 rounds; 50 warmup iterations; 200 measured iterations;
  same seed philosophy as the main benchmark line.
- Additional validation: equivalence against the uninstrumented model;
  `max_abs_diff = 0.0`; measured instrumentation overhead about 0.645 ms or 0.88 percent
  of model total.
- Data gathered: per-stage timings; per-block timings; selected operation-level timings;
  stage shares of model total; heavy internal compute units; convolution and batch-norm
  share summaries.
- Metrics reported: model total mean; stage means; percent of model total; `layer3.1`
  block timing; operation rankings; convolution share; batch-normalisation share.
- Output of the stage: an explanatory synthesis showing that coarse trends are mostly
  driven by activation-transfer burden, while refined equal-activation comparisons expose
  compute placement as an independent factor.

### RQ1.4 Multi-Microservice Kubernetes Inference Chain

- Goal: measure how latency changes when the model is decomposed into a predefined family
  of synchronous coarse-stage chains inside local Kubernetes.
- Why this data is collected: after local split selection, the thesis needs to know what
  happens when service boundaries become real Kubernetes services with in-cluster RPC.
- Frozen thesis-facing run: exported controlled local Kubernetes run from 2026-04-21.
- Repo tooling: `scripts/run_rq14_fully_controlled.sh`; `run_k8s_experiment.py`;
  `k8s/generate_manifests.py`; `configs/rq1/1.4/rq1_4_fully_controlled.yaml`.
- Environment and technologies: local Ubuntu/Linux; single-node `kind` cluster;
  namespace `rq14`; Kubernetes services and pods; gRPC in cluster; PyTorch; ResNet-18.
- Node placement: all service pods scheduled on the same node,
  `thesis-rq14-control-plane`.
- Condition family:
  - `monolithic_k8s_1svc`.
  - `chain_2svc` with split after `layer2`, cumulative transferred activation 980 KiB.
  - `chain_3svc` with splits after `layer1` and `layer3`, cumulative transferred
    activation 1568 KiB.
  - `chain_4svc` with splits after `layer1`, `layer2`, `layer3`, cumulative transferred
    activation 1960 KiB.
  - `chain_5svc` with splits after `layer1`, `layer2`, `layer3`, `layer4`, cumulative
    transferred activation 2058 KiB.
- Resource profile: service pods 1 CPU request / 1 CPU limit and 512 MiB memory request /
  512 MiB limit; client pod 1 CPU request / 1 CPU limit and 1 GiB memory request /
  1 GiB limit.
- Controls and validation: requested one-thread execution; requested one-core affinity;
  requested `nice -5`; governor and turbo controls requested but blocked by read-only
  sysfs inside the container; ASLR detected but not modified; local segment validation and
  live gRPC chain validation both passed with `max_abs_diff = 0.0`.
- Data gathered: end-to-end latency across the 1-to-5 service family; parity outputs;
  cumulative transfer burden; round-level consistency.
- Metrics reported: mean; median; standard deviation; p95; overhead vs Kubernetes
  monolithic baseline; inferred non-compute/platform cost; Cohen's d; Mann-Whitney p;
  round mean range; round CV.
- Statistical interpretation rule: p-values are supplementary only; effect size,
  cross-round stability, and parity are the primary validity signals.
- Output of the stage: the thesis-facing local Kubernetes chain cost curve; no carry
  forward is performed because the condition family is predefined.

### RQ1.5 Azure Kubernetes Service Transfer Validation

- Goal: test whether the RQ1.4 chain family preserves its ordering and overhead pattern
  when moved from local `kind` Kubernetes to AKS.
- Why this data is collected: the thesis needs to separate architecture-dependent effects
  from environment-specific local-cluster behavior.
- Frozen thesis-facing run: exported controlled AKS transfer-validation run from
  2026-04-22.
- Repo tooling: `scripts/run_rq15_fully_controlled.py`; `scripts/run_rq15_fully_controlled.sh`;
  `configs/rq1/1.5/rq1_5_full.yaml`.
- Environment and technologies: AKS; Linux Azure runtime; single-node cluster;
  `Standard_D8s_v3`; region `swedencentral`; `kubenet` networking; namespace `rq15`;
  gRPC in cluster; PyTorch; ResNet-18.
- Colocation rule: benchmark client and all service pods are forced onto the same AKS
  node `aks-rq15pool-24384142-vmss000000`.
- Condition family: same five conditions as RQ1.4, with the same chain topology and the
  same cumulative transfer burden values.
- Resource profile: service pods 1 CPU request / 1 CPU limit and 1 GiB memory request /
  1 GiB limit; client pod 500m request / 500m limit and 1 GiB memory request /
  1 GiB limit; service pods run with Guaranteed QoS.
- Controls and validation: one-thread requests applied; one-core affinity applied;
  requested `nice -5` was denied by privileges so the benchmark ran at `nice = 0`;
  governor and turbo controls unavailable on managed nodes; parity validation passed with
  `max_abs_diff = 0.0`.
- Data gathered: per-iteration end-to-end latency in AKS; transfer comparison against the
  frozen RQ1.4 local Kubernetes results; round-level stability; parity results.
- Metrics reported: mean; median; standard deviation; p95; overhead vs the AKS monolithic
  baseline; inferred non-compute/platform cost; local-vs-AKS transfer table; round CV;
  supplementary effect sizes and Mann-Whitney tests.
- Interpretation rule: preserved ordering and within-environment overhead trends are the
  main transfer signal; exact millisecond equality between local Kubernetes and AKS is not
  expected.
- Output of the stage: transfer-validation evidence that the chain family ordering is
  preserved under managed cloud execution.

### RQ2.1 Service Identity And Mutual TLS Hardening

- Goal: measure the latency, resource, and operational cost of adding service identity,
  managed-Istio mTLS, and authorization policy to the selected AKS inference path.
- Why this data is collected: once the Azure chain is selected, the thesis needs to know
  what communication-security hardening costs in the real deployment path.
- Repo tooling: `scripts/run_rq21_paired_benchmark.py`; supporting runner
  `scripts/run_rq21_fully_controlled.py`; configs in `configs/rq2/2.1/`, including
  `rq2_1_chain2_plain.yaml`, `rq2_1_chain2_mtls.yaml`, and the matching chain-5 stress
  variants.
- Environment and technologies: AKS cluster `thesis-rq15`; isolated benchmark and system
  node pools; benchmark pool `rq15pool`; managed AKS Istio add-on `asm-1-29`; service
  accounts; peer-authentication objects; authorization-policy objects; gRPC; ResNet-18;
  PyTorch.
- Main topology: `chain_2svc` with split after `layer2`.
- Stress topology: `chain_5svc` with splits after `layer1`, `layer2`, `layer3`, and
  `layer4`.
- Paired execution design: each paired pass executes both the plain and mTLS conditions;
  order is alternated from a seeded plan; 5 paired passes produce 1,000 measured
  iterations per condition.
- Artifact sets named in the chapter:
  - Main artifact: `frozen_rq2_1_paired_20260429_102941_chain2`.
  - Stress artifact: `frozen_rq2_1_paired_20260429_112307_chain5`.
- Resource profile: inference services 1 CPU / 1 GiB; benchmark client 100m CPU request,
  1 CPU limit, 1 GiB memory; sidecars 100m CPU request, 500m CPU limit, 128 MiB memory
  request, 512 MiB memory limit.
- Placement and isolation rules: strict same-node placement on the tainted benchmark node
  pool; separate system pool for control-plane/system workloads; mesh control-plane pods
  not colocated on the benchmark node in the paired runs.
- Security validation methods: static manifest validation; runtime policy validation;
  full-chain positive probe; direct non-mesh denial probe against protected downstream
  segments.
- Data gathered: end-to-end latency for plain vs mTLS; pass-level matched deltas; resource
  sampling; readiness timing; object-count overhead; validation outcomes.
- Metrics reported:
  - Mean, median, and p95 latency.
  - Inferred non-compute/platform component.
  - Mean delta, percent delta, pass min-max delta, pass-delta standard deviation.
  - Sidecar CPU, total pod CPU delta, sidecar memory, total pod memory delta.
  - Schedule-to-ready delta.
  - Count of additional mesh/security objects.
- Output of the stage: measured bounded overhead for `chain_2svc` plus a deeper `chain_5svc`
  stress comparison showing how mTLS cost grows with boundary count.

### RQ2.2 Confidential VM Execution Hardening

- Goal: measure the additional cost of placing part or all of the already mTLS-protected
  AKS inference chain on AMD SEV-SNP confidential VM infrastructure.
- Why this data is collected: mTLS protects the communication path, but not the runtime
  memory boundary of the service. This stage measures the incremental cost of VM-level
  confidential execution.
- Repo tooling: `scripts/run_rq22_confidential.py`; post-run analysis via
  `scripts/analyze_rq22_confidential.py`; thesis-facing config
  `configs/rq2/2.2/rq2_2_confidential_amd_sev_snp.yaml`.
- Environment and technologies: AKS; managed-Istio mTLS/AuthZ inherited from RQ2.1;
  AMD SEV-SNP confidential nodes; standard comparator nodes; ResNet-18; PyTorch; gRPC;
  Azure confidential node pools.
- Region and VM families: region `westeurope`; standard comparator
  `Standard_D8as_v5`; confidential comparator `Standard_DC8as_v5`.
- Base topology: `chain_2svc` with split after `layer2`.
- Experimental design:
  - Selective TEE run: service1 stays on standard nodes; service2 moves to confidential
    nodes. This isolates the cost of protecting the downstream service.
  - Full TEE run: both services move to confidential nodes. This measures the cost of
    protecting the full two-service chain.
- Paired execution volume: 5 paired passes per artifact; 200 measured iterations per
  condition execution; 1,000 measured iterations per condition after merging.
- Artifact sets named in the chapter:
  - Selective TEE artifact: `frozen_rq2_2_confidential_20260502_200835_1_tee`.
  - Full TEE artifact: `frozen_rq2_2_confidential_20260503_085320_full_tee`.
- Validation contract: the RQ2.1 communication-security policy remains fixed; new paired
  standard baselines are collected instead of reusing older RQ2.1 data.
- Data gathered: paired standard vs confidential latency data for the service2-only and
  full-chain confidential configurations.
- Metrics reported: mean latency; median latency; p95 latency; absolute and percentage
  deltas; sequential throughput derived from mean latency; throughput delta.
- Protection-boundary interpretation built into the method: this is VM-level confidential
  execution, not application-level enclave isolation; the guest OS, runtime, process, and
  local sidecar remain inside the same trust boundary.
- Output of the stage: direct comparison between selective confidential execution and full
  confidential execution, with cost expressed as incremental overhead on top of the RQ2.1
  communication-security baseline.

### RQ2.3 Security-Hardening Trade-off Synthesis

- Goal: decide which evaluated hardening level provides the best trade-off between
  performance cost, operational complexity, and protection scope.
- Why this data is collected: the thesis needs a final decision layer that compares the
  plain AKS path, the communication-secured path, and the confidential-execution path.
- Stage type: synthesis only. No new raw benchmark stream is collected.
- Data sources combined:
  - Plain AKS baseline from RQ1.5.
  - mTLS/AuthZ results from RQ2.1.
  - Selective and full confidential-execution results from RQ2.2.
- Data gathered: no new per-iteration timing data. The stage reuses previously collected
  means, deltas, resource/operational overheads, and protection-scope descriptions.
- Metrics compared: measured cost; scope of protection; operational complexity; chain-depth
  sensitivity; confidential-boundary coverage.
- Output of the stage: a trade-off matrix that says when plain AKS, mTLS/AuthZ,
  mTLS/AuthZ plus selective TEE, or mTLS/AuthZ plus full two-service TEE is the most
  appropriate configuration.

## 5. Supporting Repo Entry Points By Stage

- Local split benchmarks: `run_experiment.py` plus the RQ1 local fully controlled configs.
- Internal compute-distribution profiling: `run_internal_timing.py` plus
  `configs/internal_timing/timing_full.yaml`.
- Local Kubernetes chain benchmark: `scripts/run_rq14_fully_controlled.sh`.
- AKS transfer-validation benchmark: `scripts/run_rq15_fully_controlled.py` and
  `scripts/run_rq15_fully_controlled.sh`.
- Paired AKS security benchmark: `scripts/run_rq21_paired_benchmark.py`.
- Confidential AKS benchmark and analysis: `scripts/run_rq22_confidential.py` and
  `scripts/analyze_rq22_confidential.py`.

## 6. Practical Notes

- The thesis uses frozen artifact sets as the reporting basis whenever possible.
- The repo contains older, exploratory, smoke-test, and alternate-platform configs in
  addition to the thesis-facing ones. This file documents the thesis-facing methods, not
  every historical run path.
- Where a stage is described as a synthesis stage, the correct interpretation is that the
  data comes from previous benchmark stages and is recombined analytically rather than
  recollected.
