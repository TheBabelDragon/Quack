"""Native codec operations: encode, inspect, canonicalize, hash, validate."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from quack.fields import Field

from . import canonical as canon
from . import hashing
from .errors import CodecValidationError

FEATURE_VECTOR_DOMAIN = "feature.vector.v1"


def encode_field(
    field: Field,
    *,
    feature_id: str,
    name: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    from quack.integrations.babelcodec.fields import field_to_feature, FieldFeatureError

    try:
        return field_to_feature(
            field,
            feature_id=feature_id,
            name=name,
            provenance=provenance,
        )
    except FieldFeatureError as e:
        raise CodecValidationError(str(e), code="FIELD_MAPPING") from e


def inspect_field(field: Field) -> dict[str, Any]:
    if not isinstance(field, Field):
        raise CodecValidationError(
            f"expected Field, got {type(field).__name__}",
            code="BAD_FIELD",
        )
    return {
        "element": field.element.value,
        "shape": list(field.shape),
        "rank": field.rank,
        "size": field.size,
        "unit": str(getattr(field.unit, "name", field.unit)),
        "data_preview": list(field.data[:16]),
        "data_len": len(field.data),
    }


def canonicalize(value: Any) -> dict[str, Any]:
    text = canon.canonicalize(value)
    raw = text.encode("utf-8")
    return {
        "serialization": canon.serialization_version(),
        "text": text,
        "byte_length": len(raw),
        "bytes_hex": raw.hex(),
    }


def content_hash(value: Any, *, domain: str = FEATURE_VECTOR_DOMAIN) -> dict[str, str]:
    return hashing.content_hash(domain, value)


def validate_feature(
    feature: Mapping[str, Any],
    *,
    prefer_babelcodec: bool = True,
) -> dict[str, Any]:
    if prefer_babelcodec:
        try:
            from quack.integrations.babelcodec import BabelCodecClient

            client = BabelCodecClient()
            return client.validate_feature_vector([dict(feature)])
        except Exception:
            pass
    return _pure_validate_feature(dict(feature))


def _pure_validate_feature(f: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(f, dict):
        return {"ok": False, "errors": ["feature must be object"]}
    if not f.get("feature_id"):
        errors.append("feature_id required")
    if not f.get("name"):
        errors.append("name required")
    ftype = f.get("type")
    allowed = {"float64", "int64", "boolean", "categorical", "vector_fixed", "vector_variable"}
    if ftype not in allowed:
        errors.append(f"unsupported type: {ftype}")
    v = f.get("value")
    if ftype == "float64":
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not _finite(v):
            errors.append(f"float64 value must be finite number ({f.get('feature_id')})")
    elif ftype == "int64":
        if isinstance(v, dict) and "$i" in v:
            if not isinstance(v["$i"], str):
                errors.append(f"int64 $i invalid ({f.get('feature_id')})")
        elif not isinstance(v, int) or isinstance(v, bool):
            errors.append(f"int64 value must be int or {{$i}} ({f.get('feature_id')})")
    elif ftype == "vector_fixed":
        dims = f.get("dimensions")
        if not isinstance(v, list):
            errors.append(f"vector_fixed must be array ({f.get('feature_id')})")
        elif not isinstance(dims, list) or not dims:
            errors.append(f"vector_fixed requires dimensions ({f.get('feature_id')})")
        else:
            expected = 1
            for d in dims:
                expected *= int(d)
            if len(v) != expected:
                errors.append(
                    f"vector_fixed length {len(v)} != product(dimensions)={expected} "
                    f"({f.get('feature_id')})"
                )
            for i, x in enumerate(v):
                if not isinstance(x, (int, float)) or isinstance(x, bool) or not _finite(x):
                    errors.append(f"vector_fixed[{i}] non-finite ({f.get('feature_id')})")
                    break
    return {"ok": not errors, "errors": errors}


def _finite(x: Any) -> bool:
    try:
        import math

        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def encode_canonicalize_hash(
    field: Field,
    *,
    feature_id: str,
    name: Optional[str] = None,
) -> dict[str, Any]:
    feature = encode_field(field, feature_id=feature_id, name=name)
    canon_result = canonicalize(feature)
    identity = content_hash(feature, domain=FEATURE_VECTOR_DOMAIN)
    return {
        "contract": "quack.codec.v1",
        "feature": feature,
        "canonicalization": canon_result,
        "content_identity": identity,
    }
