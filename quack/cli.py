"""Quack CLI: check, ir, run, babelcodec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

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


def cmd_babelcodec_health() -> int:
    from .integrations.babelcodec import BabelCodecClient, BabelCodecError

    try:
        client = BabelCodecClient()
        result = client.health()
    except BabelCodecError as e:
        print(json.dumps({
            "contract": "quack.babelcodec.v1",
            "status": "unavailable",
            "error": {"code": e.code, "message": str(e)},
        }, indent=2))
        return 1
    print(json.dumps({
        "contract": "quack.babelcodec.v1",
        "status": "ok",
        "health": result,
    }, indent=2))
    return 0


def cmd_babelcodec_validate_field(path: str, field_name: str) -> int:
    from .integrations.babelcodec import (
        BabelCodecClient, BabelCodecError, field_to_feature, FieldFeatureError,
    )
    from .integrations.babelcodec.protocol import CONTRACT, FEATURE_VECTOR_DOMAIN

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
    if field_name not in env:
        available = ", ".join(sorted(env.keys())) or "(none)"
        print(f"field '{field_name}' not found after execution; available: {available}", file=sys.stderr)
        return 1

    field = env[field_name]
    try:
        feature = field_to_feature(
            field,
            feature_id=f"quack.{field_name}",
            name=field_name,
            provenance={"program": filename, "field": field_name},
        )
    except FieldFeatureError as e:
        print(json.dumps({
            "contract": CONTRACT,
            "status": "rejected",
            "field": {
                "name": field_name,
                "element": field.element.value,
                "shape": list(field.shape),
                "unit": str(getattr(field.unit, "name", field.unit)),
            },
            "error": {"code": "FIELD_MAPPING", "message": str(e)},
        }, indent=2))
        return 1

    report: dict[str, Any] = {
        "contract": CONTRACT,
        "status": "error",
        "field": {
            "name": field_name,
            "element": field.element.value,
            "shape": list(field.shape),
            "unit": str(getattr(field.unit, "name", field.unit)),
            "rank": field.rank,
            "size": field.size,
        },
        "feature": feature,
    }

    try:
        client = BabelCodecClient()
        validation = client.validate_feature_vector([feature])
        report["validation"] = validation
        if not validation.get("ok"):
            report["status"] = "invalid"
            print(json.dumps(report, indent=2))
            return 1

        canon = client.canonicalize(feature)
        report["canonicalization"] = {
            "serialization": canon.get("serialization"),
            "byte_length": canon.get("byte_length"),
            "text": canon.get("text"),
        }

        identity = client.content_hash(feature, domain=FEATURE_VECTOR_DOMAIN)
        report["content_identity"] = {
            "algorithm": identity.get("algorithm"),
            "domain": identity.get("domain"),
            "hex": identity.get("hex"),
            "serialization": identity.get("serialization"),
        }
        report["status"] = "valid"
        print(json.dumps(report, indent=2))
        return 0
    except BabelCodecError as e:
        report["status"] = (
            "unavailable"
            if e.code.endswith("MISSING") or e.code.endswith("INVALID")
            else "error"
        )
        report["error"] = {"code": e.code, "message": str(e)}
        print(json.dumps(report, indent=2))
        return 1


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

    p_bc = sub.add_parser(
        "babelcodec",
        help="optional BabelCodec Field interoperability (requires Node + BABELCODEC_ROOT)",
    )
    bc_sub = p_bc.add_subparsers(dest="bc_command", required=True)
    bc_sub.add_parser("health", help="verify BabelCodec runtime and capabilities")

    p_vf = bc_sub.add_parser(
        "validate-field",
        help="execute a Quack program and validate a named Field via BabelCodec",
    )
    p_vf.add_argument("file", help="Quack source file")
    p_vf.add_argument("--field", required=True, help="Field binding name after simulation")

    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check(args.file)
    if args.command == "ir":
        return cmd_ir(args.file)
    if args.command == "run":
        return cmd_run(args.file)
    if args.command == "babelcodec":
        if args.bc_command == "health":
            return cmd_babelcodec_health()
        if args.bc_command == "validate-field":
            return cmd_babelcodec_validate_field(args.file, args.field)
    return 1


if __name__ == "__main__":
    sys.exit(main())
