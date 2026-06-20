# ETOL Model-Checking Artifact

Artifact for **Execution-Time Opacity Logic: A Logic for Ensuring ET-Opacity in Timed Systems**.

This repository contains a Python prototype for checking ETOL formulas over timed automata, together with the ATM case study, synthetic scalability models, and an extended benchmark suite inspired by timed-opacity case studies from the literature.

## Repository contents

- `src/` — ETOL model checker, command-line driver, and helper scripts.
- `models/` — ATM model and synthetic ATM-size benchmark models.
- `formulas/` — ETOL formulas used for the quick check and ATM case study.
- `benchmarks/timed_opacity_literature/` — additional non-parametric ETOL benchmark translations from timed-opacity case studies.
- `scripts/run_literature_benchmarks.py` — repeated benchmark runner with average, standard deviation, min/max time, and timeout reporting.
- `results/` — expected outputs and benchmark result summaries.
- `csv/` — scalability CSV data.
- `plots/` — plots shipped with the artifact.
- `docs/` — input-format description, expected outputs, update notes, and extended benchmark documentation.
- `paper/ETOLModelChecking-AE.pdf` — submitted artifact-evaluation paper PDF.
- `LICENSE.md` — license file.

## Important artifact corrections

This version includes corrections motivated by reviewer comments:

1. the documentation no longer claims that a pre-built Docker image is included;
2. the command-line driver accepts both `--formula` and `--formula-file`;
3. blank lines and comment lines are ignored in formula files;
4. the README and documentation now describe a full evaluation workflow;
5. expected outputs are included for quick checks;
6. an extended `benchmarks/` repository is included with additional case studies beyond the ATM model;
7. the benchmark runner reports repeated runs, average time, standard deviation, min/max time, and timeout cases explicitly;
8. timeout cases are reported as `Timeout/unknown` and are not interpreted as negative results.

## Requirements

Tested with Python 3.11+.

Install dependencies with:

```bash
python3 -m pip install -r docs/requirements.txt
```

After dependency installation, no network access is required to run the packaged experiments.

## Quick check

From the repository root, run:

```bash
python3 src/run_examples.py
```

This command evaluates a small set of ETOL formulas on the ATM model.

A CLI-based quick check is:

```bash
python3 src/main.py \
  --model models/atm.model \
  --formula formulas/quick_check.etol \
  --output results/quick_check.txt \
  --json results/quick_check.json
```

Reference outputs are provided in:

- `results/quick_check_expected.txt`
- `results/quick_check_expected.json`
- `results/run_examples_expected.txt`

## ATM case study

Run:

```bash
python3 src/main.py \
  --model models/atm.model \
  --formula formulas/atm_case_study.etol \
  --output results/atm_case_study.txt \
  --json results/atm_case_study.json
```

Reference outputs are provided in:

- `results/atm_case_study_expected.txt`
- `results/atm_case_study_expected.json`

Additional ATM formulas are in:

```text
formulas/additional_formulas.etol
```

They can be run with:

```bash
python3 src/main.py \
  --model models/atm.model \
  --formula-file formulas/additional_formulas.etol \
  --output results/atm_case_additional_study.txt \
  --json results/atm_case_additional_study.json
```

## Extended timed-opacity benchmarks

To address the reviewer concern that the original evaluation used only one case study, this version includes additional benchmark models in:

```text
benchmarks/timed_opacity_literature/
```

Each benchmark directory contains:

- `model.model` — timed automaton in the artifact input format;
- `formula_main.etol` — main ETOL formula used for the benchmark table;
- `formulas.etol` — auxiliary formulas.

Run the benchmark suite with repeated executions:

```bash
python3 scripts/run_literature_benchmarks.py --repetitions 5 --timeout 10
```

For a faster smoke test:

```bash
python3 scripts/run_literature_benchmarks.py --repetitions 3 --timeout 3
```

The runner writes:

```text
results/benchmarks/etol_literature_benchmark_summary.csv
```

The CSV reports benchmark size, number of runs, completed runs, average time, standard deviation, minimum and maximum time, and ETOL verdict.

Verdicts are interpreted as follows:

- `Valid/opaque`: the ETOL formula is satisfied at the initial state;
- `False/vulnerable`: the ETOL formula is not satisfied at the initial state;
- `Timeout/unknown`: the run did not finish within the timeout, so no verdict is claimed.

See also:

- `benchmarks/README.md`
- `docs/extended_benchmarks.md`
- `docs/extended_benchmark_table.tex`

## Synthetic scalability benchmarks

The packaged synthetic models are in `models/m_*_0.model`. To reproduce the scalability CSV and plots, run:

```bash
python3 src/benchmark_total-CVS.py
python3 src/benchmark_total-time.py
python3 src/benchmark_total-Mem-time.py
```

Generated outputs are written to `csv/` and `plots/`.

## Input formats

The timed-automaton and formula formats are documented in:

- `docs/input_format.md`
- `docs/format_description.md`

## Notes for artifact evaluators

- The artifact is source-based; it does not include a pre-built Docker image.
- The extended literature benchmarks are non-parametric translations, because the current ETOL prototype checks non-parametric timed automata.
- Timeout cases are expected for some translated benchmarks and are explicitly reported as unknown.
- All commands should be run from the repository root.
