# RQ2.1 Aggregated Results

- Topology: `chain2`
- Image: `thesisrq21acr26.azurecr.io/thesis-inference@sha256:524e8618c61d97f466b647cdc408e836256a94807790ad66321ae724f975a221`
- Mesh revision: `asm-1-29`
- Completed executions: `10`
- Iteration rows: `2000`
- Resource metrics complete: `True`
- mTLS security validation passed: `True`

## Overall Latency

| Condition | n | Mean ms | Median ms | p95 ms | p99 ms | Non-compute mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 1000 | 70.09394797399763 | 69.93185600003926 | 71.69537169995692 | 74.00982894992467 | 4.268320992994177 |
| mtls | 1000 | 73.2163180440018 | 72.92928449987812 | 75.22686169990038 | 77.9130156600877 | 7.283530049003502 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |
| --- | ---: | ---: | ---: |
| plain | 1003520.0 | 602112.0 | 401408.0 |
| mtls | 1003520.0 | 602112.0 | 401408.0 |

## Hop Forwarding

| Condition | Hop 1 forward ms mean | Hop 2 forward ms mean |
| --- | ---: | ---: |
| plain | 30.65702629500265 | 0.0 |
| mtls | 32.9601295080031 | 0.0 |

## Paired Pass Deltas

| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 70.01516009999136 | 73.24805157499782 | 3.232891475006454 | 4.61741638580764 | 2.981615440018004 |
| 2 | 69.74295347500174 | 73.06046711500812 | 3.317513640006382 | 4.756772512072481 | 2.989127580026434 |
| 3 | 69.80925065000974 | 72.87976485998797 | 3.070514209978228 | 4.398434564743175 | 3.0142091749530664 |
| 4 | 70.48843309499262 | 73.78623303500945 | 3.29779994001683 | 4.678498010549621 | 3.060568875005174 |
| 5 | 70.41394254999204 | 73.10707363500569 | 2.693131085013647 | 3.8247128160755874 | 3.03052421004395 |

## Overall Comparison

| Metric | Value |
| --- | ---: |
| Mean latency overhead ms | 3.122370070004166 |
| Mean latency overhead % | 4.4545501576861595 |
| p95 latency overhead ms | 3.53148999994346 |
| Sidecar CPU mean mCPU | 33.51060166751547 |
| Total pod CPU overhead mean mCPU | 136.82693808614442 |
| Sidecar memory mean MiB | 84.0 |
| Total pod memory overhead mean MiB | 97.19999999999993 |
| Schedule-to-ready overhead s | 16.5 |

See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.
