# Experiment map

## 1. Quick check
### Command
`python3 src/run_examples.py`

### Inputs
- `src/ATM.model`
- `src/examples.txt`

### Expected result
A successful run prints one block per formula. The reference output is stored in `results/run_examples_expected.txt`.

## 2. CLI quick check
### Command
`python3 src/main.py --model models/atm.model --formula formulas/quick_check.etol --output results/quick_check.txt --json results/quick_check.json`

### Expected output files
- `results/quick_check.txt`
- `results/quick_check.json`

## 3. ATM case study
### Command
`python3 src/main.py --model models/atm.model --formula formulas/atm_case_study.etol --output results/atm_case_study.txt --json results/atm_case_study.json`

### Reference outputs
- `results/atm_case_study_expected.txt`
- `results/atm_case_study_expected.json`

## 4. Benchmark time plot
### Command
`python3 src/benchmark_total-time.py`

### Output
- `plots/benchmark_total_time.pdf`

## 5. Benchmark memory plots
### Command
`python3 src/benchmark_total-Mem-time.py`

### Outputs
- `plots/benchmark_peak_rss.pdf`
- `plots/benchmark_peak_python.pdf`

## 6. CSV benchmark summary
### Command
`python3 src/benchmark_total-CVS.py`

### Outputs
- `csv/benchmark_time_mem_zones.csv`
- `plots/benchmark_time.pdf`
- `plots/benchmark_peak_rss.pdf`
- `plots/benchmark_peak_python.pdf`
