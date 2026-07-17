# RQ2.1b Paired Benchmark Summary

- Topology: `chain2`
- Placement mode: `multi_node`
- Placement strategy: `multi_node_anti_affinity`
- Smoke mode: `False`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Execution order: `[{'pass': 1, 'order': ['mtls', 'plain']}, {'pass': 2, 'order': ['plain', 'mtls']}, {'pass': 3, 'order': ['mtls', 'plain']}, {'pass': 4, 'order': ['plain', 'mtls']}, {'pass': 5, 'order': ['mtls', 'plain']}]`

| Metric | Value |
| --- | ---: |
| RQ2.1 resource metrics complete | True |
| mTLS security validation passed | True |
| Mean latency overhead (ms) | 2.711704127994153 |
| Mean latency overhead (%) | 3.9034471214084863 |
| p95 latency overhead (ms) | 2.692163449751206 |
| mTLS sidecar sample rows | 60 |
| mTLS sidecar metrics available | True |
| Sidecar CPU cost (mCPU mean) | 35.382011353929336 |
| Sidecar memory cost (MiB mean) | 83.4 |
| Total pod CPU overhead (mCPU mean) | 100.25148844887127 |
| Total pod memory overhead (MiB mean) | 99.10769230769228 |
| Service sidecar requested CPU overhead (mCPU) | 200.0 |
| Service sidecar requested memory overhead (MiB) | 256.0 |
| Scheduling delay overhead (s mean) | 0.0 |
| Schedule-to-ready overhead (s mean) | 7.8 |
| mTLS sidecar start delay (s mean) | 2.6 |
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
