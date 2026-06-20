from GeneratorATM import gen_big_atm_model

def main():
    sizes=[500, 1000, 2000, 4000, 8000]   # estados aprox (depende de modules*module_size)
    trials=3
    formulas = [
        "j.OA(!(MAQ | MAN) U (j<=100))",
        "j.OE(!C U (E & j=100))",
        "j.OE(!cash U j>=20)",
        "j.OA(DB U j=10)",
        "j.OA(PQW -> !(MAW | MAN) U j>=15)",
        "j.OE(T U (cash & j=100))",
        "j.OE(T U cash)",
        "j.OE(T U j=100)",
    ]

    import os, time, statistics
    import matplotlib.pyplot as plt
    os.makedirs("plots", exist_ok=True)
    os.makedirs("atm_models", exist_ok=True)

    for formula in formulas:
        times=[]
        actual_sizes=[]
        for target in sizes:
            # convierte "target" a #módulos: n ≈ 16 + modules*module_size
            module_size = 12
            modules = max(1, (target - 16)//module_size)

            tlist=[]
            for k in range(trials):
                path=f"big_atm_{target}_{k}.model"
                gen_big_atm_model(path, modules=modules, module_size=module_size,
                                  noise_edges=int(0.2*target), seed=1000*target+k)

                t0=time.perf_counter()
                etol_model_checking(formula, path)
                tlist.append(time.perf_counter()-t0)

            times.append(statistics.mean(tlist))
            actual_sizes.append(16 + modules*module_size)

        plt.figure()
        plt.plot(actual_sizes, times, marker="o")
        plt.xlabel("Size of the model (states)")
        plt.ylabel("Total execution time (seconds)")
        safe = formula.replace(" ", "").replace("|","OR").replace("&","AND").replace("!","NOT").replace(">","GT").replace("<","LT").replace("=","EQ")
        plt.savefig(f"plots/benchmark_{safe}.pdf")
        plt.close()
        print(f"Wrote plots/benchmark_{safe}.pdf")