# RQ1.1 Experiment Report

> Source results directory: `results/rq1_1_20260415_185119/`.
> Derived analysis artifacts directory: `results/rq1_1_20260415_185119_analysis`.

## Condition Summaries

| Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) | 95% CI |
|---|---|---|---|---|---|---|
| split_after_layer1 | 1000 | 78.874 | 78.061 | 2.592 | 86.201 | [78.713, 79.035] |
| split_after_layer4 | 1000 | 78.110 | 76.898 | 3.078 | 84.918 | [77.919, 78.301] |
| split_after_layer3 | 1000 | 78.671 | 77.701 | 2.666 | 85.463 | [78.506, 78.836] |
| split_after_layer2 | 1000 | 78.626 | 77.596 | 2.693 | 85.540 | [78.459, 78.793] |
| monolithic | 1000 | 76.117 | 73.505 | 3.749 | 82.594 | [75.884, 76.350] |

## Per-Round Summaries

| Round | Condition | N | Mean (ms) | Median (ms) | Std (ms) | p95 (ms) |
|---|---|---|---|---|---|---|
| 1 | monolithic | 200 | 75.904 | 73.422 | 3.571 | 81.032 |
| 1 | split_after_layer1 | 200 | 77.645 | 77.577 | 0.567 | 78.481 |
| 1 | split_after_layer2 | 200 | 78.150 | 77.403 | 2.196 | 85.024 |
| 1 | split_after_layer3 | 200 | 77.973 | 77.329 | 2.144 | 84.854 |
| 1 | split_after_layer4 | 200 | 77.404 | 76.742 | 2.221 | 84.446 |
| 2 | monolithic | 200 | 75.944 | 73.464 | 3.567 | 80.978 |
| 2 | split_after_layer1 | 200 | 78.848 | 77.827 | 2.802 | 85.950 |
| 2 | split_after_layer2 | 200 | 78.688 | 77.613 | 2.745 | 85.501 |
| 2 | split_after_layer3 | 200 | 79.031 | 77.878 | 2.726 | 85.607 |
| 2 | split_after_layer4 | 200 | 78.046 | 76.961 | 2.731 | 84.685 |
| 3 | monolithic | 200 | 76.764 | 74.085 | 4.382 | 83.660 |
| 3 | split_after_layer1 | 200 | 79.125 | 78.142 | 2.767 | 86.189 |
| 3 | split_after_layer2 | 200 | 78.660 | 77.569 | 2.795 | 85.547 |
| 3 | split_after_layer3 | 200 | 78.436 | 77.329 | 2.733 | 85.157 |
| 3 | split_after_layer4 | 200 | 77.749 | 76.618 | 2.805 | 84.462 |
| 4 | monolithic | 200 | 75.986 | 73.506 | 3.540 | 81.047 |
| 4 | split_after_layer1 | 200 | 79.536 | 78.477 | 2.781 | 86.587 |
| 4 | split_after_layer2 | 200 | 78.764 | 77.629 | 2.754 | 85.531 |
| 4 | split_after_layer3 | 200 | 78.990 | 77.835 | 2.769 | 85.654 |
| 4 | split_after_layer4 | 200 | 78.046 | 76.925 | 2.761 | 84.669 |
| 5 | monolithic | 200 | 75.988 | 73.495 | 3.581 | 81.088 |
| 5 | split_after_layer1 | 200 | 79.217 | 78.161 | 2.834 | 86.203 |
| 5 | split_after_layer2 | 200 | 78.867 | 77.684 | 2.887 | 85.776 |
| 5 | split_after_layer3 | 200 | 78.926 | 77.841 | 2.769 | 85.682 |
| 5 | split_after_layer4 | 200 | 79.305 | 77.331 | 4.197 | 86.227 |

## Cross-Round Consistency

| Condition | Rounds | Grand Mean (ms) | Round Std (ms) | Round Range (ms) | Round CV |
|---|---|---|---|---|---|
| monolithic | 5 | 76.117 | 0.3631 | 0.8599 | 0.0048 |
| split_after_layer1 | 5 | 78.874 | 0.7297 | 1.8910 | 0.0093 |
| split_after_layer2 | 5 | 78.626 | 0.2779 | 0.7174 | 0.0035 |
| split_after_layer3 | 5 | 78.671 | 0.4579 | 1.0576 | 0.0058 |
| split_after_layer4 | 5 | 78.110 | 0.7183 | 1.9003 | 0.0092 |

## Overhead vs Monolithic

| Condition | Overhead (ms) | Overhead (%) | Activation (KB) | Boundary Crossing (ms) |
|---|---|---|---|---|
| split_after_layer1 | 2.757 | 3.6% | 784.0 | 52.989 |
| split_after_layer4 | 1.993 | 2.6% | 98.0 | 2.124 |
| split_after_layer3 | 2.554 | 3.4% | 196.0 | 25.675 |
| split_after_layer2 | 2.509 | 3.3% | 392.0 | 39.872 |

## Effect Sizes (Supplementary)

> **Methodological note:** Effect sizes below are computed from pooled per-iteration data. With N = 1,000 iterations per condition, Mann-Whitney p-values are near-zero for any non-trivial difference and should not be interpreted as strong evidence of practical significance. Cohen's d provides a more informative measure of effect magnitude. Cross-round consistency (above) is a more defensible indicator of result stability.

| Condition | Cohen's d | Interpretation | Mann-Whitney U | p-value |
|---|---|---|---|---|
| split_after_layer1 | 0.855 | large | 295570.0 | 1.90e-56 |
| split_after_layer4 | 0.581 | medium | 287603.0 | 8.66e-61 |
| split_after_layer3 | 0.785 | medium | 290533.0 | 3.57e-59 |
| split_after_layer2 | 0.769 | medium | 290084.0 | 2.03e-59 |

## Carry-Forward Selection

- **Raw fastest boundary:** split_after_layer4 (78.110 ms)
- **Near-best window:** 5.0% → threshold 82.015 ms
- **Near-best candidates:** split_after_layer1, split_after_layer4, split_after_layer3, split_after_layer2
- **Degenerate candidates:** split_after_layer4
- **Degeneracy threshold:** 10.0% of split compute
- **Selected main candidate:** split_after_layer2 (78.626 ms)
- **Selected reference candidate:** split_after_layer3 (78.671 ms)
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
