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

- **Platform:** Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.35
- **Processor:** x86_64
- **Python:** 3.10.12
- **PyTorch:** 2.11.0+cu130
- **CPU count:** 16
- **Git commit:** 1508e9bbe9acebffff4b93dd0c68cc5538ac0d60

## 2. Validation

### 2.1 Functional Equivalence

- **Passed:** True
- **Inputs tested:** 5
- **Max abs diff:** 0.00e+00
- **Tolerance:** 1.00e-06

### 2.2 Warmup Calibration

- **Total warmup iterations:** 50
- **Stabilised:** True
- **Stabilised at iteration:** 13
- **Final window CV:** 0.0289

### 2.3 Instrumentation Overhead

- **Plain forward mean:** 32.2863 ms
- **Instrumented forward mean:** 32.5020 ms
- **Overhead:** 0.2158 ms (0.67%)
- **Samples:** 50
- **Method:** interleaved_outer_timing
- **Overhead warmup:** 20 iterations per model

## 3. Results

### 3.1 Stage-Level Summary (L1)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4 | 7.1819 | 7.0824 | 0.3834 | 7.7275 | 6.7667 | 12.2059 | 22.03% |
| layer1 | 6.9802 | 6.9410 | 0.1876 | 7.2145 | 6.7844 | 9.6446 | 21.41% |
| layer2 | 6.1989 | 6.1594 | 0.1860 | 6.4208 | 6.0207 | 8.8765 | 19.01% |
| layer3 | 6.1161 | 6.0624 | 0.2952 | 6.3418 | 5.9209 | 11.4718 | 18.76% |
| stem | 5.9436 | 5.9124 | 0.1497 | 6.1141 | 5.7832 | 7.9944 | 18.23% |
| fc | 0.1347 | 0.1314 | 0.0165 | 0.1625 | 0.1109 | 0.3186 | 0.41% |
| avgpool | 0.0406 | 0.0381 | 0.0080 | 0.0563 | 0.0313 | 0.1039 | 0.12% |

### 3.2 Block-Level Summary (L2)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1 | 3.8474 | 3.8064 | 0.1806 | 4.1042 | 3.6438 | 7.0101 | 11.80% |
| layer1.0 | 3.4987 | 3.4744 | 0.1071 | 3.6428 | 3.3792 | 4.8967 | 10.73% |
| layer1.1 | 3.4698 | 3.4459 | 0.1008 | 3.6132 | 3.3516 | 4.7219 | 10.64% |
| layer2.1 | 3.3472 | 3.3215 | 0.1072 | 3.4801 | 3.2425 | 5.5873 | 10.27% |
| layer4.0 | 3.3246 | 3.2662 | 0.2565 | 3.6245 | 3.0885 | 8.1534 | 10.20% |
| layer3.1 | 3.3060 | 3.2763 | 0.1534 | 3.4433 | 3.1910 | 6.8920 | 10.14% |
| layer2.0 | 2.8416 | 2.8186 | 0.1098 | 2.9777 | 2.7221 | 5.1181 | 8.72% |
| layer3.0 | 2.8004 | 2.7685 | 0.1890 | 2.9468 | 2.6663 | 7.2146 | 8.59% |

### 3.3 Operation-Level Summary (L3) — Grouped by Parent

#### stem

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 4.0272 | 4.0024 | 0.1013 | 4.1597 | 3.9235 | 5.3722 | 12.35% |
| stem.conv1 | 1.7397 | 1.7265 | 0.0705 | 1.8161 | 1.6782 | 3.4045 | 5.34% |
| stem.bn1 | 0.1252 | 0.1218 | 0.0108 | 0.1449 | 0.1156 | 0.2191 | 0.38% |
| stem.relu | 0.0491 | 0.0474 | 0.0057 | 0.0587 | 0.0432 | 0.1094 | 0.15% |

#### layer4.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.0.conv2 | 1.9216 | 1.8874 | 0.1449 | 2.1199 | 1.7683 | 4.4157 | 5.89% |
| layer4.0.conv1 | 1.0868 | 1.0641 | 0.1089 | 1.2076 | 0.9875 | 3.6403 | 3.33% |
| layer4.0.downsample | 0.2216 | 0.2156 | 0.0214 | 0.2575 | 0.1980 | 0.5321 | 0.68% |
| layer4.0.bn1 | 0.0315 | 0.0306 | 0.0058 | 0.0404 | 0.0237 | 0.1216 | 0.10% |
| layer4.0.bn2 | 0.0322 | 0.0310 | 0.0050 | 0.0401 | 0.0239 | 0.1101 | 0.10% |
| layer4.0.relu1 | 0.0086 | 0.0082 | 0.0037 | 0.0109 | 0.0057 | 0.1288 | 0.03% |
| layer4.0.add | 0.0084 | 0.0080 | 0.0029 | 0.0096 | 0.0073 | 0.1073 | 0.03% |
| layer4.0.relu2 | 0.0080 | 0.0075 | 0.0024 | 0.0099 | 0.0067 | 0.0523 | 0.02% |

#### layer4.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1.conv1 | 1.8858 | 1.8605 | 0.1175 | 2.0436 | 1.7637 | 4.9671 | 5.78% |
| layer4.1.conv2 | 1.8653 | 1.8469 | 0.0793 | 1.9835 | 1.7577 | 2.5983 | 5.72% |
| layer4.1.bn1 | 0.0337 | 0.0325 | 0.0055 | 0.0413 | 0.0251 | 0.1009 | 0.10% |
| layer4.1.bn2 | 0.0332 | 0.0322 | 0.0047 | 0.0406 | 0.0249 | 0.1011 | 0.10% |
| layer4.1.relu1 | 0.0090 | 0.0086 | 0.0022 | 0.0114 | 0.0063 | 0.0506 | 0.03% |
| layer4.1.add | 0.0082 | 0.0078 | 0.0025 | 0.0097 | 0.0067 | 0.0613 | 0.03% |
| layer4.1.relu2 | 0.0079 | 0.0075 | 0.0025 | 0.0101 | 0.0056 | 0.0831 | 0.02% |

#### layer1.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.0.conv1 | 1.6772 | 1.6632 | 0.0554 | 1.7569 | 1.6123 | 2.3666 | 5.14% |
| layer1.0.conv2 | 1.6502 | 1.6366 | 0.0558 | 1.7222 | 1.5867 | 2.2770 | 5.06% |
| layer1.0.bn1 | 0.0513 | 0.0496 | 0.0065 | 0.0612 | 0.0451 | 0.1284 | 0.16% |
| layer1.0.bn2 | 0.0476 | 0.0458 | 0.0074 | 0.0575 | 0.0382 | 0.1424 | 0.15% |
| layer1.0.add | 0.0289 | 0.0277 | 0.0043 | 0.0364 | 0.0252 | 0.0905 | 0.09% |
| layer1.0.relu1 | 0.0198 | 0.0192 | 0.0035 | 0.0244 | 0.0175 | 0.1013 | 0.06% |
| layer1.0.relu2 | 0.0177 | 0.0169 | 0.0037 | 0.0232 | 0.0144 | 0.0808 | 0.05% |

#### layer1.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.1.conv1 | 1.6554 | 1.6414 | 0.0578 | 1.7374 | 1.5936 | 2.5038 | 5.08% |
| layer1.1.conv2 | 1.6477 | 1.6358 | 0.0490 | 1.7185 | 1.5887 | 2.2078 | 5.05% |
| layer1.1.bn1 | 0.0499 | 0.0485 | 0.0063 | 0.0593 | 0.0396 | 0.1203 | 0.15% |
| layer1.1.bn2 | 0.0484 | 0.0468 | 0.0067 | 0.0578 | 0.0389 | 0.1434 | 0.15% |
| layer1.1.add | 0.0280 | 0.0270 | 0.0050 | 0.0337 | 0.0249 | 0.1203 | 0.09% |
| layer1.1.relu1 | 0.0184 | 0.0178 | 0.0025 | 0.0222 | 0.0149 | 0.0571 | 0.06% |
| layer1.1.relu2 | 0.0174 | 0.0166 | 0.0038 | 0.0221 | 0.0144 | 0.0916 | 0.05% |

#### layer2.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.0.conv2 | 1.6197 | 1.6067 | 0.0651 | 1.6966 | 1.5584 | 3.3846 | 4.97% |
| layer2.0.conv1 | 0.8868 | 0.8772 | 0.0384 | 0.9474 | 0.8435 | 1.2304 | 2.72% |
| layer2.0.downsample | 0.2171 | 0.2108 | 0.0199 | 0.2513 | 0.1956 | 0.3815 | 0.67% |
| layer2.0.bn1 | 0.0349 | 0.0341 | 0.0049 | 0.0439 | 0.0275 | 0.0765 | 0.11% |
| layer2.0.bn2 | 0.0347 | 0.0334 | 0.0053 | 0.0422 | 0.0267 | 0.1298 | 0.11% |
| layer2.0.add | 0.0173 | 0.0166 | 0.0038 | 0.0209 | 0.0153 | 0.1207 | 0.05% |
| layer2.0.relu1 | 0.0124 | 0.0120 | 0.0034 | 0.0158 | 0.0092 | 0.0948 | 0.04% |
| layer2.0.relu2 | 0.0123 | 0.0117 | 0.0030 | 0.0152 | 0.0102 | 0.0964 | 0.04% |

#### layer2.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.1.conv1 | 1.6151 | 1.6022 | 0.0647 | 1.6853 | 1.5543 | 3.4132 | 4.95% |
| layer2.1.conv2 | 1.6142 | 1.6023 | 0.0503 | 1.6846 | 1.5517 | 2.5104 | 4.95% |
| layer2.1.bn1 | 0.0360 | 0.0346 | 0.0059 | 0.0443 | 0.0264 | 0.1102 | 0.11% |
| layer2.1.bn2 | 0.0348 | 0.0334 | 0.0059 | 0.0440 | 0.0261 | 0.1381 | 0.11% |
| layer2.1.add | 0.0174 | 0.0167 | 0.0033 | 0.0210 | 0.0151 | 0.0730 | 0.05% |
| layer2.1.relu1 | 0.0129 | 0.0124 | 0.0027 | 0.0159 | 0.0098 | 0.0534 | 0.04% |
| layer2.1.relu2 | 0.0122 | 0.0116 | 0.0031 | 0.0154 | 0.0096 | 0.0739 | 0.04% |

#### layer3.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.0.conv2 | 1.6119 | 1.5928 | 0.1180 | 1.6935 | 1.5411 | 5.6882 | 4.94% |
| layer3.0.conv1 | 0.8883 | 0.8790 | 0.0454 | 0.9446 | 0.8437 | 1.7808 | 2.72% |
| layer3.0.downsample | 0.2021 | 0.1935 | 0.0979 | 0.2331 | 0.1802 | 4.4859 | 0.62% |
| layer3.0.bn2 | 0.0312 | 0.0301 | 0.0053 | 0.0386 | 0.0223 | 0.1100 | 0.10% |
| layer3.0.bn1 | 0.0304 | 0.0294 | 0.0075 | 0.0392 | 0.0229 | 0.2100 | 0.09% |
| layer3.0.relu1 | 0.0095 | 0.0091 | 0.0027 | 0.0130 | 0.0067 | 0.0687 | 0.03% |
| layer3.0.add | 0.0111 | 0.0106 | 0.0028 | 0.0134 | 0.0095 | 0.0593 | 0.03% |
| layer3.0.relu2 | 0.0093 | 0.0088 | 0.0029 | 0.0118 | 0.0071 | 0.0752 | 0.03% |

#### layer3.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.1.conv1 | 1.6027 | 1.5858 | 0.0788 | 1.6782 | 1.5370 | 3.2535 | 4.92% |
| layer3.1.conv2 | 1.6047 | 1.5885 | 0.0931 | 1.6794 | 1.5372 | 4.6180 | 4.92% |
| layer3.1.bn1 | 0.0322 | 0.0312 | 0.0043 | 0.0399 | 0.0230 | 0.0916 | 0.10% |
| layer3.1.bn2 | 0.0314 | 0.0304 | 0.0044 | 0.0384 | 0.0229 | 0.0858 | 0.10% |
| layer3.1.relu1 | 0.0101 | 0.0095 | 0.0026 | 0.0134 | 0.0066 | 0.0510 | 0.03% |
| layer3.1.add | 0.0112 | 0.0107 | 0.0030 | 0.0134 | 0.0090 | 0.0893 | 0.03% |
| layer3.1.relu2 | 0.0095 | 0.0088 | 0.0030 | 0.0136 | 0.0067 | 0.0556 | 0.03% |

### 3.4 Ranked Operations (Top 20 by Compute Share)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 4.0272 | 4.0024 | 0.1013 | 4.1597 | 3.9235 | 5.3722 | 12.35% |
| layer4.0.conv2 | 1.9216 | 1.8874 | 0.1449 | 2.1199 | 1.7683 | 4.4157 | 5.89% |
| layer4.1.conv1 | 1.8858 | 1.8605 | 0.1175 | 2.0436 | 1.7637 | 4.9671 | 5.78% |
| layer4.1.conv2 | 1.8653 | 1.8469 | 0.0793 | 1.9835 | 1.7577 | 2.5983 | 5.72% |
| stem.conv1 | 1.7397 | 1.7265 | 0.0705 | 1.8161 | 1.6782 | 3.4045 | 5.34% |
| layer1.0.conv1 | 1.6772 | 1.6632 | 0.0554 | 1.7569 | 1.6123 | 2.3666 | 5.14% |
| layer1.1.conv1 | 1.6554 | 1.6414 | 0.0578 | 1.7374 | 1.5936 | 2.5038 | 5.08% |
| layer1.0.conv2 | 1.6502 | 1.6366 | 0.0558 | 1.7222 | 1.5867 | 2.2770 | 5.06% |
| layer1.1.conv2 | 1.6477 | 1.6358 | 0.0490 | 1.7185 | 1.5887 | 2.2078 | 5.05% |
| layer2.0.conv2 | 1.6197 | 1.6067 | 0.0651 | 1.6966 | 1.5584 | 3.3846 | 4.97% |
| layer2.1.conv1 | 1.6151 | 1.6022 | 0.0647 | 1.6853 | 1.5543 | 3.4132 | 4.95% |
| layer2.1.conv2 | 1.6142 | 1.6023 | 0.0503 | 1.6846 | 1.5517 | 2.5104 | 4.95% |
| layer3.0.conv2 | 1.6119 | 1.5928 | 0.1180 | 1.6935 | 1.5411 | 5.6882 | 4.94% |
| layer3.1.conv1 | 1.6027 | 1.5858 | 0.0788 | 1.6782 | 1.5370 | 3.2535 | 4.92% |
| layer3.1.conv2 | 1.6047 | 1.5885 | 0.0931 | 1.6794 | 1.5372 | 4.6180 | 4.92% |
| layer4.0.conv1 | 1.0868 | 1.0641 | 0.1089 | 1.2076 | 0.9875 | 3.6403 | 3.33% |
| layer2.0.conv1 | 0.8868 | 0.8772 | 0.0384 | 0.9474 | 0.8435 | 1.2304 | 2.72% |
| layer3.0.conv1 | 0.8883 | 0.8790 | 0.0454 | 0.9446 | 0.8437 | 1.7808 | 2.72% |
| layer4.0.downsample | 0.2216 | 0.2156 | 0.0214 | 0.2575 | 0.1980 | 0.5321 | 0.68% |
| layer2.0.downsample | 0.2171 | 0.2108 | 0.0199 | 0.2513 | 0.1956 | 0.3815 | 0.67% |

### 3.5 Measurement Reliability Tiers

> Operations are classified by mean timing relative to `time.perf_counter()` resolution and Python call overhead (~0.5–1 µs per `_pc()` call).

- **High confidence** (mean ≥ 1.0 ms): 16 operations — timer overhead negligible relative to measured value.
  - Examples: `stem.maxpool`, `layer4.0.conv2`, `layer4.1.conv1`, `layer4.1.conv2`, `stem.conv1`, `layer1.0.conv1`, `layer1.1.conv1`, `layer1.0.conv2`
- **Moderate confidence** (0.1–1.0 ms): 6 operations — measurable but higher relative variance expected.
  - Examples: `layer3.0.conv1`, `layer2.0.conv1`, `layer4.0.downsample`, `layer2.0.downsample`, `layer3.0.downsample`, `stem.bn1`
- **Low confidence** (mean < 0.1 ms): 41 operations — near timer resolution limit. Rankings within this tier are unreliable. Useful only for confirming these operations are negligible.
  - Examples: `layer1.0.bn1`, `layer1.1.bn1`, `stem.relu`, `layer1.1.bn2`, `layer1.0.bn2`, `layer2.1.bn1`

### 3.6 Timing Gap Analysis

> *Parent timings and the sum of their children are measured independently. A small positive residual (the "timing gap") is expected due to Python interpreter overhead between `perf_counter()` calls. This gap does not represent missing compute.*

| Parent | Parent Mean (ms) | Children Sum (ms) | Gap (ms) | Gap (%) |
|--------|-----------------|-------------------|----------|---------|
| layer3.0 | 2.8004 | 2.7938 | 0.0066 | 0.24% |
| layer2.0 | 2.8416 | 2.8353 | 0.0063 | 0.22% |
| layer4.0 | 3.3246 | 3.3187 | 0.0059 | 0.18% |
| layer1 | 6.9802 | 6.9685 | 0.0117 | 0.17% |
| layer1.0 | 3.4987 | 3.4926 | 0.0060 | 0.17% |
| layer2 | 6.1989 | 6.1887 | 0.0101 | 0.16% |
| layer3 | 6.1161 | 6.1064 | 0.0097 | 0.16% |
| layer4 | 7.1819 | 7.1720 | 0.0099 | 0.14% |
| layer1.1 | 3.4698 | 3.4651 | 0.0047 | 0.13% |
| layer2.1 | 3.3472 | 3.3427 | 0.0045 | 0.13% |
| layer3.1 | 3.3060 | 3.3018 | 0.0043 | 0.13% |
| layer4.1 | 3.8474 | 3.8432 | 0.0042 | 0.11% |
| stem | 5.9436 | 5.9412 | 0.0024 | 0.04% |
| model | 32.6034 | 32.5959 | 0.0075 | 0.02% |

### 3.7 Cross-Round Consistency

| Unit | Round CV |
|------|----------|
| layer3.0.downsample | 0.0339 |
| layer4.0.relu1 | 0.0292 |
| layer3.0.relu2 | 0.0268 |
| layer1.1.bn1 | 0.0268 |
| avgpool | 0.0260 |
| layer3.0.relu1 | 0.0260 |
| layer1.0.add | 0.0260 |
| layer3.1.relu2 | 0.0257 |
| layer2.0.relu1 | 0.0241 |
| layer4.1.add | 0.0233 |
| layer3.1.add | 0.0225 |
| layer4.0.add | 0.0223 |
| layer4.1.relu2 | 0.0212 |
| layer2.0.relu2 | 0.0211 |
| layer3.1.relu1 | 0.0194 |

## 4. Interpretation

### 4.1 Observations

- Total mean forward pass: 32.6034 ms.
- Most expensive stage: `layer4` at 22.0% of total (7.1819 ms).
- Least expensive stage: `avgpool` at 0.1% of total (0.0406 ms).
- Most expensive block: `layer4.1` at 11.8% of total (3.8474 ms).
- Convolution operations account for 81.5% of total compute.
- BatchNorm operations account for 2.2% of total compute.
- Operations below 0.1 ms (relu, add, some bn) collectively account for ~3.0% of compute. Individual rankings within this tier are near timer resolution and should not be over-interpreted.
- Largest timing gap: `layer3.0` (0.0066 ms, 0.24%).

### 4.2 Model Total

- **Mean forward pass:** 32.6034 ms
- **Median:** 32.4012 ms
- **Std:** 0.9267 ms
- **p95:** 33.8925 ms
- **Observations:** 2000
