# RQ1.1 — Coarse-Boundary Screening for ResNet-18

> **RQ1.1:** Which coarse architectural stage boundaries provide the most
> suitable two-part microservice decompositions of ResNet-18 under controlled
> local execution, and how do their latency and boundary-crossing costs compare
> to monolithic inference?

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Compile the gRPC proto stubs

```bash
python build_proto.py
```

This generates `proto/inference_pb2.py` and `proto/inference_pb2_grpc.py`.

### 3. Validate functional equivalence

```bash
python -m src.models.validation
```

Verifies that all four split configurations produce numerically equivalent
outputs to the monolithic ResNet-18.

### 4. Run the experiment

```bash
python run_experiment.py --config configs/rq1_1.yaml
```

This executes the full benchmark:

- 5 conditions (1 monolithic + 4 split points)
- 5 rounds × 200 measured iterations per condition per round
- 50 warmup iterations before each condition (discarded)
- Randomised condition order per round
- 5-second cooldown between conditions

Raw per-iteration data is saved to `results/rq1_1_<timestamp>/raw_iterations.csv`.

**Estimated wall-clock time:** roughly 30–90 minutes depending on hardware
(5000 measured iterations total, plus warmup and cooldown).

### 5. Run the analysis

```bash
python run_analysis.py results/rq1_1_<timestamp>
```

If the source results directory is read-only, the analysis script now writes
derived artifacts to a sibling directory named `results/rq1_1_<timestamp>_analysis`.
You can also override that explicitly:

```bash
python run_analysis.py results/rq1_1_<timestamp> --output-dir results/my_analysis_output
```

This produces:

- `condition_summaries.csv` — per-condition statistics
- `round_summaries.csv` — per-(round, condition) statistics
- `cross_condition.csv` — overhead relative to monolithic
- `effect_sizes.csv` — Cohen's d and Mann-Whitney U
- `carry_forward.json` — carry-forward selection result
- `plots/` — box plot, violin plot, overhead scatter, stationarity traces
- `report.md` — Markdown summary report

## Project Structure

```
opus/
├── proto/
│   └── inference.proto             # gRPC service definition
├── src/
│   ├── models/
│   │   ├── resnet_splits.py        # PartA / PartB model splitting
│   │   └── validation.py           # Functional equivalence check
│   ├── services/
│   │   ├── service_b.py            # gRPC server (runs in separate process)
│   │   └── service_b_runner.py     # CLI launcher for Service B
│   ├── benchmark/
│   │   ├── config.py               # YAML config loading
│   │   ├── timer.py                # time.perf_counter() utilities
│   │   ├── runner.py               # Main benchmark orchestrator
│   │   ├── warmup.py               # Warmup iteration runner
│   │   └── logging.py              # Artifact persistence
│   ├── analysis/
│   │   ├── statistics.py           # Summary stats, effect sizes, carry-forward
│   │   └── plots.py                # Matplotlib visualizations
│   └── client/
│       ├── monolithic.py           # Direct model(input) with timing
│       └── split_client.py         # PartA + gRPC call with timing
├── configs/
│   └── rq1_1.yaml                  # Experiment configuration
├── results/                        # Output directory (auto-created)
├── build_proto.py                  # Proto compilation script
├── run_experiment.py               # Main experiment entry point
├── run_analysis.py                 # Post-experiment analysis
├── requirements.txt
└── README.md
```

## Conditions

| Condition              | Description                     | Intermediate Tensor | Activation Size |
| ---------------------- | ------------------------------- | ------------------- | --------------- |
| C0: Monolithic         | Full ResNet-18, direct call     | —                   | —               |
| C1: Split after layer1 | A: stem+layer1, B: layer2–fc    | 64×56×56            | ~784 KB         |
| C2: Split after layer2 | A: stem+layer1–2, B: layer3–fc  | 128×28×28           | ~392 KB         |
| C3: Split after layer3 | A: stem+layer1–3, B: layer4+fc  | 256×14×14           | ~196 KB         |
| C4: Split after layer4 | A: stem+layer1–4, B: avgpool+fc | 512×7×7             | ~98 KB          |

## Measurement Contract

- **Primary metric:** Mean end-to-end inference latency (ms)
- **Timing instrument:** `time.perf_counter()`
- **Monolithic boundary:** before `model(input)` → after return
- **Split boundary:** before `part_A(input)` → after response deserialization

## Carry-Forward Rule

1. Minimise `end_to_end_latency_ms_mean` among split conditions
2. Define near-best window (default 10% of best split mean)
3. Filter compute-degenerate candidates (default <5% share for one side)
4. Tie-break on lower `activation_bytes_mean`

## Configuration

All experiment parameters are in `configs/rq1_1.yaml`.
The benchmark is fully config-driven — no parameters are hard-coded.
