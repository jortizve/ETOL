#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, statistics, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etol_model_checking import timed_model_checking_etol

DEFAULT_MODEL = ROOT / 'models' / 'atm.model'
DEFAULT_FORMULAS = [ROOT / 'formulas' / 'atm_case_study.etol', ROOT / 'formulas' / 'additional_formulas.etol']
DEFAULT_CSV = ROOT / 'results' / 'atm_repeated' / 'atm_repeated_summary.csv'
DEFAULT_JSON = ROOT / 'results' / 'atm_repeated' / 'atm_repeated_raw.json'

def normalize_formula_text(raw: str) -> list[str]:
    formulas = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        formulas.append(ln)
    return formulas

def load_formulas(paths: list[Path]) -> list[tuple[str,str]]:
    out = []
    seen = set()
    for p in paths:
        for f in normalize_formula_text(p.read_text(encoding='utf-8')):
            key = (str(p.name), f)
            if key not in seen:
                out.append((p.name, f))
                seen.add(key)
    return out

def count_model(model_path: Path) -> tuple[int,int,int]:
    text = model_path.read_text(encoding='utf-8').splitlines()
    states=clocks=edges=0
    for i,line in enumerate(text):
        if line.strip() == 'Name_State' and i+1 < len(text): states = len(text[i+1].split())
        if line.strip() == 'Clocks' and i+1 < len(text): clocks = len(text[i+1].split())
        if line.strip() == 'Transition':
            j=i+1
            while j < len(text) and text[j].strip():
                edges += sum(1 for x in text[j].split() if x == '1')
                j += 1
    return states, clocks, edges

def verdict(result: dict) -> str:
    if isinstance(result, dict) and result.get('results'):
        initial = result['results'][0].get('initial_state','')
    else:
        initial = result.get('initial_state','') if isinstance(result,dict) else ''
    if initial.endswith('True') or ': True' in initial:
        return 'Valid/opaque'
    if initial.endswith('False') or ': False' in initial:
        return 'False/vulnerable'
    return 'Unknown'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    ap.add_argument('--formulas', type=Path, nargs='*', default=DEFAULT_FORMULAS)
    ap.add_argument('--repetitions', type=int, default=50)
    ap.add_argument('--csv', type=Path, default=DEFAULT_CSV)
    ap.add_argument('--json', type=Path, default=DEFAULT_JSON)
    args = ap.parse_args()
    formulas = load_formulas(args.formulas)
    states, clocks, edges = count_model(args.model)
    rows=[]; raw=[]
    for idx,(source, formula) in enumerate(formulas, start=1):
        times=[]; verdicts=[]; results=[]
        for rep in range(args.repetitions):
            start=time.perf_counter()
            res=timed_model_checking_etol(formula, str(args.model))
            elapsed=time.perf_counter()-start
            times.append(elapsed)
            v=verdict(res)
            verdicts.append(v)
            results.append(res)
        avg=statistics.mean(times)
        std=statistics.stdev(times) if len(times)>1 else 0.0
        row={
            'id': f'ATM-F{idx}', 'formula_source': source, 'formula': formula,
            'states': states, 'clocks': clocks, 'edges': edges,
            'runs': args.repetitions, 'completed': args.repetitions,
            'avg_s': f'{avg:.6f}', 'std_s': f'{std:.6f}', 'min_s': f'{min(times):.6f}', 'max_s': f'{max(times):.6f}',
            'verdict': max(set(verdicts), key=verdicts.count)
        }
        rows.append(row)
        raw.append({'row': row, 'times_s': times, 'verdicts': verdicts, 'last_result': results[-1]})
        print(row)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(raw, indent=2), encoding='utf-8')
    print('CSV written to', args.csv)
    print('JSON written to', args.json)
if __name__ == '__main__': main()
