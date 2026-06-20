# Extended ETOL benchmark evaluation

## Motivation

The original artifact focused mainly on the ATM case study and synthetic ATM-size variants. To make the empirical evaluation more convincing, this version adds an independent benchmark suite with case studies inspired by the timed-opacity literature and STAC timing-leak examples.

The goal is not to claim that all original parametric benchmarks are reproduced exactly. The current ETOL prototype checks non-parametric timed automata. Therefore, the benchmarks in `benchmarks/timed_opacity_literature/` are non-parametric translations or simplifications of the corresponding timed-opacity case studies.

## How to reproduce

Install dependencies:

```bash
python3 -m pip install -r docs/requirements.txt
```

Run the extended benchmarks:

```bash
python3 scripts/run_literature_benchmarks.py --repetitions 5 --timeout 10
```

For faster artifact smoke testing, use:

```bash
python3 scripts/run_literature_benchmarks.py --repetitions 3 --timeout 3
```

## Measurement protocol

For each benchmark, the runner performs repeated executions and records:

- number of completed runs;
- average execution time;
- standard deviation;
- minimum and maximum time;
- timeout cases;
- ETOL verdict.

This directly addresses measurement-noise concerns raised by reviewers. Timeout cases are not counted as valid or invalid verdicts.

## Interpretation

The `Valid/opaque` verdict means that the translated ETOL formula is true at the initial state. The `False/vulnerable` verdict means that the formula is false at the initial state. The `Timeout/unknown` verdict means that the prototype did not finish within the selected timeout.

The current suite is useful for evaluating robustness beyond the ATM example. Some larger translated examples still time out; this is reported as an implementation limitation and a target for future optimization.
