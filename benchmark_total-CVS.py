import random, time, os, statistics, sys, platform, csv
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

# IMPORTANTE: si tu módulo se llama distinto, ajusta aquí
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
    else:  # Linux: KB
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
            row.append("x=1" if mat[i][j]==1 else "0")
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


# ---------------- Zones extraction helpers ----------------
def _extract_zones_count(result_obj):
    """
    Try to extract 'zones explored' count from different possible returns.
    Works if timed_model_checking_etol returns a dict with a key,
    or returns a richer object, etc.
    Returns int or -1 if not found.
    """
    # Case 1: dict with explicit field
    if isinstance(result_obj, dict):
        for key in ("zones", "zones_explored", "zone_count", "explored_zones"):
            if key in result_obj and isinstance(result_obj[key], int):
                return result_obj[key]

    # Case 2: object attributes
    for attr in ("zones", "zones_explored", "zone_count", "explored_zones"):
        if hasattr(result_obj, attr):
            v = getattr(result_obj, attr)
            if isinstance(v, int):
                return v

    return -1


def run_and_measure(formulas, path):
    """
    Returns (elapsed_seconds, peak_rss_mib, peak_tracemalloc_mib, zones_count)
    """
    tracemalloc.start()
    rss_before = _ru_maxrss_mib()

    t0 = time.perf_counter()
    result = timed_model_checking_etol(formulas, path)
    elapsed = time.perf_counter() - t0

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_py_mib = peak / (1024.0 * 1024.0)
    rss_after = _ru_maxrss_mib()
    peak_rss_mib = max(rss_before, rss_after)

    zones = _extract_zones_count(result)

    return elapsed, peak_rss_mib, peak_py_mib, zones, result


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

    os.makedirs("plots", exist_ok=True)
    os.makedirs("random_models", exist_ok=True)
    os.makedirs("csv", exist_ok=True)

    # Per-size aggregates
    avg_time=[]
    avg_rss=[]
    avg_py=[]
    avg_zones=[]

    csv_rows = []
    csv_path = "csv/benchmark_time_mem_zones.csv"

    for n in sizes:
        tlist=[]
        rss_list=[]
        py_list=[]
        zones_list=[]

        for k in range(trials):
            path=f"random_models/m_{n}_{k}.model"

            # Generación (elige la que uses realmente)
            # gen_random_model(path, n, p_edge=min(0.02, 30/(n*n)), seed=1000*n+k)

            elapsed, rss_mib, py_mib, zones, _ = run_and_measure(formulas, path)

            tlist.append(elapsed)
            rss_list.append(rss_mib)
            py_list.append(py_mib)
            zones_list.append(zones if zones >= 0 else float("nan"))

            csv_rows.append({
                "size": n,
                "trial": k,
                "time_s": elapsed,
                "peak_rss_mib": rss_mib,
                "peak_py_mib": py_mib,
                "zones": zones,
                "model_path": path,
            })

        avg_time.append(statistics.mean(tlist))
        avg_rss.append(statistics.mean(rss_list))
        avg_py.append(statistics.mean(py_list))

        # zones: si no existe (=-1), el promedio se vuelve nan
        z_clean = [z for z in zones_list if isinstance(z, (int,float)) and z == z]  # filter nan
        avg_zones.append(statistics.mean(z_clean) if z_clean else float("nan"))

        print(f"n={n}  time={avg_time[-1]:.3f}s  peakRSS={avg_rss[-1]:.1f}MiB  peakPy={avg_py[-1]:.1f}MiB  zones={avg_zones[-1]}")

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["size","trial","time_s","peak_rss_mib","peak_py_mib","zones","model_path"])
        w.writeheader()
        for row in csv_rows:
            w.writerow(row)
    print(f"Wrote {csv_path}")

    # Plot time
    plt.figure()
    plt.plot(sizes, avg_time, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Average execution time (seconds)")
    plt.savefig("plots/benchmark_time.pdf")
    plt.close()

    # Plot peak RSS
    plt.figure()
    plt.plot(sizes, avg_rss, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Average peak RSS (MiB)")
    plt.savefig("plots/benchmark_peak_rss.pdf")
    plt.close()

    # Plot peak Python allocations
    plt.figure()
    plt.plot(sizes, avg_py, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Average peak Python allocated memory (MiB)")
    plt.savefig("plots/benchmark_peak_python.pdf")
    plt.close()

    # Plot zones (only if available)
    if any((z == z) for z in avg_zones):  # any non-nan
        plt.figure()
        plt.plot(sizes, avg_zones, marker="o")
        plt.xlabel("Size of the model (states)")
        plt.ylabel("Average explored zones")
        plt.savefig("plots/benchmark_zones.pdf")
        plt.close()
        print("Wrote plots/benchmark_zones.pdf")
    else:
        print("Zones count not available (zones=-1). Skipping zones plot.")

    print("Wrote plots/benchmark_time.pdf")
    print("Wrote plots/benchmark_peak_rss.pdf")
    print("Wrote plots/benchmark_peak_python.pdf")


if __name__=="__main__":
    main()
