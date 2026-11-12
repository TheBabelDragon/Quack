"""Deterministic Quack Field → BabelCodec feature.vector.v1 mapping.

Rules (locked):
- Same Field + metadata → same feature descriptor.
- (1,) remains a vector, never collapsed to scalar.
- Large integers use BabelCodec {$i: "..."} tagged form when needed.
- Integer vector elements must be exact JS-safe integers or are rejected.
- Non-finite floats rejected.
- DUCK explicitly unsupported.
- No silent clip / normalize / round / reinterpret.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

from quack.fields import Field
from quack.types import ElementType
from quack import __version__ as QUACK_VERSION

_JS_SAFE_MAX = (1 << 53) - 1
_JS_SAFE_MIN = -((1 << 53) - 1)


class FieldFeatureError(ValueError):
    """Raised when a Field cannot be mapped to a BabelCodec feature."""


def _unit_name(unit: Any) -> str:
    if unit is None:
        return "Dimensionless"
    name = getattr(unit, "name", None)
    if name:
        return str(name)
    return str(unit)


def _is_js_safe_int(n: int) -> bool:
    return _JS_SAFE_MIN <= n <= _JS_SAFE_MAX


def _encode_int_scalar(value: int) -> Any:
    if _is_js_safe_int(value):
        return int(value)
    return {"$i": str(int(value))}


def _encode_float_scalar(value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise FieldFeatureError(f"float scalar must be numeric, got {type(value).__name__}")
    f = float(value)
    if not math.isfinite(f):
        raise FieldFeatureError(f"non-finite float value: {value!r}")
    if f == 0.0:
        return 0.0
    return f


def _encode_int_vector(values: Sequence[Any]) -> list[float]:
    out: list[float] = []
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, int):
            raise FieldFeatureError(
                f"INT vector element [{i}] must be int, got {type(v).__name__}"
            )
        if not _is_js_safe_int(v):
            raise FieldFeatureError(
                f"INT vector element [{i}]={v} exceeds JS safe integer range; "
                "cannot represent exactly in feature.vector.v1 vector_fixed"
            )
        out.append(float(v))
    return out


def _encode_float_vector(values: Sequence[Any]) -> list[float]:
    out: list[float] = []
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise FieldFeatureError(
                f"FLOAT vector element [{i}] must be numeric, got {type(v).__name__}"
            )
        f = float(v)
        if not math.isfinite(f):
            raise FieldFeatureError(f"FLOAT vector element [{i}] is non-finite: {v!r}")
        if f == 0.0:
            f = 0.0
        out.append(f)
    return out


def field_to_feature(
    field: Field,
    *,
    feature_id: str,
    name: Optional[str] = None,
    extraction_method: str = "quack.field",
    provenance: Optional[Mapping[str, Any]] = None,
    transform: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Convert a Quack Field into a BabelCodec feature descriptor."""
    if not isinstance(field, Field):
        raise FieldFeatureError(f"expected Field, got {type(field).__name__}")
    if not feature_id or not isinstance(feature_id, str):
        raise FieldFeatureError("feature_id is required")

    element = field.element
    if element is ElementType.DUCK:
        raise FieldFeatureError(
            "DUCK fields are explicitly unsupported until a suitable semantic "
            "mapping exists; refusing silent conversion"
        )

    unit = _unit_name(field.unit)
    shape = list(field.shape)
    data = list(field.data)
    feat_name = name or feature_id

    base_prov: dict[str, Any] = {
        "source": "quack",
        "quack_version": QUACK_VERSION,
        "element": element.value,
        "shape": shape,
        "rank": field.rank,
        "size": field.size,
    }
    if provenance:
        base_prov.update(dict(provenance))

    if field.rank == 0:
        if element is ElementType.INT:
            if not isinstance(data[0], int) or isinstance(data[0], bool):
                raise FieldFeatureError(
                    f"INT scalar value must be int, got {type(data[0]).__name__}"
                )
            value = _encode_int_scalar(data[0])
            ftype = "int64"
        elif element is ElementType.FLOAT:
            value = _encode_float_scalar(data[0])
            ftype = "float64"
        else:
            raise FieldFeatureError(f"unsupported element type: {element}")
        feature: dict[str, Any] = {
            "feature_id": feature_id,
            "name": feat_name,
            "type": ftype,
            "unit": unit,
            "value": value,
            "extraction_method": extraction_method,
            "provenance": base_prov,
        }
    else:
        if element is ElementType.INT:
            value = _encode_int_vector(data)
        elif element is ElementType.FLOAT:
            value = _encode_float_vector(data)
        else:
            raise FieldFeatureError(f"unsupported element type: {element}")
        feature = {
            "feature_id": feature_id,
            "name": feat_name,
            "type": "vector_fixed",
            "unit": unit,
            "dimensions": shape,
            "value": value,
            "extraction_method": extraction_method,
            "provenance": base_prov,
        }

    if transform is not None:
        feature["transform"] = dict(transform)

    return feature
