"""Protocol and client unit tests (Node optional)."""

from __future__ import annotations

import os

import pytest

from quack.integrations.babelcodec.protocol import (
    ALLOWED_OPS,
    CONTRACT,
    FEATURE_VECTOR_DOMAIN,
)
from quack.integrations.babelcodec.client import (
    BabelCodecClient,
    BabelCodecError,
    BabelCodecUnavailable,
)


def test_contract_constant():
    assert CONTRACT == "quack.babelcodec.v1"
    assert "health" in ALLOWED_OPS
    assert FEATURE_VECTOR_DOMAIN == "feature.vector.v1"


def test_missing_root_raises():
    env_backup = os.environ.pop("BABELCODEC_ROOT", None)
    try:
        client = BabelCodecClient()
        with pytest.raises(BabelCodecUnavailable) as ei:
            client.health()
        assert ei.value.code in {
            "BABELCODEC_ROOT_MISSING",
            "NODE_MISSING",
            "BABELCODEC_ROOT_INVALID",
        }
    finally:
        if env_backup is not None:
            os.environ["BABELCODEC_ROOT"] = env_backup


def test_disallowed_op():
    client = BabelCodecClient(babelcodec_root="/tmp", node_bin="node")
    with pytest.raises(BabelCodecError) as ei:
        client.call("not_a_real_op", {})
    assert ei.value.code == "OP_DENIED"
