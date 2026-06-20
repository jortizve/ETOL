import time, platform, tracemalloc
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    import resource
except ImportError:
    resource = None
from etol_model_checking import timed_model_checking_etol


def _ru_maxrss_mib() -> float:
    if resource is None:
        return float('nan')
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / (1024.0 * 1024.0) if platform.system().lower() == 'darwin' else r / 1024.0


def run_and_measure(formula, path):
    tracemalloc.start()
    rss_before = _ru_maxrss_mib()
    t0 = time.perf_counter()
    timed_model_checking_etol(formula, str(path))
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, max(rss_before, _ru_maxrss_mib()), peak / (1024.0 * 1024.0)


def main():
    repo = Path(__file__).resolve().parent.parent
    model_dir = repo / 'models'
    models = [model_dir / 'm_200_0.model']
    sizes = [200]
    formula = 'OE(!p U p)'
    peak_rss = []
    peak_py = []
    plot_dir = repo / 'plots'
    plot_dir.mkdir(exist_ok=True)
    for path in models:
        _, rss_mib, py_mib = run_and_measure(formula, path)
        peak_rss.append(rss_mib)
        peak_py.append(py_mib)
    plt.figure(); plt.plot(sizes, peak_rss, marker='o'); plt.xlabel('Size of the model (states)'); plt.ylabel('Peak memory RSS (MiB)'); plt.tight_layout(); plt.savefig(plot_dir / 'benchmark_peak_rss.pdf'); plt.close()
    plt.figure(); plt.plot(sizes, peak_py, marker='o'); plt.xlabel('Size of the model (states)'); plt.ylabel('Peak Python allocated memory (MiB)'); plt.tight_layout(); plt.savefig(plot_dir / 'benchmark_peak_python.pdf'); plt.close()
    print('Wrote', plot_dir / 'benchmark_peak_rss.pdf')
    print('Wrote', plot_dir / 'benchmark_peak_python.pdf')


if __name__ == '__main__':
    main()
