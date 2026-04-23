# Uniform Experiment Runs

Run these commands from the repository root.

## What is directly comparable

Use only these thesis-facing configs for direct comparison:

- `configs/rq1/1.1/rq1_1_fully_controlled.yaml`
- `configs/rq1/1.2/rq1_2_fully_controlled.yaml`
- `configs/rq1/1.4/rq1_4_fully_controlled.yaml`
- `configs/rq1/1.5/rq1_5_full.yaml`

`python scripts/check_uniform_configs.py` confirms that these four configs share the same core measurement contract:

- ResNet-18 on CPU, FP32, input shape `[1, 3, 224, 224]`
- `5` rounds, `50` warmup iterations, `200` measured iterations, `5` second cooldown, seed `42`
- warmup calibration window `10`, CV threshold `0.02`
- parity validation with `5` inputs at `1e-5`
- single-threaded CPU stabilisation across PyTorch, OMP, MKL, and OpenBLAS

## What is not directly comparable

Do not mix these into the thesis-facing comparison set:

- `*_experimental.yaml`
- `*_threaded.yaml`
- `*_smoke*.yaml`
- `configs/internal_timing/timing_full.yaml`

Internal timing is exploratory, not part of the thesis-facing split benchmark family.

## Important RQ1.5 caveat

RQ1.5 is comparable to RQ1.4 by design, but not identical at the host-control level. The current AKS full config intentionally differs in these ways:

- governor and turbo controls are disabled on AKS managed nodes
- service pod memory is `1Gi` instead of `512Mi`
- the benchmark client pod is `500m` CPU instead of `1` full CPU
- image pull policy is `Always` and the image must be pinned by digest

## Check first

```bash
python scripts/check_uniform_configs.py
```

## Canonical start commands

### RQ1.1 fully controlled

```bash
python run_experiment.py --config configs/rq1/1.1/rq1_1_fully_controlled.yaml --run-analysis
```

### RQ1.2 fully controlled

```bash
python run_experiment.py --config configs/rq1/1.2/rq1_2_fully_controlled.yaml --run-analysis
```

### RQ1.4 fully controlled

Run this from WSL or another bash shell:

```bash
bash scripts/run_rq14_fully_controlled.sh
```

### RQ1.5 fully controlled on an existing AKS cluster

```bash
python scripts/run_rq15_fully_controlled.py
```

### RQ1.5 fully controlled with fresh AKS provisioning and a fresh pinned image

```bash
python scripts/run_rq15_fully_controlled.py --provision --push --build --acr-name <your-acr-name>
```

## Optional exploratory run

This is useful for interpretation, but it is not part of the directly comparable thesis run set:

```bash
python run_internal_timing.py --config configs/internal_timing/timing_full.yaml --run-analysis
```
