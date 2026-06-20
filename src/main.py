#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict

from etol_model_checking import timed_model_checking_etol


@dataclass
class CheckResult:
    model: str
    formula_source: str
    result: dict
    runtime_seconds: float
    message: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETOL model checker over timed automata.")
    parser.add_argument("--model", required=True, help="Path to the input timed automaton model.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--formula", help="Path to a formula file or a literal ETOL formula.")
    group.add_argument("--formula-file", dest="formula_file", help="Path to a formula file. Alias for artifact evaluators.")
    parser.add_argument("--output", required=True, help="Path to the human-readable output file.")
    parser.add_argument("--json", required=False, help="Optional path to a JSON output file.")
    return parser.parse_args()


def validate_inputs(model_path: Path) -> None:
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")


def _normalize_formula_text(raw: str) -> str:
    lines = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        lines.append(ln)
    return "\n".join(lines)


def load_formula_input(formula_arg: str) -> tuple[str, str]:
    p = Path(formula_arg)
    if p.is_file():
        return _normalize_formula_text(p.read_text(encoding="utf-8")), str(p)
    return _normalize_formula_text(formula_arg), "literal"


def write_text_output(output_path: Path, check: CheckResult) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"Model: {check.model}",
        f"Formula source: {check.formula_source}",
        f"Time: {check.runtime_seconds:.6f}s",
        f"Message: {check.message}",
        "Result:",
        json.dumps(check.result, indent=2),
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json_output(json_path: Path, check: CheckResult) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(asdict(check), indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)
    output_path = Path(args.output)
    json_path = Path(args.json) if args.json else None
    try:
        validate_inputs(model_path)
        formula_input = args.formula_file if args.formula_file else args.formula
        formulas, formula_source = load_formula_input(formula_input)
        start = time.perf_counter()
        result = timed_model_checking_etol(formulas, str(model_path))
        elapsed = time.perf_counter() - start
        check = CheckResult(
            model=str(model_path),
            formula_source=formula_source,
            result=result,
            runtime_seconds=elapsed,
            message="Model checking completed successfully.",
        )
        write_text_output(output_path, check)
        if json_path is not None:
            write_json_output(json_path, check)
        print("Result written to", output_path)
        return 0
    except Exception as exc:
        check = CheckResult(
            model=str(model_path),
            formula_source=args.formula_file if args.formula_file else args.formula,
            result={"status": "ERROR"},
            runtime_seconds=0.0,
            message=str(exc),
        )
        try:
            write_text_output(output_path, check)
            if json_path is not None:
                write_json_output(json_path, check)
        except Exception:
            pass
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
