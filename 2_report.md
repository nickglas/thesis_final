# RQ1.1 Experiment Report

> Source results directory: `results/rq1_1_20260415_190323/`.
> Derived analysis artifacts directory: `results/rq1_1_20260415_190323_analysis`.

## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 78.724 | 77.875 | 2.571 | 85.893 | [78.564, 78.884] |
| split_after_layer4 | 1000 | 77.440 | 76.339 | 2.814 | 84.516 | [77.265, 77.615] |
| split_after_layer3 | 1000 | 78.079 | 77.068 | 2.670 | 84.928 | [77.913, 78.244] |
| split_after_layer2 | 1000 | 78.189 | 77.144 | 2.700 | 85.060 | [78.022, 78.357] |
| monolithic | 1000 | 75.581 | 73.529 | 3.502 | 81.001 | [75.363, 75.798] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 75.250 | 72.718 | 3.590 | 80.318 |
| 1 | split_after_layer1 | 200 | 78.029 | 78.021 | 0.517 | 78.742 |
| 1 | split_after_layer2 | 200 | 78.535 | 77.896 | 2.193 | 85.780 |
| 1 | split_after_layer3 | 200 | 77.967 | 77.333 | 2.100 | 84.890 |
| 1 | split_after_layer4 | 200 | 76.895 | 76.207 | 2.235 | 83.843 |
| 2 | monolithic | 200 | 75.228 | 72.685 | 3.584 | 80.294 |
| 2 | split_after_layer1 | 200 | 78.897 | 77.842 | 2.828 | 86.148 |
| 2 | split_after_layer2 | 200 | 78.220 | 77.112 | 2.784 | 85.024 |
| 2 | split_after_layer3 | 200 | 77.982 | 76.883 | 2.770 | 84.704 |
| 2 | split_after_layer4 | 200 | 77.542 | 76.397 | 2.831 | 84.344 |
| 3 | monolithic | 200 | 76.151 | 74.629 | 3.090 | 80.427 |
| 3 | split_after_layer1 | 200 | 78.930 | 77.868 | 2.864 | 86.017 |
| 3 | split_after_layer2 | 200 | 77.961 | 76.850 | 2.808 | 84.842 |
| 3 | split_after_layer3 | 200 | 78.188 | 77.094 | 2.790 | 85.013 |
| 3 | split_after_layer4 | 200 | 77.424 | 76.303 | 2.802 | 84.173 |
| 4 | monolithic | 200 | 76.066 | 73.603 | 3.548 | 81.171 |
| 4 | split_after_layer1 | 200 | 78.919 | 77.830 | 2.854 | 86.102 |
| 4 | split_after_layer2 | 200 | 78.007 | 76.879 | 2.803 | 85.015 |
| 4 | split_after_layer3 | 200 | 78.076 | 76.914 | 2.838 | 84.993 |
| 4 | split_after_layer4 | 200 | 77.637 | 76.474 | 2.875 | 84.642 |
| 5 | monolithic | 200 | 75.209 | 72.687 | 3.570 | 80.241 |
| 5 | split_after_layer1 | 200 | 78.844 | 77.776 | 2.824 | 85.828 |
| 5 | split_after_layer2 | 200 | 78.224 | 77.078 | 2.843 | 85.097 |
| 5 | split_after_layer3 | 200 | 78.181 | 77.015 | 2.795 | 84.909 |
| 5 | split_after_layer4 | 200 | 77.702 | 76.342 | 3.195 | 85.608 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 75.581 | 0.4833 | 0.9429 | 0.0064 |
| split_after_layer1 | 5 | 78.724 | 0.3897 | 0.9010 | 0.0050 |
| split_after_layer2 | 5 | 78.189 | 0.2276 | 0.5746 | 0.0029 |
| split_after_layer3 | 5 | 78.079 | 0.1051 | 0.2213 | 0.0013 |
| split_after_layer4 | 5 | 77.440 | 0.3219 | 0.8064 | 0.0042 |

## Overhead vs Monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary Crossing (ms) |
|---|---|---|---|---|
| split_after_layer1 | 3.143 | 4.2% | 784.0 | 52.840 |
| split_after_layer4 | 1.859 | 2.5% | 98.0 | 2.148 |
| split_after_layer3 | 2.498 | 3.3% | 196.0 | 25.844 |
| split_after_layer2 | 2.609 | 3.5% | 392.0 | 39.958 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 1.023 | large | 298966.0 | 1.20e-54 |
| split_after_layer4 | 0.585 | medium | 301216.0 | 1.80e-53 |
| split_after_layer3 | 0.802 | large | 296304.0 | 4.68e-56 |
| split_after_layer2 | 0.834 | large | 295730.0 | 2.31e-56 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer4 (77.440 ms)
- **Near-best window:** 5.0% → threshold 81.312 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3 (78.079 ms)
- **Selected reference candidate:** split_after_layer2 (78.189 ms)
- **Rejected:** split_after_layer1, split_after_layer4
- **Fallback used:** False

## Carry-Forward Rule (as implemented)

1. Identify `raw_fastest`: split with lowest mean end-to-end latency.
2. Near-best window: all splits within 5.0% of `raw_fastest` mean.
3. Degeneracy filter: exclude candidates where the minor compute side contributes < 10.0% of total split compute (`service_a` + `service_b`).
4. If non-degenerate near-best candidates exist: select `selected_main` by (`mean_ms`, `activation_bytes`), with `selected_reference` as runner-up.
5. If ALL near-best candidates are degenerate: `selected_main = None`, `selected_reference = raw_fastest` (reference only, not promoted).
6. Tie-break: prefer lower `activation_bytes_mean`.

## Methodology Notes

- **Parity validation:** Functional equivalence was verified as a mandatory precondition for both local (PartA→PartB) and gRPC round-trip paths. Results are recorded in `parity_validation.json`.
- **Warmup calibration:** Each condition×round warmup was monitored for latency stabilisation using a trailing-window coefficient of variation (CV) check. Calibration results are recorded in `warmup_calibration.json`.
- **Statistical reporting:** Per-iteration significance tests (Mann-Whitney U) are reported as supplementary. With large N, p-values are inflated and should not be over-interpreted. Cross-round consistency and confidence intervals are the primary evidence of result stability.
- **Carry-forward rule:** The selection rule is predeclared and fully explicit. No hidden fallback promotes degenerate candidates to `selected_main`.
