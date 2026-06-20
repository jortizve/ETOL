# Benchmarks

This directory contains the benchmark inputs used for the extended ETOL artifact evaluation.

## `timed_opacity_literature/`

These benchmarks are non-parametric ETOL translations of timed-opacity case studies inspired by the experimental suite of André, Lime, Marinho, and Sun (ToSEM 2022 / arXiv:2206.05438v1). They complement the ATM case study and are intended to answer the artifact-review concern that the original evaluation used only a single case study.

Each benchmark directory contains:

- `model.model`: timed automaton in the artifact input format;
- `formula_main.etol`: main ETOL opacity formula used by the benchmark runner;
- `formulas.etol`: auxiliary formulas, usually including existential and universal variants.

The main formula checks execution-time indistinguishability between runs satisfying the `secret` proposition and runs reaching the `final` proposition. The translations are intentionally non-parametric: parameters from the original IMITATOR/PTA benchmarks are instantiated or removed so that they can be handled by the current ETOL prototype.

## Running the benchmark suite

From the repository root:

```bash
python3 scripts/run_literature_benchmarks.py --repetitions 5 --timeout 10
```

The script writes a CSV summary to:

```text
results/benchmarks/etol_literature_benchmark_summary.csv
```

The CSV includes the number of states, clocks, edges, repeated runs, completed runs, average time, standard deviation, minimum time, maximum time, and ETOL verdict.

## Verdicts

- `Valid/opaque`: the ETOL formula is satisfied at the initial state.
- `False/vulnerable`: the ETOL formula is not satisfied at the initial state.
- `Timeout/unknown`: the run did not finish within the timeout; no correctness verdict is claimed.

Timeouts are reported explicitly rather than interpreted as negative results.
