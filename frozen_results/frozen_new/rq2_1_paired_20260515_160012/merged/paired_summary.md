# RQ2.1 Paired Benchmark Summary

- Topology: `chain2`
- Placement mode: `single_node`
- Placement strategy: `strict_same_node`
- Smoke mode: `False`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Execution order: `[{'pass': 1, 'order': ['mtls', 'plain']}, {'pass': 2, 'order': ['plain', 'mtls']}, {'pass': 3, 'order': ['mtls', 'plain']}, {'pass': 4, 'order': ['plain', 'mtls']}, {'pass': 5, 'order': ['mtls', 'plain']}]`

| Metric | Value |
| --- | ---: |
| RQ2.1 resource metrics complete | True |
| mTLS security validation passed | True |
| Mean latency overhead (ms) | 3.487743644001114 |
| Mean latency overhead (%) | 4.616028497678492 |
| p95 latency overhead (ms) | 3.623453250008879 |
| mTLS sidecar sample rows | 64 |
| mTLS sidecar metrics available | True |
| Sidecar CPU cost (mCPU mean) | 34.684449272126855 |
| Sidecar memory cost (MiB mean) | 82.125 |
| Total pod CPU overhead (mCPU mean) | -56.81297359313305 |
| Total pod memory overhead (MiB mean) | 93.81944444444446 |
| Service sidecar requested CPU overhead (mCPU) | 200.0 |
| Service sidecar requested memory overhead (MiB) | 256.0 |
| Scheduling delay overhead (s mean) | 0.0 |
| Schedule-to-ready overhead (s mean) | 6.300000000000001 |
| mTLS sidecar start delay (s mean) | 3.1 |
| Additional Kubernetes objects | 5 |
| Additional ServiceAccounts | 2 |
| Additional PeerAuthentications | 2 |
| Additional AuthorizationPolicies | 1 |
| Additional control-plane pods | 2 |
| Additional injected containers | 2 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean |
| --- | ---: | ---: | ---: |
| plain | 1003520.0 | 602112.0 | 401408.0 |
| mtls | 1003520.0 | 602112.0 | 401408.0 |

See `paired_summary.json`, `aggregated_results.md`, and `raw_iterations.csv` for thesis inspection.
