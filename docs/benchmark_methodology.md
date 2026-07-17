# Benchmark Methodology Notes

This repository uses a conservative, auditable measurement contract for the
thesis-facing experiments:

- Warmup iterations are excluded from summaries.
- Each condition runs a fixed minimum warmup budget before measurement.
- When extra warmup is allowed, warmup ends only when the current trailing
  latency window is stable according to coefficient of variation (CV), or when
  the extra-iteration budget is exhausted.
- Each thesis-facing condition targets 1000 measured requests by default:
  RQ1 uses 5 rounds x 200 measured iterations; RQ2 uses 5 outer passes x 200
  measured iterations.
- Local CPU benchmark runs try to reduce environmental noise with CPU governor,
  turbo, thread-count, and priority controls. Cloud/Kubernetes runs record the
  weaker control surface in metadata rather than pretending it is identical.

## Literature Support

Kalibera and Jones argue that modern systems are non-deterministic and that
valid performance evaluation needs repeated measurements, uncertainty estimates,
and attention to which experimental level contributes variance:
https://kar.kent.ac.uk/33611/

Georges, Buytaert, and Eeckhout show that common performance evaluation methods
can be misleading without statistically rigorous treatment of non-determinism,
and they advocate measuring both startup and steady-state behavior:
https://dri.es/statistically-rigorous-java-performance-evaluation

The steady-state benchmarking literature treats warmup as data to discard before
measurement, but also warns that a fixed warmup length does not guarantee steady
state. Later work describes dynamic warmup approaches that use sliding-window
stability criteria, including CV, while also showing that such heuristics are
not perfect and should be treated as quality checks rather than proof:
https://link.springer.com/article/10.1007/s10664-022-10247-x

Google Benchmark exposes repeated benchmark runs and reports mean, median,
standard deviation, and CV for repeated measurements, which matches this repo's
decision to record repeated passes and expose CV-based stability metadata:
https://google.github.io/benchmark/user_guide.html

LLVM's benchmarking guidance recommends reducing noise by running benchmarks
multiple times and controlling OS-level sources such as CPU frequency scaling
and Turbo Boost where possible:
https://llvm.org/docs/Benchmarking.html

Mytkowicz et al. show that seemingly irrelevant experimental setup details can
introduce measurement bias, and recommend techniques such as randomization and
causal analysis. This supports keeping conditions uniform, recording metadata,
and avoiding hidden privilege or environment changes between stages:
https://sape.inf.usi.ch/publications/asplos09.html

## Caveats

The current CV readiness check is a pragmatic automation guard, not a formal
steady-state proof. A final stable window means the benchmark was recently low
variance; it does not rule out later drift, thermal effects, cloud neighbor
noise, or measurement bias. For thesis reporting, use the warmup metadata and
per-condition distribution summaries together, and treat unstable final windows
as a run-quality warning.
