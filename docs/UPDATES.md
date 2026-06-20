# Artifact updates

This artifact version includes the following reviewer-facing corrections.

## Documentation and execution

- Removed the incorrect statement that a pre-built Docker image is included.
- Corrected the paper path in the README.
- Added clear quick-check and full case-study commands.
- Added `--formula-file` as an alias for formula-file based execution.
- Kept `--formula` for backward compatibility with literal formulas and file paths.
- Formula loading now ignores blank lines and lines starting with `#`.

## Benchmarks

- Added `benchmarks/timed_opacity_literature/` with additional non-parametric ETOL benchmarks inspired by timed-opacity case studies from the literature.
- Added `scripts/run_literature_benchmarks.py`, which performs repeated runs and reports average time, standard deviation, minimum/maximum time, completed runs, and timeouts.
- Added `docs/extended_benchmarks.md` and `docs/extended_benchmark_table.tex` to explain the new evaluation and provide a LaTeX table template.
- Added `results/benchmarks/etol_literature_benchmark_summary.csv` as a prepared summary from the artifact-preparation environment.

## Interpretation of results

- `Valid/opaque` means that the translated ETOL formula holds at the initial state.
- `False/vulnerable` means that the translated ETOL formula does not hold at the initial state.
- `Timeout/unknown` means that the benchmark did not finish under the selected timeout; no correctness verdict is claimed.

These changes address reviewer concerns about limited experiments, missing repeated-run statistics, and lack of clarity about timeout and vulnerability verdicts.
