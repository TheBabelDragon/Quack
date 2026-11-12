"""Quack ↔ BabelCodec Field interoperability (optional).

BabelCodec remains authoritative for canonicalization, hashing, and
feature validation. Quack remains an independent field language.

Requires:
  - Node.js on PATH
  - BABELCODEC_ROOT pointing at a BabelCodec checkout (>= 0.12.1)

Ordinary Quack programs do not need this package.
"""

from __future__ import annotations

from .client import BabelCodecClient, BabelCodecError, BabelCodecUnavailable
from .fields import field_to_feature, FieldFeatureError
from .protocol import CONTRACT, PROTOCOL_VERSION

__all__ = [
    "BabelCodecClient",
    "BabelCodecError",
    "BabelCodecUnavailable",
    "field_to_feature",
    "FieldFeatureError",
    "CONTRACT",
    "PROTOCOL_VERSION",
]
