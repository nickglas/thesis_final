# RQ1.1 Experiment Report

> Source results directory: `results/rq1_1_20260415_192843/`.
> Derived analysis artifacts directory: `results/rq1_1_20260415_192843_analysis`.

## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 78.841 | 77.969 | 2.610 | 85.961 | [78.680, 79.003] |
| split_after_layer4 | 1000 | 77.243 | 76.190 | 2.723 | 84.093 | [77.075, 77.412] |
| split_after_layer3 | 1000 | 77.903 | 76.843 | 2.756 | 84.742 | [77.732, 78.074] |
| split_after_layer2 | 1000 | 79.218 | 78.210 | 2.622 | 85.993 | [79.055, 79.381] |
| monolithic | 1000 | 75.357 | 72.775 | 3.542 | 80.263 | [75.137, 75.577] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 75.254 | 72.674 | 3.608 | 80.248 |
| 1 | split_after_layer1 | 200 | 77.905 | 77.845 | 1.062 | 78.429 |
| 1 | split_after_layer2 | 200 | 79.380 | 78.754 | 2.138 | 86.425 |
| 1 | split_after_layer3 | 200 | 77.745 | 77.025 | 2.242 | 84.660 |
| 1 | split_after_layer4 | 200 | 76.950 | 76.276 | 2.216 | 83.928 |
| 2 | monolithic | 200 | 75.289 | 72.711 | 3.601 | 80.309 |
| 2 | split_after_layer1 | 200 | 78.979 | 77.941 | 2.835 | 85.950 |
| 2 | split_after_layer2 | 200 | 79.145 | 78.090 | 2.708 | 85.823 |
| 2 | split_after_layer3 | 200 | 77.839 | 76.669 | 2.832 | 84.686 |
| 2 | split_after_layer4 | 200 | 77.266 | 76.080 | 2.833 | 84.047 |
| 3 | monolithic | 200 | 75.938 | 73.955 | 3.283 | 80.399 |
| 3 | split_after_layer1 | 200 | 79.031 | 77.935 | 2.850 | 85.884 |
| 3 | split_after_layer2 | 200 | 79.126 | 78.048 | 2.703 | 85.855 |
| 3 | split_after_layer3 | 200 | 77.971 | 76.868 | 2.786 | 84.851 |
| 3 | split_after_layer4 | 200 | 77.521 | 76.409 | 2.802 | 84.327 |
| 4 | monolithic | 200 | 75.276 | 72.676 | 3.585 | 80.255 |
| 4 | split_after_layer1 | 200 | 79.143 | 78.111 | 2.847 | 86.243 |
| 4 | split_after_layer2 | 200 | 79.201 | 78.145 | 2.697 | 85.993 |
| 4 | split_after_layer3 | 200 | 77.992 | 76.806 | 2.914 | 84.662 |
| 4 | split_after_layer4 | 200 | 77.233 | 76.083 | 2.864 | 83.879 |
| 5 | monolithic | 200 | 75.031 | 72.447 | 3.594 | 79.995 |
| 5 | split_after_layer1 | 200 | 79.150 | 78.063 | 2.770 | 86.050 |
| 5 | split_after_layer2 | 200 | 79.237 | 78.080 | 2.828 | 86.041 |
| 5 | split_after_layer3 | 200 | 77.968 | 76.747 | 2.961 | 84.795 |
| 5 | split_after_layer4 | 200 | 77.247 | 76.136 | 2.840 | 84.095 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 75.357 | 0.3412 | 0.9070 | 0.0045 |
| split_after_layer1 | 5 | 78.841 | 0.5288 | 1.2450 | 0.0067 |
| split_after_layer2 | 5 | 79.218 | 0.1006 | 0.2534 | 0.0013 |
| split_after_layer3 | 5 | 77.903 | 0.1068 | 0.2463 | 0.0014 |
| split_after_layer4 | 5 | 77.243 | 0.2022 | 0.5704 | 0.0026 |

## Overhead vs Monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary Crossing (ms) |
|---|---|---|---|---|
| split_after_layer1 | 3.484 | 4.6% | 784.0 | 52.948 |
| split_after_layer4 | 1.886 | 2.5% | 98.0 | 2.162 |
| split_after_layer3 | 2.546 | 3.4% | 196.0 | 25.813 |
| split_after_layer2 | 3.861 | 5.1% | 392.0 | 40.130 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 1.120 | large | 303709.0 | 3.49e-52 |
| split_after_layer4 | 0.597 | medium | 301918.0 | 4.16e-53 |
| split_after_layer3 | 0.802 | large | 300254.0 | 5.67e-54 |
| split_after_layer2 | 1.239 | large | 297938.0 | 3.44e-55 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer4 (77.243 ms)
- **Near-best window:** 5.0% → threshold 81.106 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer3 (77.903 ms)
- **Selected reference candidate:** split_after_layer1 (78.841 ms)
- **Rejected:** split_after_layer4, split_after_layer2
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
