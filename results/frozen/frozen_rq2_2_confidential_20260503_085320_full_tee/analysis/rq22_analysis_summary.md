# RQ2.2 Confidential Analysis

Artifact: `C:\Users\Nick\Desktop\opus\results_exports\rq2_2_confidential_20260503_085320`
Generated: `2026-05-03T10:45:02.602860+00:00`
TEE scope: `full_2svc`

## Condition Summary

| Condition | Service1 VM | Service2 VM | n | Mean ms | Median ms | p95 ms | Throughput req/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| standard | Standard_D8as_v5 | Standard_D8as_v5 | 1000 | 60.126 | 59.766 | 63.040 | 16.632 |
| confidential | Standard_DC8as_v5 | Standard_DC8as_v5 | 1000 | 65.031 | 64.158 | 68.250 | 15.377 |

## Confidential Delta

- Mean latency delta: `4.904 ms` (8.156%).
- Median latency delta: `4.392 ms` (7.349%).
- p95 latency delta: `5.209 ms` (8.264%).
- Throughput delta: `-1.254 req/s` (-7.541%).

## Paired Pass Deltas

| Pass | Order | Std mean ms | TEE mean ms | Delta ms | Delta % |
|---:|---|---:|---:|---:|---:|
| 1 | confidential->standard | 59.859 | 63.338 | 3.478 | 5.811 |
| 2 | standard->confidential | 61.034 | 66.200 | 5.166 | 8.464 |
| 3 | confidential->standard | 59.049 | 64.714 | 5.665 | 9.594 |
| 4 | standard->confidential | 59.919 | 65.488 | 5.570 | 9.296 |
| 5 | confidential->standard | 60.771 | 65.412 | 4.641 | 7.637 |

## Interpretation Guardrails

- Both service1 and service2 move to AMD SEV-SNP confidential nodes in the confidential condition.
- The measured variable is both service1 and service2 on standard AMD VMs vs both services on AMD SEV-SNP.
- Both conditions used the same pushed image digest and managed AKS Istio mTLS/AuthZ semantics.
- Throughput is computed as sequential client request rate: `1000 / mean_latency_ms`.
