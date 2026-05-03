# RQ2.2 Confidential Service2 Analysis

Artifact: `C:\Users\Nick\Desktop\opus\results_exports\rq2_2_confidential_20260502_200835`
Generated: `2026-05-02T21:45:11.910058+00:00`

## Condition Summary

| Condition | Service2 VM | n | Mean ms | Median ms | p95 ms | Throughput req/s |
|---|---:|---:|---:|---:|---:|---:|
| standard | Standard_D8as_v5 | 1000 | 60.204 | 59.631 | 63.982 | 16.610 |
| confidential | Standard_DC8as_v5 | 1000 | 62.263 | 61.462 | 67.832 | 16.061 |

## Confidential Delta

- Mean latency delta: `2.059 ms` (3.420%).
- Median latency delta: `1.831 ms` (3.071%).
- p95 latency delta: `3.850 ms` (6.017%).
- Throughput delta: `-0.549 req/s` (-3.307%).

## Paired Pass Deltas

| Pass | Order | Std mean ms | TEE mean ms | Delta ms | Delta % |
|---:|---|---:|---:|---:|---:|
| 1 | confidential->standard | 60.019 | 62.223 | 2.204 | 3.672 |
| 2 | standard->confidential | 59.064 | 63.559 | 4.496 | 7.612 |
| 3 | confidential->standard | 62.217 | 61.410 | -0.808 | -1.298 |
| 4 | standard->confidential | 59.193 | 62.187 | 2.994 | 5.059 |
| 5 | confidential->standard | 60.529 | 61.938 | 1.409 | 2.328 |

## Interpretation Guardrails

- Service1 stayed on the standard AMD pool; the measured variable is service2 standard vs service2 AMD SEV-SNP.
- Both conditions used the same pushed image digest and managed AKS Istio mTLS/AuthZ semantics.
- Throughput is computed as sequential client request rate: `1000 / mean_latency_ms`.
