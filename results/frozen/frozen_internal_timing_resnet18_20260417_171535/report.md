# Internal Timing Report — ResNet-18 Compute Distribution

## 1. Setup

### 1.1 Configuration

```yaml
# Internal Timing Mode — Full Operation-Level Profiling
# Strict single-thread/single-core CPU stabilisation.
# This is the primary exploratory profiling config.
#
# NOTE: This is an exploratory mode, NOT thesis-facing split benchmarking.
# It measures local compute distribution within a single-process forward pass.

experiment:
  name: "internal_timing_resnet18"
  description: "Full operation-level compute distribution profiling of ResNet-18"

model:
  name: "resnet18"
  pretrained: true
  device: "cpu"
  input_shape: [1, 3, 224, 224]
  precision: "fp32"

timing:
  level: "full" # stage | block | operation | full
  include_stem_ops: true
  include_timing_gaps: true
  measure_overhead: true

benchmark:
  rounds: 10
  warmup_iterations: 50
  measured_iterations: 200
  seed: 42

validation:
  num_inputs: 5
  atol: 1.0e-6

warmup_calibration:
  window: 10
  cv_threshold: 0.02

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
    requested_mode: "performance"
  turbo:
    disable_turbo: false
```

### 1.2 Environment

- **Platform:** Linux-6.17.0-20-generic-x86_64-with-glibc2.39
- **Processor:** x86_64
- **Python:** 3.12.3
- **PyTorch:** 2.11.0+cu130
- **CPU count:** 16
- **Git commit:** 0df2ac36e4b8b803cfd8e75952cabcbe63355975

## 2. Validation

### 2.1 Functional Equivalence

- **Passed:** True
- **Inputs tested:** 5
- **Max abs diff:** 0.00e+00
- **Tolerance:** 1.00e-06

### 2.2 Warmup Calibration

- **Total warmup iterations:** 50
- **Stabilised:** True
- **Stabilised at iteration:** 11
- **Final window CV:** 0.0014

### 2.3 Instrumentation Overhead

- **Plain forward mean:** 72.9672 ms
- **Instrumented forward mean:** 73.6125 ms
- **Overhead:** 0.6453 ms (0.88%)
- **Samples:** 50
- **Method:** interleaved_outer_timing
- **Overhead warmup:** 20 iterations per model

## 3. Results

### 3.1 Stage-Level Summary (L1)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4 | 22.6391 | 22.6270 | 0.1192 | 22.7250 | 22.5227 | 27.3915 | 30.70% |
| layer3 | 13.6888 | 13.6838 | 0.0579 | 13.7697 | 13.5422 | 14.4074 | 18.56% |
| layer1 | 13.0706 | 13.0667 | 0.0656 | 13.1661 | 12.6952 | 13.6194 | 17.72% |
| stem | 12.0278 | 12.0131 | 0.1333 | 12.0820 | 11.9389 | 14.3282 | 16.31% |
| layer2 | 11.9682 | 11.9490 | 0.0938 | 12.1436 | 11.7805 | 12.7032 | 16.23% |
| fc | 0.2321 | 0.2295 | 0.0080 | 0.2475 | 0.2188 | 0.3118 | 0.31% |
| avgpool | 0.0923 | 0.0901 | 0.0065 | 0.1057 | 0.0863 | 0.1763 | 0.13% |

### 3.2 Block-Level Summary (L2)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1 | 12.3001 | 12.2919 | 0.0387 | 12.3636 | 12.2316 | 12.8258 | 16.68% |
| layer4.0 | 10.3065 | 10.2970 | 0.1103 | 10.3661 | 10.2353 | 14.9917 | 13.97% |
| layer3.1 | 7.3402 | 7.3348 | 0.0403 | 7.4067 | 7.2443 | 7.9013 | 9.95% |
| layer1.0 | 6.6056 | 6.7575 | 0.2101 | 6.8509 | 6.3494 | 7.1771 | 8.96% |
| layer1.1 | 6.4205 | 6.3532 | 0.1837 | 6.6458 | 6.1973 | 7.0037 | 8.71% |
| layer3.0 | 6.3161 | 6.3098 | 0.0358 | 6.3779 | 6.2457 | 6.6180 | 8.56% |
| layer2.1 | 6.1676 | 6.1579 | 0.0417 | 6.2409 | 6.0872 | 6.5471 | 8.36% |
| layer2.0 | 5.7652 | 5.7545 | 0.0637 | 5.8751 | 5.6398 | 6.4631 | 7.82% |

### 3.3 Operation-Level Summary (L3) — Grouped by Parent

#### stem

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 7.1885 | 7.1836 | 0.0328 | 7.2343 | 7.1328 | 7.6717 | 9.75% |
| stem.conv1 | 3.5978 | 3.5953 | 0.0404 | 3.6273 | 3.5594 | 4.2461 | 4.88% |
| stem.bn1 | 0.8890 | 0.8866 | 0.0511 | 0.8979 | 0.8419 | 1.7232 | 1.21% |
| stem.relu | 0.3338 | 0.3252 | 0.0263 | 0.3535 | 0.3129 | 0.7092 | 0.45% |

#### layer4.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1.conv1 | 6.0389 | 6.0346 | 0.0255 | 6.0801 | 6.0001 | 6.4540 | 8.19% |
| layer4.1.conv2 | 5.9715 | 5.9678 | 0.0208 | 6.0099 | 5.9261 | 6.1839 | 8.10% |
| layer4.1.bn1 | 0.0906 | 0.0891 | 0.0052 | 0.1032 | 0.0840 | 0.1648 | 0.12% |
| layer4.1.bn2 | 0.0880 | 0.0863 | 0.0052 | 0.1001 | 0.0814 | 0.1408 | 0.12% |
| layer4.1.relu1 | 0.0299 | 0.0295 | 0.0027 | 0.0315 | 0.0266 | 0.0568 | 0.04% |
| layer4.1.add | 0.0321 | 0.0315 | 0.0037 | 0.0338 | 0.0288 | 0.1273 | 0.04% |
| layer4.1.relu2 | 0.0228 | 0.0223 | 0.0027 | 0.0240 | 0.0203 | 0.0458 | 0.03% |

#### layer4.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.0.conv2 | 6.0287 | 6.0224 | 0.1065 | 6.0661 | 5.9854 | 10.6983 | 8.17% |
| layer4.0.conv1 | 3.4851 | 3.4813 | 0.0200 | 3.5205 | 3.4407 | 3.7079 | 4.73% |
| layer4.0.downsample | 0.4952 | 0.4956 | 0.0125 | 0.5147 | 0.4729 | 0.6491 | 0.67% |
| layer4.0.bn1 | 0.0909 | 0.0893 | 0.0053 | 0.1025 | 0.0840 | 0.1342 | 0.12% |
| layer4.0.bn2 | 0.0878 | 0.0864 | 0.0049 | 0.0985 | 0.0816 | 0.1407 | 0.12% |
| layer4.0.add | 0.0347 | 0.0349 | 0.0042 | 0.0374 | 0.0262 | 0.0920 | 0.05% |
| layer4.0.relu1 | 0.0299 | 0.0293 | 0.0030 | 0.0318 | 0.0271 | 0.0654 | 0.04% |
| layer4.0.relu2 | 0.0235 | 0.0229 | 0.0032 | 0.0245 | 0.0210 | 0.0553 | 0.03% |

#### layer3.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.0.conv2 | 3.6052 | 3.6004 | 0.0222 | 3.6447 | 3.5715 | 3.8526 | 4.89% |
| layer3.0.conv1 | 1.9223 | 1.9201 | 0.0136 | 1.9427 | 1.8895 | 2.0214 | 2.61% |
| layer3.0.downsample | 0.4853 | 0.4836 | 0.0151 | 0.5058 | 0.4420 | 0.6280 | 0.66% |
| layer3.0.bn2 | 0.0935 | 0.0921 | 0.0053 | 0.1043 | 0.0861 | 0.1549 | 0.13% |
| layer3.0.bn1 | 0.0836 | 0.0812 | 0.0074 | 0.0955 | 0.0721 | 0.1331 | 0.11% |
| layer3.0.add | 0.0387 | 0.0379 | 0.0041 | 0.0414 | 0.0343 | 0.0755 | 0.05% |
| layer3.0.relu1 | 0.0295 | 0.0289 | 0.0032 | 0.0322 | 0.0256 | 0.0859 | 0.04% |
| layer3.0.relu2 | 0.0267 | 0.0259 | 0.0037 | 0.0281 | 0.0237 | 0.0613 | 0.04% |

#### layer3.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.1.conv1 | 3.5759 | 3.5751 | 0.0219 | 3.6085 | 3.5191 | 3.8716 | 4.85% |
| layer3.1.conv2 | 3.4566 | 3.4529 | 0.0219 | 3.4952 | 3.4154 | 3.6690 | 4.69% |
| layer3.1.bn1 | 0.0900 | 0.0888 | 0.0048 | 0.1003 | 0.0830 | 0.1404 | 0.12% |
| layer3.1.bn2 | 0.0915 | 0.0900 | 0.0053 | 0.1027 | 0.0839 | 0.1393 | 0.12% |
| layer3.1.add | 0.0426 | 0.0420 | 0.0031 | 0.0475 | 0.0390 | 0.0728 | 0.06% |
| layer3.1.relu1 | 0.0320 | 0.0315 | 0.0035 | 0.0339 | 0.0289 | 0.1370 | 0.04% |
| layer3.1.relu2 | 0.0257 | 0.0249 | 0.0038 | 0.0324 | 0.0226 | 0.0962 | 0.03% |

#### layer1.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.0.conv1 | 3.1289 | 3.1264 | 0.0246 | 3.1582 | 3.0518 | 3.4846 | 4.24% |
| layer1.0.conv2 | 2.9116 | 2.9447 | 0.0616 | 2.9890 | 2.8313 | 3.1428 | 3.95% |
| layer1.0.bn1 | 0.1513 | 0.1783 | 0.0393 | 0.1997 | 0.1064 | 0.2801 | 0.21% |
| layer1.0.add | 0.1474 | 0.1700 | 0.0365 | 0.1985 | 0.1041 | 0.2574 | 0.20% |
| layer1.0.bn2 | 0.1428 | 0.1842 | 0.0535 | 0.2066 | 0.0830 | 0.3068 | 0.19% |
| layer1.0.relu1 | 0.0517 | 0.0527 | 0.0067 | 0.0587 | 0.0439 | 0.1517 | 0.07% |
| layer1.0.relu2 | 0.0450 | 0.0467 | 0.0079 | 0.0557 | 0.0353 | 0.1533 | 0.06% |

#### layer2.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.0.conv2 | 3.0228 | 3.0097 | 0.0295 | 3.0817 | 2.9915 | 3.1766 | 4.10% |
| layer2.0.conv1 | 1.8342 | 1.8280 | 0.0254 | 1.8701 | 1.7805 | 1.9547 | 2.49% |
| layer2.0.downsample | 0.5663 | 0.5575 | 0.0360 | 0.6271 | 0.5086 | 1.2688 | 0.77% |
| layer2.0.bn1 | 0.0913 | 0.0897 | 0.0058 | 0.1024 | 0.0829 | 0.1537 | 0.12% |
| layer2.0.add | 0.0842 | 0.0904 | 0.0173 | 0.1106 | 0.0457 | 0.1692 | 0.11% |
| layer2.0.bn2 | 0.0729 | 0.0692 | 0.0077 | 0.0869 | 0.0643 | 0.1187 | 0.10% |
| layer2.0.relu2 | 0.0337 | 0.0329 | 0.0052 | 0.0358 | 0.0291 | 0.1361 | 0.05% |
| layer2.0.relu1 | 0.0326 | 0.0320 | 0.0031 | 0.0351 | 0.0290 | 0.0815 | 0.04% |

#### layer2.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.1.conv1 | 2.9988 | 2.9989 | 0.0195 | 3.0289 | 2.9474 | 3.1595 | 4.07% |
| layer2.1.conv2 | 2.9145 | 2.9111 | 0.0144 | 2.9414 | 2.8855 | 3.1298 | 3.95% |
| layer2.1.bn1 | 0.0750 | 0.0712 | 0.0088 | 0.0911 | 0.0642 | 0.1432 | 0.10% |
| layer2.1.bn2 | 0.0625 | 0.0606 | 0.0051 | 0.0716 | 0.0566 | 0.1237 | 0.08% |
| layer2.1.add | 0.0454 | 0.0437 | 0.0047 | 0.0543 | 0.0395 | 0.0735 | 0.06% |
| layer2.1.relu1 | 0.0276 | 0.0267 | 0.0034 | 0.0314 | 0.0235 | 0.0761 | 0.04% |
| layer2.1.relu2 | 0.0239 | 0.0230 | 0.0036 | 0.0289 | 0.0210 | 0.0812 | 0.03% |

#### layer1.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.1.conv1 | 2.9532 | 2.9740 | 0.0427 | 3.0065 | 2.8695 | 3.0930 | 4.00% |
| layer1.1.conv2 | 2.9146 | 2.9155 | 0.0641 | 2.9916 | 2.8307 | 3.1628 | 3.95% |
| layer1.1.add | 0.1647 | 0.1335 | 0.0626 | 0.2439 | 0.0967 | 0.3002 | 0.22% |
| layer1.1.bn1 | 0.1440 | 0.1240 | 0.0412 | 0.1963 | 0.0911 | 0.3133 | 0.20% |
| layer1.1.bn2 | 0.1283 | 0.1056 | 0.0401 | 0.1808 | 0.0834 | 0.2314 | 0.17% |
| layer1.1.relu1 | 0.0471 | 0.0505 | 0.0084 | 0.0562 | 0.0351 | 0.1372 | 0.06% |
| layer1.1.relu2 | 0.0465 | 0.0500 | 0.0100 | 0.0559 | 0.0348 | 0.1394 | 0.06% |

### 3.4 Ranked Operations (Top 20 by Compute Share)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 7.1885 | 7.1836 | 0.0328 | 7.2343 | 7.1328 | 7.6717 | 9.75% |
| layer4.1.conv1 | 6.0389 | 6.0346 | 0.0255 | 6.0801 | 6.0001 | 6.4540 | 8.19% |
| layer4.0.conv2 | 6.0287 | 6.0224 | 0.1065 | 6.0661 | 5.9854 | 10.6983 | 8.17% |
| layer4.1.conv2 | 5.9715 | 5.9678 | 0.0208 | 6.0099 | 5.9261 | 6.1839 | 8.10% |
| layer3.0.conv2 | 3.6052 | 3.6004 | 0.0222 | 3.6447 | 3.5715 | 3.8526 | 4.89% |
| stem.conv1 | 3.5978 | 3.5953 | 0.0404 | 3.6273 | 3.5594 | 4.2461 | 4.88% |
| layer3.1.conv1 | 3.5759 | 3.5751 | 0.0219 | 3.6085 | 3.5191 | 3.8716 | 4.85% |
| layer4.0.conv1 | 3.4851 | 3.4813 | 0.0200 | 3.5205 | 3.4407 | 3.7079 | 4.73% |
| layer3.1.conv2 | 3.4566 | 3.4529 | 0.0219 | 3.4952 | 3.4154 | 3.6690 | 4.69% |
| layer1.0.conv1 | 3.1289 | 3.1264 | 0.0246 | 3.1582 | 3.0518 | 3.4846 | 4.24% |
| layer2.0.conv2 | 3.0228 | 3.0097 | 0.0295 | 3.0817 | 2.9915 | 3.1766 | 4.10% |
| layer2.1.conv1 | 2.9988 | 2.9989 | 0.0195 | 3.0289 | 2.9474 | 3.1595 | 4.07% |
| layer1.1.conv1 | 2.9532 | 2.9740 | 0.0427 | 3.0065 | 2.8695 | 3.0930 | 4.00% |
| layer1.0.conv2 | 2.9116 | 2.9447 | 0.0616 | 2.9890 | 2.8313 | 3.1428 | 3.95% |
| layer1.1.conv2 | 2.9146 | 2.9155 | 0.0641 | 2.9916 | 2.8307 | 3.1628 | 3.95% |
| layer2.1.conv2 | 2.9145 | 2.9111 | 0.0144 | 2.9414 | 2.8855 | 3.1298 | 3.95% |
| layer3.0.conv1 | 1.9223 | 1.9201 | 0.0136 | 1.9427 | 1.8895 | 2.0214 | 2.61% |
| layer2.0.conv1 | 1.8342 | 1.8280 | 0.0254 | 1.8701 | 1.7805 | 1.9547 | 2.49% |
| stem.bn1 | 0.8890 | 0.8866 | 0.0511 | 0.8979 | 0.8419 | 1.7232 | 1.21% |
| layer2.0.downsample | 0.5663 | 0.5575 | 0.0360 | 0.6271 | 0.5086 | 1.2688 | 0.77% |

### 3.5 Measurement Reliability Tiers

> Operations are classified by mean timing relative to `time.perf_counter()` resolution and Python call overhead (~0.5–1 µs per `_pc()` call).

- **High confidence** (mean ≥ 1.0 ms): 18 operations — timer overhead negligible relative to measured value.
  - Examples: `stem.maxpool`, `layer4.1.conv1`, `layer4.0.conv2`, `layer4.1.conv2`, `layer3.0.conv2`, `stem.conv1`, `layer3.1.conv1`, `layer4.0.conv1`
- **Moderate confidence** (0.1–1.0 ms): 11 operations — measurable but higher relative variance expected.
  - Examples: `stem.bn1`, `layer2.0.downsample`, `layer4.0.downsample`, `layer3.0.downsample`, `stem.relu`, `layer1.1.add`
- **Low confidence** (mean < 0.1 ms): 34 operations — near timer resolution limit. Rankings within this tier are unreliable. Useful only for confirming these operations are negligible.
  - Examples: `layer3.0.bn2`, `layer3.1.bn2`, `layer2.0.bn1`, `layer4.0.bn1`, `layer4.1.bn1`, `layer3.1.bn1`

### 3.6 Timing Gap Analysis

> *Parent timings and the sum of their children are measured independently. A small positive residual (the "timing gap") is expected due to Python interpreter overhead between `perf_counter()` calls. This gap does not represent missing compute.*

| Parent | Parent Mean (ms) | Children Sum (ms) | Gap (ms) | Gap (%) |
|--------|-----------------|-------------------|----------|---------|
| layer3.0 | 6.3161 | 6.2847 | 0.0314 | 0.50% |
| layer2.0 | 5.7652 | 5.7381 | 0.0271 | 0.47% |
| layer1.0 | 6.6056 | 6.5788 | 0.0268 | 0.41% |
| layer3.1 | 7.3402 | 7.3144 | 0.0258 | 0.35% |
| layer1.1 | 6.4205 | 6.3983 | 0.0222 | 0.35% |
| layer1 | 13.0706 | 13.0261 | 0.0445 | 0.34% |
| layer2.1 | 6.1676 | 6.1477 | 0.0199 | 0.32% |
| layer2 | 11.9682 | 11.9328 | 0.0354 | 0.30% |
| layer4.0 | 10.3065 | 10.2758 | 0.0307 | 0.30% |
| layer3 | 13.6888 | 13.6563 | 0.0325 | 0.24% |
| layer4.1 | 12.3001 | 12.2738 | 0.0263 | 0.21% |
| stem | 12.0278 | 12.0091 | 0.0187 | 0.16% |
| layer4 | 22.6391 | 22.6066 | 0.0326 | 0.14% |
| model | 73.7529 | 73.7188 | 0.0341 | 0.05% |

### 3.7 Cross-Round Consistency

| Unit | Round CV |
|------|----------|
| layer1.1.add | 0.3941 |
| layer1.0.bn2 | 0.3897 |
| layer1.1.bn2 | 0.3149 |
| layer1.1.bn1 | 0.2916 |
| layer1.0.bn1 | 0.2683 |
| layer1.0.add | 0.2546 |
| layer2.0.add | 0.1780 |
| layer1.1.relu2 | 0.1774 |
| layer1.1.relu1 | 0.1576 |
| layer1.0.relu2 | 0.1215 |
| layer2.1.bn1 | 0.0906 |
| layer1.0.relu1 | 0.0859 |
| layer2.0.bn2 | 0.0772 |
| layer3.0.bn1 | 0.0701 |
| layer2.1.add | 0.0657 |

## 4. Interpretation

### 4.1 Observations

- Total mean forward pass: 73.7529 ms.
- Most expensive stage: `layer4` at 30.7% of total (22.6391 ms).
- Least expensive stage: `avgpool` at 0.1% of total (0.0923 ms).
- Most expensive block: `layer4.1` at 16.7% of total (12.3001 ms).
- Convolution operations account for 81.8% of total compute.
- BatchNorm operations account for 3.4% of total compute.
- Operations below 0.1 ms (relu, add, some bn) collectively account for ~2.5% of compute. Individual rankings within this tier are near timer resolution and should not be over-interpreted.
- Largest timing gap: `layer3.0` (0.0314 ms, 0.50%).

### 4.2 Model Total

- **Mean forward pass:** 73.7529 ms
- **Median:** 73.7118 ms
- **Std:** 0.2623 ms
- **p95:** 74.0257 ms
- **Observations:** 2000
