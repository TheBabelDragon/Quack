"""Native Quack codec operations.

BabelCodec owns the *definition* of canonicalization, hashing, and feature
validation. Quack owns computational expression and may execute a compatible
implementation without a Node subprocess.
"""

from __future__ import annotations

from .errors import CodecError, CodecUnavailable, CodecValidationError
from .ops import (
    canonicalize,
    content_hash,
    encode_field,
    inspect_field,
    validate_feature,
)
from .registry import CodecRegistry, get_registry, Operation

__all__ = [
    "CodecError",
    "CodecUnavailable",
    "CodecValidationError",
    "canonicalize",
    "content_hash",
    "encode_field",
    "inspect_field",
    "validate_feature",
    "CodecRegistry",
    "get_registry",
    "Operation",
]
