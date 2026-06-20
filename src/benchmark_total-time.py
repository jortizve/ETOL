import time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from etol_model_checking import timed_model_checking_etol


def main():
    repo = Path(__file__).resolve().parent.parent
    model_dir = repo / 'models'
    models = [model_dir / 'm_200_0.model']
    sizes = [200]
    formula = 'OE(!p U p)'
    times = []
    plot_dir = repo / 'plots'
    plot_dir.mkdir(exist_ok=True)
    for path in models:
        t0 = time.perf_counter()
        timed_model_checking_etol(formula, str(path))
        times.append(time.perf_counter() - t0)
    plt.figure()
    plt.plot(sizes, times, marker='o')
    plt.xlabel('Size of the model (states)')
    plt.ylabel('Total execution time (seconds)')
    plt.tight_layout()
    plt.savefig(plot_dir / 'benchmark_total_time.pdf')
    plt.close()
    print('Wrote', plot_dir / 'benchmark_total_time.pdf')


if __name__ == '__main__':
    main()
