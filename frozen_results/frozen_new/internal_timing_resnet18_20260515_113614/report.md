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
  max_extra_iterations: -1

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

- **Platform:** Linux-6.17.0-23-generic-x86_64-with-glibc2.39
- **Processor:** x86_64
- **Python:** 3.12.3
- **PyTorch:** 2.11.0+cu130
- **CPU count:** 16
- **Git commit:** 6b152f6e377d71747641c351acc99b3c44b2ceec

## 2. Validation

### 2.1 Functional Equivalence

- **Passed:** True
- **Inputs tested:** 5
- **Max abs diff:** 0.00e+00
- **Tolerance:** 1.00e-06

### 2.2 Warmup Calibration

- **Total warmup iterations:** 50
- **Stabilised:** True
- **Stabilised at iteration:** 16
- **Final window CV:** 0.0102

### 2.3 Instrumentation Overhead

- **Plain forward mean:** 75.0759 ms
- **Instrumented forward mean:** 75.7835 ms
- **Overhead:** 0.7076 ms (0.94%)
- **Samples:** 50
- **Method:** interleaved_outer_timing
- **Overhead warmup:** 20 iterations per model

## 3. Results

### 3.1 Stage-Level Summary (L1)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4 | 23.5758 | 23.4788 | 0.4199 | 24.1954 | 23.0836 | 30.5080 | 31.28% |
| layer3 | 13.9611 | 13.8940 | 0.2942 | 14.4573 | 13.5338 | 19.0179 | 18.52% |
| layer1 | 13.1323 | 13.1100 | 0.3962 | 13.7477 | 12.5523 | 18.0478 | 17.42% |
| stem | 12.1716 | 12.1192 | 0.2171 | 12.5046 | 11.9138 | 15.8228 | 16.15% |
| layer2 | 12.1720 | 12.0882 | 0.3757 | 12.7360 | 11.7268 | 18.5819 | 16.15% |
| fc | 0.2367 | 0.2286 | 0.0213 | 0.2749 | 0.2197 | 0.7194 | 0.31% |
| avgpool | 0.0937 | 0.0906 | 0.0088 | 0.1094 | 0.0861 | 0.3058 | 0.12% |

### 3.2 Block-Level Summary (L2)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1 | 12.5651 | 12.5058 | 0.2425 | 12.9744 | 12.2925 | 16.6128 | 16.67% |
| layer4.0 | 10.9775 | 10.9210 | 0.2522 | 11.3444 | 10.6902 | 15.6643 | 14.56% |
| layer3.1 | 7.4748 | 7.4296 | 0.2003 | 7.8210 | 7.2230 | 10.1557 | 9.92% |
| layer1.0 | 6.5697 | 6.5219 | 0.1897 | 6.8811 | 6.3402 | 9.0843 | 8.72% |
| layer1.1 | 6.5193 | 6.5589 | 0.2880 | 6.9567 | 6.1149 | 8.9134 | 8.65% |
| layer3.0 | 6.4534 | 6.4181 | 0.1550 | 6.7184 | 6.2609 | 8.8186 | 8.56% |
| layer2.1 | 6.3228 | 6.2779 | 0.2053 | 6.6556 | 6.0731 | 9.5288 | 8.39% |
| layer2.0 | 5.8147 | 5.7657 | 0.2230 | 6.1542 | 5.5398 | 9.2923 | 7.71% |

### 3.3 Operation-Level Summary (L3) — Grouped by Parent

#### stem

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 7.2674 | 7.2471 | 0.1102 | 7.4158 | 7.1420 | 9.4787 | 9.64% |
| stem.conv1 | 3.6152 | 3.5937 | 0.0875 | 3.7517 | 3.5146 | 4.6727 | 4.80% |
| stem.bn1 | 0.9095 | 0.9012 | 0.0389 | 0.9772 | 0.8075 | 1.4933 | 1.21% |
| stem.relu | 0.3601 | 0.3454 | 0.0541 | 0.4638 | 0.2971 | 0.8215 | 0.48% |

#### layer4.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.1.conv1 | 6.1572 | 6.1204 | 0.1375 | 6.3904 | 6.0136 | 8.0924 | 8.17% |
| layer4.1.conv2 | 6.1026 | 6.0691 | 0.1354 | 6.3293 | 5.9587 | 8.1193 | 8.10% |
| layer4.1.bn1 | 0.0963 | 0.0941 | 0.0083 | 0.1124 | 0.0858 | 0.1590 | 0.13% |
| layer4.1.bn2 | 0.0945 | 0.0921 | 0.0084 | 0.1106 | 0.0816 | 0.1412 | 0.13% |
| layer4.1.relu1 | 0.0313 | 0.0305 | 0.0042 | 0.0375 | 0.0270 | 0.1144 | 0.04% |
| layer4.1.add | 0.0332 | 0.0324 | 0.0038 | 0.0399 | 0.0281 | 0.0783 | 0.04% |
| layer4.1.relu2 | 0.0237 | 0.0229 | 0.0037 | 0.0281 | 0.0200 | 0.0988 | 0.03% |

#### layer4.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer4.0.conv2 | 6.1529 | 6.1186 | 0.1726 | 6.3738 | 5.9963 | 10.8001 | 8.16% |
| layer4.0.conv1 | 4.0020 | 3.9805 | 0.1045 | 4.2045 | 3.8524 | 5.1023 | 5.31% |
| layer4.0.downsample | 0.5124 | 0.5035 | 0.0385 | 0.5735 | 0.4745 | 1.0455 | 0.68% |
| layer4.0.bn1 | 0.0987 | 0.0959 | 0.0096 | 0.1168 | 0.0853 | 0.1863 | 0.13% |
| layer4.0.bn2 | 0.0943 | 0.0919 | 0.0091 | 0.1103 | 0.0833 | 0.2092 | 0.13% |
| layer4.0.relu1 | 0.0320 | 0.0310 | 0.0037 | 0.0396 | 0.0277 | 0.0754 | 0.04% |
| layer4.0.add | 0.0301 | 0.0291 | 0.0040 | 0.0381 | 0.0262 | 0.0712 | 0.04% |
| layer4.0.relu2 | 0.0242 | 0.0234 | 0.0033 | 0.0288 | 0.0203 | 0.0484 | 0.03% |

#### layer3.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.0.conv2 | 3.6694 | 3.6456 | 0.0859 | 3.8227 | 3.5424 | 4.7893 | 4.87% |
| layer3.0.conv1 | 1.9706 | 1.9480 | 0.0725 | 2.0868 | 1.8939 | 2.8070 | 2.61% |
| layer3.0.downsample | 0.4954 | 0.4878 | 0.0346 | 0.5556 | 0.4471 | 0.8287 | 0.66% |
| layer3.0.bn2 | 0.1027 | 0.0998 | 0.0115 | 0.1245 | 0.0885 | 0.2055 | 0.14% |
| layer3.0.bn1 | 0.0867 | 0.0831 | 0.0120 | 0.1085 | 0.0725 | 0.2056 | 0.11% |
| layer3.0.add | 0.0384 | 0.0371 | 0.0052 | 0.0504 | 0.0325 | 0.0864 | 0.05% |
| layer3.0.relu1 | 0.0316 | 0.0304 | 0.0052 | 0.0415 | 0.0261 | 0.1057 | 0.04% |
| layer3.0.relu2 | 0.0274 | 0.0263 | 0.0044 | 0.0329 | 0.0239 | 0.1043 | 0.04% |

#### layer3.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer3.1.conv1 | 3.6251 | 3.5973 | 0.0970 | 3.8169 | 3.5005 | 4.8964 | 4.81% |
| layer3.1.conv2 | 3.5207 | 3.4953 | 0.1150 | 3.7064 | 3.3841 | 4.8139 | 4.67% |
| layer3.1.bn1 | 0.0974 | 0.0944 | 0.0100 | 0.1151 | 0.0847 | 0.1882 | 0.13% |
| layer3.1.bn2 | 0.0981 | 0.0952 | 0.0139 | 0.1219 | 0.0798 | 0.2002 | 0.13% |
| layer3.1.add | 0.0470 | 0.0457 | 0.0057 | 0.0590 | 0.0395 | 0.0961 | 0.06% |
| layer3.1.relu1 | 0.0339 | 0.0329 | 0.0042 | 0.0429 | 0.0293 | 0.1128 | 0.05% |
| layer3.1.relu2 | 0.0268 | 0.0256 | 0.0046 | 0.0382 | 0.0215 | 0.0720 | 0.04% |

#### layer1.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.0.conv1 | 3.1665 | 3.1453 | 0.0889 | 3.2920 | 3.0519 | 4.7686 | 4.20% |
| layer1.0.conv2 | 2.9202 | 2.8947 | 0.0845 | 3.0577 | 2.8357 | 4.0818 | 3.87% |
| layer1.0.bn1 | 0.1252 | 0.1215 | 0.0160 | 0.1489 | 0.1083 | 0.3991 | 0.17% |
| layer1.0.bn2 | 0.1215 | 0.1131 | 0.0288 | 0.1743 | 0.0887 | 0.3528 | 0.16% |
| layer1.0.add | 0.1160 | 0.1124 | 0.0130 | 0.1382 | 0.1006 | 0.2772 | 0.15% |
| layer1.0.relu1 | 0.0492 | 0.0476 | 0.0059 | 0.0603 | 0.0444 | 0.1322 | 0.07% |
| layer1.0.relu2 | 0.0442 | 0.0423 | 0.0065 | 0.0591 | 0.0362 | 0.1173 | 0.06% |

#### layer2.0

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.0.conv2 | 3.0715 | 3.0480 | 0.0955 | 3.2113 | 2.9610 | 4.6350 | 4.07% |
| layer2.0.conv1 | 1.8866 | 1.8700 | 0.0814 | 2.0056 | 1.8032 | 2.9539 | 2.50% |
| layer2.0.downsample | 0.5241 | 0.5119 | 0.0530 | 0.6152 | 0.4534 | 1.0800 | 0.70% |
| layer2.0.bn1 | 0.1026 | 0.0987 | 0.0134 | 0.1264 | 0.0879 | 0.2237 | 0.14% |
| layer2.0.bn2 | 0.0836 | 0.0782 | 0.0187 | 0.1225 | 0.0629 | 0.2023 | 0.11% |
| layer2.0.add | 0.0512 | 0.0485 | 0.0084 | 0.0687 | 0.0420 | 0.1467 | 0.07% |
| layer2.0.relu1 | 0.0352 | 0.0339 | 0.0055 | 0.0453 | 0.0291 | 0.1613 | 0.05% |
| layer2.0.relu2 | 0.0314 | 0.0301 | 0.0049 | 0.0409 | 0.0258 | 0.1006 | 0.04% |

#### layer2.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer2.1.conv1 | 3.0204 | 2.9931 | 0.0953 | 3.1637 | 2.9122 | 4.4263 | 4.01% |
| layer2.1.conv2 | 3.0065 | 2.9811 | 0.0931 | 3.1476 | 2.8933 | 4.6079 | 3.99% |
| layer2.1.bn1 | 0.0802 | 0.0756 | 0.0161 | 0.1134 | 0.0620 | 0.1879 | 0.11% |
| layer2.1.bn2 | 0.0782 | 0.0718 | 0.0199 | 0.1216 | 0.0582 | 0.2214 | 0.10% |
| layer2.1.add | 0.0578 | 0.0568 | 0.0093 | 0.0744 | 0.0404 | 0.1351 | 0.08% |
| layer2.1.relu1 | 0.0307 | 0.0292 | 0.0063 | 0.0406 | 0.0229 | 0.1511 | 0.04% |
| layer2.1.relu2 | 0.0273 | 0.0258 | 0.0056 | 0.0381 | 0.0213 | 0.0867 | 0.04% |

#### layer1.1

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| layer1.1.conv2 | 2.9761 | 2.9732 | 0.1093 | 3.1508 | 2.8388 | 4.1100 | 3.95% |
| layer1.1.conv1 | 2.9666 | 2.9426 | 0.0873 | 3.1149 | 2.8740 | 4.0754 | 3.94% |
| layer1.1.bn2 | 0.1607 | 0.1673 | 0.0487 | 0.2276 | 0.0901 | 0.3693 | 0.21% |
| layer1.1.bn1 | 0.1498 | 0.1345 | 0.0465 | 0.2164 | 0.0911 | 0.4496 | 0.20% |
| layer1.1.add | 0.1450 | 0.1303 | 0.0399 | 0.2046 | 0.0916 | 0.3893 | 0.19% |
| layer1.1.relu1 | 0.0488 | 0.0492 | 0.0100 | 0.0663 | 0.0349 | 0.1490 | 0.06% |
| layer1.1.relu2 | 0.0477 | 0.0476 | 0.0103 | 0.0686 | 0.0353 | 0.1571 | 0.06% |

### 3.4 Ranked Operations (Top 20 by Compute Share)

| Unit | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | Min (ms) | Max (ms) | % of Model |
|------|-----------|-------------|----------|----------|----------|----------|------------|
| stem.maxpool | 7.2674 | 7.2471 | 0.1102 | 7.4158 | 7.1420 | 9.4787 | 9.64% |
| layer4.1.conv1 | 6.1572 | 6.1204 | 0.1375 | 6.3904 | 6.0136 | 8.0924 | 8.17% |
| layer4.0.conv2 | 6.1529 | 6.1186 | 0.1726 | 6.3738 | 5.9963 | 10.8001 | 8.16% |
| layer4.1.conv2 | 6.1026 | 6.0691 | 0.1354 | 6.3293 | 5.9587 | 8.1193 | 8.10% |
| layer4.0.conv1 | 4.0020 | 3.9805 | 0.1045 | 4.2045 | 3.8524 | 5.1023 | 5.31% |
| layer3.0.conv2 | 3.6694 | 3.6456 | 0.0859 | 3.8227 | 3.5424 | 4.7893 | 4.87% |
| layer3.1.conv1 | 3.6251 | 3.5973 | 0.0970 | 3.8169 | 3.5005 | 4.8964 | 4.81% |
| stem.conv1 | 3.6152 | 3.5937 | 0.0875 | 3.7517 | 3.5146 | 4.6727 | 4.80% |
| layer3.1.conv2 | 3.5207 | 3.4953 | 0.1150 | 3.7064 | 3.3841 | 4.8139 | 4.67% |
| layer1.0.conv1 | 3.1665 | 3.1453 | 0.0889 | 3.2920 | 3.0519 | 4.7686 | 4.20% |
| layer2.0.conv2 | 3.0715 | 3.0480 | 0.0955 | 3.2113 | 2.9610 | 4.6350 | 4.07% |
| layer2.1.conv1 | 3.0204 | 2.9931 | 0.0953 | 3.1637 | 2.9122 | 4.4263 | 4.01% |
| layer2.1.conv2 | 3.0065 | 2.9811 | 0.0931 | 3.1476 | 2.8933 | 4.6079 | 3.99% |
| layer1.1.conv2 | 2.9761 | 2.9732 | 0.1093 | 3.1508 | 2.8388 | 4.1100 | 3.95% |
| layer1.1.conv1 | 2.9666 | 2.9426 | 0.0873 | 3.1149 | 2.8740 | 4.0754 | 3.94% |
| layer1.0.conv2 | 2.9202 | 2.8947 | 0.0845 | 3.0577 | 2.8357 | 4.0818 | 3.87% |
| layer3.0.conv1 | 1.9706 | 1.9480 | 0.0725 | 2.0868 | 1.8939 | 2.8070 | 2.61% |
| layer2.0.conv1 | 1.8866 | 1.8700 | 0.0814 | 2.0056 | 1.8032 | 2.9539 | 2.50% |
| stem.bn1 | 0.9095 | 0.9012 | 0.0389 | 0.9772 | 0.8075 | 1.4933 | 1.21% |
| layer2.0.downsample | 0.5241 | 0.5119 | 0.0530 | 0.6152 | 0.4534 | 1.0800 | 0.70% |

### 3.5 Measurement Reliability Tiers

> Operations are classified by mean timing relative to `time.perf_counter()` resolution and Python call overhead (~0.5–1 µs per `_pc()` call).

- **High confidence** (mean ≥ 1.0 ms): 18 operations — timer overhead negligible relative to measured value.
  - Examples: `stem.maxpool`, `layer4.1.conv1`, `layer4.0.conv2`, `layer4.1.conv2`, `layer4.0.conv1`, `layer3.0.conv2`, `layer3.1.conv1`, `stem.conv1`
- **Moderate confidence** (0.1–1.0 ms): 13 operations — measurable but higher relative variance expected.
  - Examples: `stem.bn1`, `layer2.0.downsample`, `layer4.0.downsample`, `layer3.0.downsample`, `stem.relu`, `layer1.1.bn2`
- **Low confidence** (mean < 0.1 ms): 32 operations — near timer resolution limit. Rankings within this tier are unreliable. Useful only for confirming these operations are negligible.
  - Examples: `layer4.0.bn1`, `layer3.1.bn2`, `layer3.1.bn1`, `layer4.1.bn1`, `layer4.1.bn2`, `layer4.0.bn2`

### 3.6 Timing Gap Analysis

> *Parent timings and the sum of their children are measured independently. A small positive residual (the "timing gap") is expected due to Python interpreter overhead between `perf_counter()` calls. This gap does not represent missing compute.*

| Parent | Parent Mean (ms) | Children Sum (ms) | Gap (ms) | Gap (%) |
|--------|-----------------|-------------------|----------|---------|
| layer2.0 | 5.8147 | 5.7862 | 0.0286 | 0.49% |
| layer3.0 | 6.4534 | 6.4222 | 0.0312 | 0.48% |
| layer1.0 | 6.5697 | 6.5427 | 0.0270 | 0.41% |
| layer1.1 | 6.5193 | 6.4947 | 0.0247 | 0.38% |
| layer3.1 | 7.4748 | 7.4489 | 0.0258 | 0.35% |
| layer2.1 | 6.3228 | 6.3012 | 0.0216 | 0.34% |
| layer1 | 13.1323 | 13.0891 | 0.0433 | 0.33% |
| layer2 | 12.1720 | 12.1375 | 0.0345 | 0.28% |
| layer4.0 | 10.9775 | 10.9465 | 0.0309 | 0.28% |
| layer3 | 13.9611 | 13.9282 | 0.0330 | 0.24% |
| layer4.1 | 12.5651 | 12.5389 | 0.0262 | 0.21% |
| stem | 12.1716 | 12.1522 | 0.0194 | 0.16% |
| layer4 | 23.5758 | 23.5426 | 0.0332 | 0.14% |
| model | 75.3769 | 75.3433 | 0.0337 | 0.04% |

### 3.7 Cross-Round Consistency

| Unit | Round CV |
|------|----------|
| layer1.1.bn1 | 0.2832 |
| layer1.1.bn2 | 0.2633 |
| layer1.1.add | 0.2476 |
| layer1.1.relu1 | 0.1452 |
| layer1.1.relu2 | 0.1265 |
| layer2.1.bn1 | 0.0534 |
| layer2.0.bn2 | 0.0414 |
| layer2.1.relu1 | 0.0373 |
| layer2.1.add | 0.0363 |
| layer1.1 | 0.0333 |
| layer2.1.bn2 | 0.0321 |
| layer1.0.bn2 | 0.0283 |
| layer3.0.relu1 | 0.0241 |
| layer1.0.relu2 | 0.0237 |
| layer1.1.conv2 | 0.0219 |

## 4. Interpretation

### 4.1 Observations

- Total mean forward pass: 75.3769 ms.
- Most expensive stage: `layer4` at 31.3% of total (23.5758 ms).
- Least expensive stage: `avgpool` at 0.1% of total (0.0937 ms).
- Most expensive block: `layer4.1` at 16.7% of total (12.5651 ms).
- Convolution operations account for 82.0% of total compute.
- BatchNorm operations account for 3.4% of total compute.
- Operations below 0.1 ms (relu, add, some bn) collectively account for ~2.3% of compute. Individual rankings within this tier are near timer resolution and should not be over-interpreted.
- Largest timing gap: `layer2.0` (0.0286 ms, 0.49%).

### 4.2 Model Total

- **Mean forward pass:** 75.3769 ms
- **Median:** 75.2299 ms
- **Std:** 1.1426 ms
- **p95:** 76.8046 ms
- **Observations:** 2000
