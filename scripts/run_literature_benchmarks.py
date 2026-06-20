#!/usr/bin/env python3
"""Run the extended ETOL literature benchmark suite.

The script executes each benchmark several times, reports average/min/max/std
runtime, and writes a CSV summary. Timeout cases are explicitly marked as
`Timeout/unknown` and are not counted as valid or invalid results.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = ROOT / "benchmarks" / "timed_opacity_literature"
DEFAULT_OUT = ROOT / "results" / "benchmarks" / "etol_literature_benchmark_summary.csv"


def run_with_timeout(cmd: list[str], timeout_s: float, cwd: Path) -> tuple[str, float, str, str]:
    start = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        elapsed = time.perf_counter() - start
        if proc.returncode == 0:
            return "ok", elapsed, stdout, stderr
        return "error", elapsed, stdout, stderr
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return "timeout", time.perf_counter() - start, "", f"timeout after {timeout_s}s"


def verdict_from_json(json_path: Path) -> str:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    result = data.get("result", {})
    initial = ""
    if isinstance(result, dict) and result.get("results"):
        initial = result["results"][0].get("initial_state", "")
    elif isinstance(result, dict):
        initial = result.get("initial_state", "")
    if initial.endswith("True") or ": True" in initial:
        return "Valid/opaque"
    if initial.endswith("False") or ": False" in initial:
        return "False/vulnerable"
    return "Unknown"


def count_model(model_path: Path) -> tuple[int, int, int]:
    text = model_path.read_text(encoding="utf-8").splitlines()
    states = clocks = edges = 0
    for i, line in enumerate(text):
        if line.strip() == "Name_State" and i + 1 < len(text):
            states = len(text[i + 1].split())
        if line.strip() == "Clocks" and i + 1 < len(text):
            clocks = len(text[i + 1].split())
        if line.strip() == "Transition":
            j = i + 1
            while j < len(text) and text[j].strip():
                edges += sum(1 for x in text[j].split() if x == "1")
                j += 1
    return states, clocks, edges


def run_benchmarks(repetitions: int, timeout_s: float, out_csv: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for bench in sorted(p for p in BENCH_ROOT.iterdir() if p.is_dir()):
        model = bench / "model.model"
        formula = bench / "formula_main.etol"
        states, clocks, edges = count_model(model)
        times: list[float] = []
        verdicts: list[str] = []
        statuses: list[str] = []
        out_dir = ROOT / "results" / "benchmarks" / bench.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for rep in range(repetitions):
            txt = out_dir / f"run_{rep}.txt"
            js = out_dir / f"run_{rep}.json"
            cmd = [
                sys.executable,
                "src/main.py",
                "--model", str(model),
                "--formula", str(formula),
                "--output", str(txt),
                "--json", str(js),
            ]
            status, wall, stdout, stderr = run_with_timeout(cmd, timeout_s, ROOT)
            statuses.append(status)
            if status == "ok" and js.exists():
                data = json.loads(js.read_text(encoding="utf-8"))
                times.append(float(data.get("runtime_seconds", wall)))
                verdicts.append(verdict_from_json(js))
            elif status == "timeout":
                txt.write_text(f"TIMEOUT after {timeout_s}s\n", encoding="utf-8")
                verdicts.append("Timeout/unknown")
            else:
                txt.write_text(stdout + "\n" + stderr, encoding="utf-8")
                verdicts.append("Error")
        if times:
            avg = statistics.mean(times)
            std = statistics.stdev(times) if len(times) > 1 else 0.0
            verdict = max(set(verdicts), key=verdicts.count)
            row = {
                "benchmark": bench.name,
                "states": str(states),
                "clocks": str(clocks),
                "edges": str(edges),
                "runs": str(repetitions),
                "completed": str(len(times)),
                "avg_s": f"{avg:.6f}",
                "std_s": f"{std:.6f}",
                "min_s": f"{min(times):.6f}",
                "max_s": f"{max(times):.6f}",
                "verdict": verdict,
                "status": ";".join(statuses),
            }
        else:
            row = {
                "benchmark": bench.name,
                "states": str(states),
                "clocks": str(clocks),
                "edges": str(edges),
                "runs": str(repetitions),
                "completed": "0",
                "avg_s": "timeout",
                "std_s": "--",
                "min_s": "--",
                "max_s": "--",
                "verdict": "Timeout/unknown",
                "status": ";".join(statuses),
            }
        rows.append(row)
        print(row)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run extended ETOL timed-opacity benchmarks.")
    parser.add_argument("--repetitions", type=int, default=5, help="Number of repeated runs per benchmark.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout per run in seconds.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="CSV output path.")
    args = parser.parse_args()
    run_benchmarks(args.repetitions, args.timeout, args.output)
    print(f"Summary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
