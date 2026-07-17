# RQ2.1 Aggregated Results

- Topology: `chain5`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Completed executions: `10`
- Iteration rows: `2000`
- Resource metrics complete: `True`
- mTLS security validation passed: `True`

## Overall Latency

| Condition | n | Mean ms | Median ms | p95 ms | p99 ms | Non-compute mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 1000 | 82.30234917700135 | 81.81840849999844 | 87.50235095001244 | 89.67742697996073 | 10.800686571001279 |
| mtls | 1000 | 91.13914478000221 | 90.82305449990713 | 96.48503329998448 | 99.80559899011041 | 19.94945685600885 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean | Hop 3 bytes mean | Hop 4 bytes mean | Hop 5 bytes mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |
| mtls | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |

## Hop Forwarding

| Condition | Hop 1 forward ms mean | Hop 2 forward ms mean | Hop 3 forward ms mean | Hop 4 forward ms mean | Hop 5 forward ms mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| plain | 52.611569379994954 | 37.692471664996 | 22.099513362002057 | 2.074162856997077 | 0.0 |
| mtls | 60.782711954005045 | 42.9651104979998 | 25.393323836996775 | 3.663701669001739 | 0.0 |

## Paired Pass Deltas

| Pass | Plain mean ms | mTLS mean ms | Delta ms | Delta % | Non-compute delta ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 81.49066214499669 | 90.14779128499697 | 8.65712914000028 | 10.623461525685743 | 8.94888759499679 |
| 2 | 81.92911634500031 | 91.24402373000012 | 9.314907384999813 | 11.369471319298869 | 9.297315965002326 |
| 3 | 81.26742821499306 | 89.87123442500659 | 8.60380621001353 | 10.587029021334542 | 9.075629335035273 |
| 4 | 82.34723083500285 | 92.33255321499998 | 9.985322379997129 | 12.125875125059734 | 9.12457598001538 |
| 5 | 84.47730834501384 | 92.10012124500736 | 7.622812899993519 | 9.02350352932788 | 9.29744254998809 |

## Overall Comparison

| Metric | Value |
| --- | ---: |
| Mean latency overhead ms | 8.836795603000866 |
| Mean latency overhead % | 10.736990731572252 |
| p95 latency overhead ms | 8.982682349972038 |
| Sidecar CPU mean mCPU | 87.60210778563598 |
| Total pod CPU overhead mean mCPU | 37.48977333121957 |
| Sidecar memory mean MiB | 223.71428571428572 |
| Total pod memory overhead mean MiB | 264.1428571428571 |
| Schedule-to-ready overhead s | 6.839999999999999 |

See `aggregated_results.json`, `aggregated_results.csv`, and `raw_iterations.csv` for the complete merged evidence.
