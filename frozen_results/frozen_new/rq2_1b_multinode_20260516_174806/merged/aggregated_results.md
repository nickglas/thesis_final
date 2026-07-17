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
| plain | 1000 | 69.46947258800537 | 69.38827149997451 | 71.02450900013082 | 72.6857376000271 | 4.945256289005556 |
| mtls | 1000 | 72.18117671599953 | 72.03303599976607 | 73.71667244988203 | 76.3062729799185 | 7.8136381819881535 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |
| --- | ---: | ---: | ---: |
| plain | 1003520.0 | 602112.0 | 401408.0 |
| mtls | 1003520.0 | 602112.0 | 401408.0 |

## Hop Forwarding

| Condition | Hop 1 forward ms mean | Hop 2 forward ms mean |
| --- | ---: | ---: |
| plain | 30.4928616229995 | 0.0 |
| mtls | 32.32602808599631 | 0.0 |

## Paired Pass Deltas

| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 68.95228563498222 | 72.09999795500266 | 3.147712320020446 | 4.565058708399779 | 2.9384990850417125 |
| 2 | 69.47082786500005 | 72.25232145499831 | 2.781493589998263 | 4.003829629615803 | 2.8952026399633723 |
| 3 | 69.00046764001672 | 72.40714118498772 | 3.4066735449709995 | 4.937174575024625 | 2.8376658899401264 |
| 4 | 69.85232424501874 | 71.95814009000287 | 2.1058158449841358 | 3.014668255844478 | 2.609401204970254 |
| 5 | 70.07145755500915 | 72.18828289500607 | 2.1168253399969217 | 3.0209523447334052 | 3.061140644997522 |

## Overall Comparison

| Metric | Value |
| --- | ---: |
| Mean latency overhead ms | 2.711704127994153 |
| Mean latency overhead % | 3.9034471214084863 |
| p95 latency overhead ms | 2.692163449751206 |
| Sidecar CPU mean mCPU | 35.382011353929336 |
| Total pod CPU overhead mean mCPU | 100.25148844887127 |
| Sidecar memory mean MiB | 83.4 |
| Total pod memory overhead mean MiB | 99.10769230769228 |
| Schedule-to-ready overhead s | 7.8 |

See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.
