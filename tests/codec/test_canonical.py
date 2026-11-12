"""Pure canonical JSON + hash tests; optional parity with BabelCodec worker."""

from __future__ import annotations

import os
import shutil

import pytest

from quack.codec.canonical import canonicalize, serialization_version
from quack.codec.hashing import content_hash
from quack.codec.errors import CodecValidationError
from quack.codec.ops import encode_field, encode_canonicalize_hash
from quack.fields import Field
from quack.types import ElementType


def test_serialization_version():
    assert serialization_version() == "babelcodec.canonical-json.v1"


def test_key_order():
    assert canonicalize({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_nested_and_null():
    assert canonicalize({"z": None, "a": {"y": 1, "x": 2}}) == '{"a":{"x":2,"y":1},"z":null}'


def test_neg_zero():
    assert canonicalize(-0.0) == "0"


def test_non_finite_rejected():
    with pytest.raises(CodecValidationError, match="non-finite"):
        canonicalize(float("nan"))


def test_unsafe_int_rejected():
    with pytest.raises(CodecValidationError, match="safe range"):
        canonicalize((1 << 53) + 1)


def test_tagged_int():
    assert canonicalize({"$i": "9007199254740993"}) == '{"$i":"9007199254740993"}'


def test_content_hash_stable():
    a = content_hash("feature.vector.v1", {"x": 1, "y": [2, 3]})
    b = content_hash("feature.vector.v1", {"y": [2, 3], "x": 1})
    assert a["hex"] == b["hex"]
    assert a["algorithm"] == "sha-256"


def test_encode_pipeline():
    f = Field.from_values([5, 6, 7, 8], (4,), element=ElementType.INT)
    result = encode_canonicalize_hash(f, feature_id="quack.result", name="result")
    assert result["contract"] == "quack.codec.v1"
    assert result["feature"]["type"] == "vector_fixed"
    assert result["content_identity"]["hex"]


def _bc_ready() -> bool:
    return bool(os.environ.get("BABELCODEC_ROOT")) and shutil.which("node") is not None


@pytest.mark.skipif(not _bc_ready(), reason="BABELCODEC_ROOT + node required")
def test_parity_with_babelcodec_worker():
    from quack.integrations.babelcodec import BabelCodecClient

    f = Field.from_values([5, 6, 7, 8], (4,), element=ElementType.INT)
    feature = encode_field(f, feature_id="quack.result", name="result")
    pure_canon = canonicalize(feature)
    pure_hash = content_hash("feature.vector.v1", feature)
    client = BabelCodecClient()
    bc_canon = client.canonicalize(feature)
    bc_hash = client.content_hash(feature, domain="feature.vector.v1")
    assert pure_canon == bc_canon["text"]
    assert pure_hash["hex"] == bc_hash["hex"]
