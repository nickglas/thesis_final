# RQ2.1 Aggregated Results

- Topology: `chain2`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Completed executions: `10`
- Iteration rows: `2000`
- Resource metrics complete: `True`
- mTLS security validation passed: `True`

## Overall Latency

| Condition | n | Mean ms | Median ms | p95 ms | p99 ms | Non-compute mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 1000 | 75.55723812699989 | 75.26246199995512 | 80.04655040002149 | 83.34716431994025 | 4.559136917999922 |
| mtls | 1000 | 79.044981771001 | 78.58992650005803 | 83.67000365003037 | 87.88505896011428 | 7.890561717001788 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |
| --- | ---: | ---: | ---: |
| plain | 1003520.0 | 602112.0 | 401408.0 |
| mtls | 1003520.0 | 602112.0 | 401408.0 |

## Hop Forwarding

| Condition | Hop 1 forward ms mean | Hop 2 forward ms mean |
| --- | ---: | ---: |
| plain | 34.134550986998875 | 0.0 |
| mtls | 36.597946226004126 | 0.0 |

## Paired Pass Deltas

| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 75.99548541500042 | 78.21844874999812 | 2.2229633349977007 | 2.9251255161519367 | 3.2022801999949024 |
| 2 | 76.19311193499982 | 79.34840943499921 | 3.155297499999392 | 4.141184707997187 | 3.3009195850030437 |
| 3 | 75.56478707500901 | 78.91823360000444 | 3.3534465249954337 | 4.437842882646717 | 3.468490234992032 |
| 4 | 75.79647195998746 | 79.27307916500808 | 3.4766072050206276 | 4.586766527676788 | 3.268845465040613 |
| 5 | 74.23633425000276 | 79.46673790499517 | 5.230403654992415 | 7.0456114352012476 | 3.4165885099787374 |

## Overall Comparison

| Metric | Value |
| --- | ---: |
| Mean latency overhead ms | 3.487743644001114 |
| Mean latency overhead % | 4.616028497678492 |
| p95 latency overhead ms | 3.623453250008879 |
| Sidecar CPU mean mCPU | 34.684449272126855 |
| Total pod CPU overhead mean mCPU | -56.81297359313305 |
| Sidecar memory mean MiB | 82.125 |
| Total pod memory overhead mean MiB | 93.81944444444446 |
| Schedule-to-ready overhead s | 6.300000000000001 |

See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.
