# Expected outputs

## Quick check (`python3 src/run_examples.py`)
The script prints one block per formula. A successful run should produce the following final truth values for the packaged ATM example set:

- `OE((T & !cash) U cash)` -> `Initial state I: False`
- `j.OA(!(MAQ | MAN) U (E & j<=100))` -> `Initial state I: False`
- `OE(!cash U j.(cash & j<=20))` -> `Initial state I: False`
- `OA((PQW & x<=15) U j.(cash & j<=5))` -> `Initial state I: False`
- `j1.((!C & j1<=100) & j2.OE(correctPwd U (cash & j2<=30)))` -> `Initial state I: False`
- `OA(!cash U j.(E & j=10))` -> `Initial state I: False`

A reference run is stored in `results/run_examples_expected.txt`.


### 1. ATM case study

Run:

```bash
python3 src/main.py   --model models/atm.model   --formula formulas/atm_case_study.etol   --output results/atm_case_study.txt   --json results/atm_case_study.json
```

This command should terminate successfully and create:
- `results/atm_case_study.txt`
- `results/atm_case_study.json`

Reference outputs are included in:
- `results/atm_case_study_expected.txt`
- `results/atm_case_study_expected.json`


## Additional formulas for evaluation

The artifact also includes an additional set of ETOL formulas that can be used for supplementary checks on the ATM case study.

File:
- `formulas/additional_formulas.etol`

Example usage:
```bash
python3 src/main.py  --model models/atm.model  --formula-file formulas/additional_formulas.etol  --output results/atm_case_addittional_study.txt   --json results/atm_case_addittional_study.json


## CLI ATM case study
This command should terminate successfully and create both a text file and a JSON file in `results/`.
Reference outputs are stored in:
- `results/atm_case_study_expected.txt`
- `results/atm_case_study_expected.json`

## Benchmark scripts
Successful runs create the following files:
- `plots/benchmark_total_time.pdf`
- `plots/benchmark_peak_rss.pdf`
- `plots/benchmark_peak_python.pdf`
- `csv/benchmark_time_mem_zones.csv` (for `benchmark_total-CVS.py`)

## Extended benchmarks

The extended benchmark runner creates a CSV file:

```text
results/benchmarks/etol_literature_benchmark_summary.csv
```

The exact times depend on the machine. Evaluators should check that terminating benchmarks receive a verdict (`Valid/opaque` or `False/vulnerable`) and that timeout cases are reported as `Timeout/unknown` rather than being interpreted as failures of the property.
