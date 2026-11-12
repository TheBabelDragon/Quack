"""Pure-Python canonical JSON compatible with babelcodec.canonical-json.v1."""

from __future__ import annotations

import json
import math
from typing import Any

from .errors import CodecValidationError

SERIALIZATION_VERSION = "babelcodec.canonical-json.v1"
_JS_SAFE_MAX = (1 << 53) - 1
_JS_SAFE_MIN = -((1 << 53) - 1)


def _is_decimal_int(s: str) -> bool:
    if not s:
        return False
    if s[0] == "-":
        return len(s) > 1 and s[1:].isdigit()
    return s.isdigit()


def _normalize(value: Any, path: str = "$") -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value < _JS_SAFE_MIN or value > _JS_SAFE_MAX:
            raise CodecValidationError(
                f"integer outside JS safe range at {path}; use {{'$i': '...'}} form",
                code="UNSAFE_INTEGER",
            )
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CodecValidationError(
                f"non-finite number at {path}",
                code="NON_FINITE",
            )
        if value == 0.0:
            return 0.0
        return float(value)
    if isinstance(value, dict):
        if set(value.keys()) == {"$i"} and isinstance(value.get("$i"), str):
            if not _is_decimal_int(value["$i"]):
                raise CodecValidationError(
                    f"invalid $i at {path}",
                    code="BAD_TAGGED_INT",
                )
            return {"$i": value["$i"]}
        out: dict[str, Any] = {}
        for k in sorted(value.keys()):
            if not isinstance(k, str):
                raise CodecValidationError(
                    f"object key must be string at {path}",
                    code="BAD_KEY",
                )
            out[k] = _normalize(value[k], f"{path}.{k}")
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize(v, f"{path}[{i}]") for i, v in enumerate(value)]
    raise CodecValidationError(
        f"unsupported type {type(value).__name__} at {path}",
        code="UNSUPPORTED_TYPE",
    )


def _dump(norm: Any) -> str:
    """Match JS JSON.stringify numeric form: integers without trailing .0"""
    if norm is None:
        return "null"
    if isinstance(norm, bool):
        return "true" if norm else "false"
    if isinstance(norm, str):
        return json.dumps(norm, ensure_ascii=False)
    if isinstance(norm, int) and not isinstance(norm, bool):
        return str(norm)
    if isinstance(norm, float):
        if norm == int(norm) and abs(norm) < 1e15:
            return str(int(norm))
        return json.dumps(norm)
    if isinstance(norm, list):
        return "[" + ",".join(_dump(x) for x in norm) + "]"
    if isinstance(norm, dict):
        parts = []
        for k, v in norm.items():
            parts.append(json.dumps(k, ensure_ascii=False) + ":" + _dump(v))
        return "{" + ",".join(parts) + "}"
    raise CodecValidationError(
        f"cannot dump {type(norm).__name__}",
        code="UNSUPPORTED_TYPE",
    )


def canonicalize(value: Any) -> str:
    return _dump(_normalize(value))


def canonicalize_bytes(value: Any) -> bytes:
    return canonicalize(value).encode("utf-8")


def serialization_version() -> str:
    return SERIALIZATION_VERSION
