"""Unit tests for Field \u2192 feature.vector.v1 mapping (no Node required)."""

from __future__ import annotations

import math

import pytest

from quack.fields import Field
from quack.types import ElementType
from quack.units import Dimensionless, Voltage
from quack.integrations.babelcodec.fields import field_to_feature, FieldFeatureError


def test_int_scalar():
    f = Field.scalar(42, element=ElementType.INT)
    feat = field_to_feature(f, feature_id="q.x", name="x")
    assert feat["type"] == "int64"
    assert feat["value"] == 42
    assert "dimensions" not in feat
    assert feat["provenance"]["shape"] == []
    assert feat["provenance"]["rank"] == 0


def test_float_scalar():
    f = Field.scalar(3.5, element=ElementType.FLOAT)
    feat = field_to_feature(f, feature_id="q.y")
    assert feat["type"] == "float64"
    assert feat["value"] == 3.5


def test_large_int_scalar_tagged():
    big = (1 << 53) + 7
    f = Field.scalar(big, element=ElementType.INT)
    feat = field_to_feature(f, feature_id="q.big")
    assert feat["type"] == "int64"
    assert feat["value"] == {"$i": str(big)}


def test_int_vector_preserves_shape():
    f = Field.from_values([1, 2, 3, 4], (4,), element=ElementType.INT)
    feat = field_to_feature(f, feature_id="q.v")
    assert feat["type"] == "vector_fixed"
    assert feat["dimensions"] == [4]
    assert feat["value"] == [1.0, 2.0, 3.0, 4.0]


def test_one_element_vector_not_scalar():
    f = Field.from_values([9], (1,), element=ElementType.INT)
    assert f.rank == 1
    feat = field_to_feature(f, feature_id="q.one")
    assert feat["type"] == "vector_fixed"
    assert feat["dimensions"] == [1]
    assert feat["value"] == [9.0]


def test_rank2_float():
    f = Field.from_values(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        (2, 3),
        element=ElementType.FLOAT,
        unit=Voltage,
    )
    feat = field_to_feature(f, feature_id="q.m")
    assert feat["type"] == "vector_fixed"
    assert feat["dimensions"] == [2, 3]
    assert feat["unit"] == "Voltage"
    assert feat["value"] == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_non_finite_rejected():
    f = Field.scalar(float("nan"), element=ElementType.FLOAT)
    with pytest.raises(FieldFeatureError, match="non-finite"):
        field_to_feature(f, feature_id="q.bad")


def test_duck_rejected():
    f = Field.scalar("quack", element=ElementType.DUCK)
    with pytest.raises(FieldFeatureError, match="DUCK"):
        field_to_feature(f, feature_id="q.duck")


def test_large_int_vector_rejected():
    big = (1 << 53) + 1
    f = Field.from_values([1, big], (2,), element=ElementType.INT)
    with pytest.raises(FieldFeatureError, match="safe integer"):
        field_to_feature(f, feature_id="q.bigvec")


def test_deterministic():
    f = Field.from_values([1, 2, 3], (3,), element=ElementType.INT, unit=Dimensionless)
    a = field_to_feature(f, feature_id="q.d", name="d")
    b = field_to_feature(f, feature_id="q.d", name="d")
    assert a == b


def test_neg_zero_normalized():
    f = Field.scalar(-0.0, element=ElementType.FLOAT)
    feat = field_to_feature(f, feature_id="q.z")
    assert feat["value"] == 0.0
    assert not math.copysign(1.0, feat["value"]) < 0
