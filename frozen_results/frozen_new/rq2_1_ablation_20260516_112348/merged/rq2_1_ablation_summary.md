# RQ2.1 Ablation Summary

- Smoke mode: `False`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Execution order: `[{'pass': 1, 'order': ['c2', 'c1', 'c3', 'c0']}, {'pass': 2, 'order': ['c1', 'c3', 'c0', 'c2']}, {'pass': 3, 'order': ['c3', 'c0', 'c2', 'c1']}, {'pass': 4, 'order': ['c0', 'c2', 'c1', 'c3']}, {'pass': 5, 'order': ['c2', 'c1', 'c3', 'c0']}]`

## Latency By Condition

| Condition | Mean ms | p95 ms | Non-compute mean ms |
| --- | ---: | ---: | ---: |
| c0 | 69.90069103400106 | 72.59065940003211 | 4.195945547998917 |
| c1 | 72.46961707099922 | 74.38040410002031 | 7.165405327008102 |
| c2 | 72.78449932900435 | 75.31073824992518 | 7.181504002012161 |
| c3 | 72.74026514400362 | 75.13340789990934 | 7.195083034001755 |

## Adjacent Deltas

| Delta | Mean ms | Mean % | p95 ms |
| --- | ---: | ---: | ---: |
| c1_minus_c0 | 2.568926036998164 | 3.6751082128052044 | 1.789744699988205 |
| c2_minus_c1 | 0.31488225800512737 | 0.4345024449303134 | 0.9303341499048656 |
| c3_minus_c2 | -0.044234185000732396 | -0.06077418325127537 | -0.1773303500158363 |
| c3_minus_c0 | 2.839574110002559 | 4.062297622524698 | 2.5427484998772343 |

## Notes

- Ablation results are internally comparable within this interleaved campaign.
- Do not numerically splice these deltas into the frozen two-condition RQ2.1 result.
- C1 is mesh-default sidecar/auto-mTLS/no-AuthZ, not a proven plaintext sidecar-only condition.
