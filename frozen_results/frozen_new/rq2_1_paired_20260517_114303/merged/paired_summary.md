# RQ2.1 Paired Benchmark Summary

- Topology: `chain5`
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
| Mean latency overhead (ms) | 8.836795603000866 |
| Mean latency overhead (%) | 10.736990731572252 |
| p95 latency overhead (ms) | 8.982682349972038 |
| mTLS sidecar sample rows | 175 |
| mTLS sidecar metrics available | True |
| Sidecar CPU cost (mCPU mean) | 87.60210778563598 |
| Sidecar memory cost (MiB mean) | 223.71428571428572 |
| Total pod CPU overhead (mCPU mean) | 37.48977333121957 |
| Total pod memory overhead (MiB mean) | 264.1428571428571 |
| Service sidecar requested CPU overhead (mCPU) | 500.0 |
| Service sidecar requested memory overhead (MiB) | 640.0 |
| Scheduling delay overhead (s mean) | 0.0 |
| Schedule-to-ready overhead (s mean) | 6.839999999999999 |
| mTLS sidecar start delay (s mean) | 2.1599999999999997 |
| Additional Kubernetes objects | 14 |
| Additional ServiceAccounts | 5 |
| Additional PeerAuthentications | 5 |
| Additional AuthorizationPolicies | 4 |
| Additional control-plane pods | 2 |
| Additional injected containers | 5 |

## Activation Sanity

| Condition | Total activation bytes mean | Hop 1 bytes mean | Hop 2 bytes mean | Hop 3 bytes mean | Hop 4 bytes mean | Hop 5 bytes mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |
| mtls | 2107392.0 | 602112.0 | 802816.0 | 401408.0 | 200704.0 | 100352.0 |

See `paired_summary.json`, `aggregated_results.md`, and `raw_iterations.csv` for thesis inspection.
