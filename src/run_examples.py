import time, sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from etol_model_checking import timed_model_checking_etol

def load_formulas(path):
    fs=[]
    with open(path,'r',encoding='utf-8') as f:
        for ln in f:
            ln=ln.strip()
            if not ln or ln.startswith('#'):
                continue
            fs.append(ln)
    return fs

if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    model = str((base.parent / 'models' / 'atm.model').resolve())
    formulas = load_formulas(base / 'examples.txt')
    total = 0.0
    for f in formulas:
        t0=time.perf_counter()
        res=timed_model_checking_etol(f, model)
        dt=time.perf_counter()-t0
        print("="*70)
        print("Formula:", f)
        print("Time(s):", round(dt,6))
        for k,v in res.items():
            print(f"{k}: {v}")
        total += dt
        print("Total accumulated time", round(total, 6))
