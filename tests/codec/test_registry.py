"""Codec operation registry tests."""

from __future__ import annotations

from quack.codec.registry import get_registry
from quack.fields import Field
from quack.types import ElementType


def test_registry_lists_ops():
    reg = get_registry()
    names = {op.name for op in reg.list_ops()}
    assert "canonicalize" in names
    assert "content_hash" in names
    assert "encode_field" in names
    assert "inspect_field" in names


def test_registry_canonicalize():
    reg = get_registry()
    result = reg.call("canonicalize", {"b": 1, "a": 2})
    assert result["text"] == '{"a":2,"b":1}'
    assert result["serialization"] == "babelcodec.canonical-json.v1"


def test_registry_encode_field():
    reg = get_registry()
    f = Field.scalar(42, element=ElementType.INT)
    feat = reg.call("encode_field", f, feature_id="q.x")
    assert feat["type"] == "int64"
    assert feat["value"] == 42


def test_pure_ops_marked():
    reg = get_registry()
    canon = reg.get("canonicalize")
    assert canon is not None and canon.pure is True
