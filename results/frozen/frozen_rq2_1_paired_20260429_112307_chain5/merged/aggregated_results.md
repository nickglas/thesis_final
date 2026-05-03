# RQ2.1 Aggregated Results

- Topology: `chain5`
- Image: `thesisrq21acr26.azurecr.io/thesis-inference@sha256:524e8618c61d97f466b647cdc408e836256a94807790ad66321ae724f975a221`
- Mesh revision: `asm-1-29`
- Completed executions: `10`
- Iteration rows: `2000`
- Resource metrics complete: `True`
- mTLS security validation passed: `True`

## Overall Latency

| Condition | n | Mean ms | Median ms | p95 ms | p99 ms | Non-compute mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 1000 | 76.69316789299995 | 76.23482900010004 | 79.91813695002747 | 84.08905068985405 | 9.726628656999765 |
| mtls | 1000 | 85.70165645900886 | 85.11237400000482 | 89.94660524988376 | 93.85179872993149 | 18.164162571009 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean | Hop 3 bytes mean | Hop 4 bytes mean | Hop 5 bytes mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |
| mtls | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |

## Hop Forwarding

| Condition | Hop 1 forward ms mean | Hop 2 forward ms mean | Hop 3 forward ms mean | Hop 4 forward ms mean | Hop 5 forward ms mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| plain | 48.4690054290019 | 34.203926052998504 | 19.888696437000817 | 1.91690816299365 | 0.0 |
| mtls | 56.47910376599664 | 39.4088560469984 | 23.047937733999795 | 3.34260326099934 | 0.0 |

## Paired Pass Deltas

| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 76.54754294998952 | 84.7507331750052 | 8.203190225015675 | 10.716464446644656 | 8.219940365029288 |
| 2 | 76.79738293499781 | 86.0185696000042 | 9.221186665006385 | 12.007162630543418 | 8.562230100030774 |
| 3 | 76.4621821600042 | 86.43034042500746 | 9.968158265003254 | 13.03671695393673 | 8.820967990005784 |
| 4 | 76.78127369000208 | 85.39651880500969 | 8.61524511500761 | 11.220502996330767 | 8.204570625006227 |
| 5 | 76.87745773000643 | 85.91212029001781 | 9.034662560011384 | 11.75203086415931 | 8.37996048997411 |

## Overall Comparison

| Metric | Value |
| --- | ---: |
| Mean latency overhead ms | 9.008488566008907 |
| Mean latency overhead % | 11.746142209925772 |
| p95 latency overhead ms | 10.028468299856286 |
| Sidecar CPU mean mCPU | 82.14072095345186 |
| Total pod CPU overhead mean mCPU | 72.4809002136044 |
| Sidecar memory mean MiB | 222.68571428571428 |
| Total pod memory overhead mean MiB | 267.4294372294371 |
| Schedule-to-ready overhead s | 19.28 |

See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.
