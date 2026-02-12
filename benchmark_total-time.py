
import random, time, os, statistics, sys
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from etol_model_checking import timed_model_checking_etol

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

def main():
    sizes=[200,400,600,800,1000,1200, 1400, 1800, 2000]
    trials=1
    formula=[
        "j.OA(!(MAQ | MAN) U (j<=100))",
        "j.OE(!C U (E & j=100))",
        "j.OE(!cash U j>=20)",
        "j.OA(DB U j=10)",
        "j.OA(PQW -> !(MAW | MAN) U j=15)",
        "j.OE(T U (cash & j=100))",
        "j.OE(T U cash)",
        "j.OE(T U j=100)",
    ]
    times=[]
    os.makedirs("plots", exist_ok=True)
    os.makedirs("random_models", exist_ok=True)
    for n in sizes:
        tlist=[]
        for k in range(trials):
            path=f"random_models/m_{n}_{k}.model"
          #  gen_random_model(path, n, p_edge=min(0.02, 30/(n*n)), seed=1000*n+k)
            t0=time.perf_counter()
            timed_model_checking_etol(formula, path)
            tlist.append(time.perf_counter()-t0)
        times.append(statistics.mean(tlist))
    plt.figure()
    plt.plot(sizes, times, marker="o")
    plt.xlabel("Size of the model (states)")
    plt.ylabel("Total execution time (seconds)")
    plt.savefig("plots/benchmark_total.pdf")
    plt.close()
    print("Wrote plots/benchmark_total.pdf")

if __name__=="__main__":
    main()
