"""Quack CLI: check, ir, run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .diagnostics import QuackError
from .ir.printer import print_ir
from .parser import Parser
from .semantic import analyze
from .backends.simulator import Simulator


def _load(path: str) -> tuple[str, str]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"file not found: {path}")
    return p.read_text(encoding="utf-8"), str(p)


def cmd_check(path: str) -> int:
    source, filename = _load(path)
    try:
        program = Parser.parse_source(source, filename)
        module, diags = analyze(program, filename)
    except QuackError as e:
        print(e, file=sys.stderr)
        return 1
    for d in diags:
        print(d, file=sys.stderr)
    if diags.has_errors():
        return 1
    print(f"OK: {path}")
    return 0


def cmd_ir(path: str) -> int:
    source, filename = _load(path)
    try:
        program = Parser.parse_source(source, filename)
        module, diags = analyze(program, filename)
    except QuackError as e:
        print(e, file=sys.stderr)
        return 1
    for d in diags:
        print(d, file=sys.stderr)
    if diags.has_errors():
        return 1
    print(print_ir(module))
    return 0


def cmd_run(path: str) -> int:
    source, filename = _load(path)
    try:
        program = Parser.parse_source(source, filename)
        module, diags = analyze(program, filename)
    except QuackError as e:
        print(e, file=sys.stderr)
        return 1
    for d in diags:
        print(d, file=sys.stderr)
    if diags.has_errors():
        return 1
    sim = Simulator()
    env = sim.run(module)
    for line in sim.outputs:
        print(line)
    if not sim.outputs and env:
        for name, field in env.items():
            print(f"{name} = {field}")
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quack",
        description="Quack — field-oriented programming language",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="parse and type-check a program")
    p_check.add_argument("file")

    p_ir = sub.add_parser("ir", help="print Field IR")
    p_ir.add_argument("file")

    p_run = sub.add_parser("run", help="execute with the simulator backend")
    p_run.add_argument("file")

    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check(args.file)
    if args.command == "ir":
        return cmd_ir(args.file)
    if args.command == "run":
        return cmd_run(args.file)
    return 1


if __name__ == "__main__":
    sys.exit(main())
