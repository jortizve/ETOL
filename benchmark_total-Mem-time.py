import random, time, os, statistics, sys, platform
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from etol_model_checking import timed_model_checking_etol

# --------- Memory tools ----------
import tracemalloc
try:
    import resource
except ImportError:
    resource = None


def _ru_maxrss_mib() -> float:
    """
    Peak RSS in MiB using resource.getrusage.
    - Linux: ru_maxrss is in KB
    - macOS: ru_maxrss is in bytes
    """
    if resource is None:
        return float("nan")

    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    sysname = platform.system().lower()
    if "darwin" in sysname:  # macOS
        return r / (1024.0 * 1024.0)
    else:  # Linux, typically KB
        return r / 1024.0


def gen_random_model(path, n, p_edge=0.02, seed=0):
    rng=random.Random(seed)
    states=[f"s{i}" for i in range(n)]
    mat=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i!=j and rng.random()<p_edge:
                mat[i][j]=1
    for i in range(n-1):
        mat[i][i+1]=1

    props=["p"]
    lab=[[1 if (i==n-1) else 0] for i in range(n)]

    clocks="x y"
    cc=[]
    for i in range(n):
        row=[]
        for j in range(n):
            if mat[i][j]==1:
                row.append("x=1")
            else:
                row.append("0")
        cc.append(" ".join(row))
    inv=["0 0" for _ in range(n)]

    with open(path,'w',encoding='utf-8') as f:
        f.write("Transition\n")
        for i in range(n):
            f.write(" ".join(str(mat[i][j]) for j in range(n))+"\n")
        f.write("\nName_State\n")
        f.write(" ".join(states)+"\n\n")
        f.write("Initial_State\n")
        f.write(states[0]+"\n\n")
        f.write("Atomic_propositions\n")
        f.write(" ".join(props)+"\n\n")
        f.write("Labelling\n")
        for i in range(n):
            f.write(" ".join(str(x) for x in lab[i])+"\n")
        f.write("\nNumber_of_agents\n1\n\n")
        f.write("Clocks\n")
        f.write(clocks+"\n\n")
        f.write("Clock_constraints\n")
        for line in cc:
            f.write(line+"\n")
        f.write("\nInvariants\n")
        for line in inv:
            f.write(line+"\n")


def run_and_measure(formulas, path):
    """
    Returns (elapsed_seconds, peak_rss_mib, peak_tracemalloc_mib)
    """
    # Start tracemalloc for Python-level peak
    tracemalloc.start()
    rss_before = _ru_maxrss_mib()

    t0 = time.perf_counter()
    timed_model_checking_etol(formulas, path)
    elapsed = time.perf_counter() - t0

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_tracemalloc_mib = peak / (1024.0 * 1024.0)

    # ru_maxrss is already a peak for the process lifetime, but we still read it after run.
    rss_after = _ru_maxrss_mib()
    peak_rss_mib = max(rss_before, rss_after)

    return elapsed, peak_rss_mib, peak_tracemalloc_mib


def main():
    sizes=[200,400,600,800,1000,1200,1400,1800,2000]
    trials=1

    formulas=[
        "j.OA(!(MAQ | MAN) U (j<=100))",
        "j.OE(!C U (E & j=100))",
        "j.OE(!cash U j>=20)",
        "j.OA(DB U j=10)",
        "j.OA(PQW -> !(MAW | MAN) U j=15)",
        "j.OE(T U (cash & j=100))",
        "j.OE(T U cash)",
        "j.OE(T U j=100)",
        "OE(T U cash)",
        "j.OA(!(MAQ | MAN) U (E & j<=100))", 
        "OE(T U j.(takeCash & j <= 20))",
        "OA((PQW & x<= 15) U j.(takeCash & j<= 5))", 
        "x.((!C & x <= 100) & j.OE(correctPwd U (takeCash & j <= 30)))", 
        "OA(!takeCash U j.(E & j =10))"
    ]

    times=[]
    peak_rss=[]
    peak_py=[]

    os.makedirs("plots", exist_ok=True)
    os.makedirs("random_models", exist_ok=True)

    for n in sizes:
        tlist=[]
        rss_list=[]
        py_list=[]
        for k in range(trials):
            path=f"random_models/m_{n}_{k}.model"

            # OJO: si realmente usas ATM grandes, aquí llama a tu gen_big_atm_model_by_size(...)
            # gen_random_model(path, n, p_edge=min(0.02, 30/(n*n)), seed=1000*n+k)

            elapsed, rss_mib, py_mib = run_and_measure(formulas, path)
            tlist.append(elapsed)
            rss_list.append(rss_mib)
            py_list.append(py_mib)

        times.append(statistics.mean(tlist))
        peak_rss.append(statistics.mean(rss_list))
        peak_py.append(statistics.mean(py_list))

        print(f"n={n}  time={times[-1]:.3f}s  peakRSS={peak_rss[-1]:.1f}MiB  peakPy={peak_py[-1]:.1f}MiB")

    # Plot time
    plt.figure()
    plt.plot(sizes, times, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Total execution time (seconds)")
    plt.savefig("plots/benchmark_total_time.pdf")
    plt.close()

    # Plot peak RSS memory
    plt.figure()
    plt.plot(sizes, peak_rss, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Peak memory RSS (MiB)")
    plt.savefig("plots/benchmark_peak_rss.pdf")
    plt.close()

    # Plot peak Python allocations (optional)
    plt.figure()
    plt.plot(sizes, peak_py, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Peak Python allocated memory (MiB)")
    plt.savefig("plots/benchmark_peak_python.pdf")
    plt.close()

    print("Wrote plots/benchmark_total_time.pdf")
    print("Wrote plots/benchmark_peak_rss.pdf")
    print("Wrote plots/benchmark_peak_python.pdf")


if __name__=="__main__":
    main()
