# RQ2.1 mTLS Split Sensitivity Summary

- Smoke mode: `False`
- Image: `thesisrq15acr.azurecr.io/thesis-inference@sha256:d292aef407ee8a15da2bdaa680de1cc24b0975e7de81d27e1fc3a7d128b8736b`
- Mesh revision: `asm-1-29`
- Protected hop index: `2`
- Execution order: `[{'pass': 1, 'split_order': ['l3', 'l2', 'l4', 'l1'], 'security_order': ['plain', 'mtls'], 'order': ['l3_plain', 'l3_mtls', 'l2_plain', 'l2_mtls', 'l4_plain', 'l4_mtls', 'l1_plain', 'l1_mtls']}, {'pass': 2, 'split_order': ['l2', 'l4', 'l1', 'l3'], 'security_order': ['mtls', 'plain'], 'order': ['l2_mtls', 'l2_plain', 'l4_mtls', 'l4_plain', 'l1_mtls', 'l1_plain', 'l3_mtls', 'l3_plain']}, {'pass': 3, 'split_order': ['l4', 'l1', 'l3', 'l2'], 'security_order': ['plain', 'mtls'], 'order': ['l4_plain', 'l4_mtls', 'l1_plain', 'l1_mtls', 'l3_plain', 'l3_mtls', 'l2_plain', 'l2_mtls']}, {'pass': 4, 'split_order': ['l1', 'l3', 'l2', 'l4'], 'security_order': ['mtls', 'plain'], 'order': ['l1_mtls', 'l1_plain', 'l3_mtls', 'l3_plain', 'l2_mtls', 'l2_plain', 'l4_mtls', 'l4_plain']}, {'pass': 5, 'split_order': ['l3', 'l2', 'l4', 'l1'], 'security_order': ['plain', 'mtls'], 'order': ['l3_plain', 'l3_mtls', 'l2_plain', 'l2_mtls', 'l4_plain', 'l4_mtls', 'l1_plain', 'l1_mtls']}]`

## Split Deltas

| Split | Protected bytes | Plain mean ms | mTLS mean ms | Delta ms | Delta % | p95 delta ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| split_after_layer1 | 802816 | 58.751997384021706 | 63.172091544993684 | 4.420094160971978 | 7.523308751668201 | 5.359367200253473 |
| split_after_layer2 | 401408 | 59.31743288999633 | 63.00445295601049 | 3.6870200660141563 | 6.215744489232539 | 4.172184549815924 |
| split_after_layer3 | 200704 | 57.99178594000704 | 61.473175322007144 | 3.4813893820001027 | 6.003245676209433 | 3.4281442501651327 |
| split_after_layer4 | 100352 | 56.81526273099052 | 59.40124040699674 | 2.585977676006223 | 4.551554550139699 | 2.9180752503179974 |

## Notes

- Split-sensitivity results are internally comparable within this interleaved campaign.
- The protected inter-service activation for chain_2svc is reported as hop_2_activation_bytes.
- split_after_layer4 is retained as a low-payload diagnostic endpoint and remains compute-degenerate.
