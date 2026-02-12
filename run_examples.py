
import time, sys, os
# Make local package visible
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
    s = 0
    model="ATM.model"
    formulas=load_formulas("examples.txt")
    for f in formulas:
        t0=time.perf_counter()
        res=timed_model_checking_etol(f, model)
        dt=time.perf_counter()-t0
        print("="*70)
        print("Formula:", f)
        print("Time(s):", round(dt,6))
        for k,v in res.items():
            print(f"{k}: {v}")
        s= s + dt                  
        print("Total time", s)