"""End-to-end tests against a real BabelCodec checkout.

Skipped automatically when BABELCODEC_ROOT is unset or Node is missing.
"""

from __future__ import annotations

import os
import shutil

import pytest

from quack.fields import Field
from quack.types import ElementType
from quack.integrations.babelcodec import (
    BabelCodecClient,
    field_to_feature,
)
from quack.integrations.babelcodec.protocol import FEATURE_VECTOR_DOMAIN


def _ready() -> bool:
    return bool(os.environ.get("BABELCODEC_ROOT")) and shutil.which("node") is not None


pytestmark = pytest.mark.skipif(
    not _ready(),
    reason="BABELCODEC_ROOT + node required for live BabelCodec integration",
)


@pytest.fixture(scope="module")
def client() -> BabelCodecClient:
    return BabelCodecClient()


def test_health_reports_version(client: BabelCodecClient):
    h = client.health()
    assert h["babelcodec_version"].startswith("0.12") or h["babelcodec_version"] >= "0.12.1"
    assert "validate_feature_vector" in h["ops"]
    assert h["serialization"]


def test_validate_int_vector(client: BabelCodecClient):
    f = Field.from_values([5, 6, 7, 8], (4,), element=ElementType.INT)
    feat = field_to_feature(f, feature_id="quack.result", name="result")
    result = client.validate_feature_vector([feat])
    assert result["ok"] is True


def test_canonicalize_deterministic(client: BabelCodecClient):
    f = Field.from_values([1, 2, 3], (3,), element=ElementType.INT)
    feat = field_to_feature(f, feature_id="quack.t", name="t")
    a = client.canonicalize(feat)
    b = client.canonicalize(feat)
    assert a["text"] == b["text"]
    assert a["bytes_base64"] == b["bytes_base64"]
    assert a["serialization"].startswith("babelcodec.canonical-json")


def test_content_identity_reproducible(client: BabelCodecClient):
    f = Field.from_values([1, 2, 3], (3,), element=ElementType.INT)
    feat = field_to_feature(f, feature_id="quack.t", name="t")
    a = client.content_hash(feat, domain=FEATURE_VECTOR_DOMAIN)
    b = client.content_hash(feat, domain=FEATURE_VECTOR_DOMAIN)
    assert a["hex"] == b["hex"]
    assert a["domain"] == FEATURE_VECTOR_DOMAIN
    assert a["algorithm"] == "sha-256"


def test_scalar_and_one_vector_distinct(client: BabelCodecClient):
    scalar = field_to_feature(
        Field.scalar(9, element=ElementType.INT),
        feature_id="quack.s",
    )
    one = field_to_feature(
        Field.from_values([9], (1,), element=ElementType.INT),
        feature_id="quack.s",
    )
    assert scalar["type"] == "int64"
    assert one["type"] == "vector_fixed"
    hs = client.content_hash(scalar, domain=FEATURE_VECTOR_DOMAIN)["hex"]
    hv = client.content_hash(one, domain=FEATURE_VECTOR_DOMAIN)["hex"]
    assert hs != hv


def test_invalid_feature_diagnostics(client: BabelCodecClient):
    bad_vec = {
        "feature_id": "bad",
        "name": "bad",
        "type": "vector_fixed",
        "dimensions": [2],
        "value": [1.0],
    }
    result = client.validate_feature_vector([bad_vec])
    assert result["ok"] is False
    assert result["errors"]
