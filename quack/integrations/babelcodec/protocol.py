"""Versioned JSON-lines protocol: quack.babelcodec.v1

Request (one JSON object per line on stdin):
  {
    "contract": "quack.babelcodec.v1",
    "id": "<request-id>",
    "op": "health" | "validate_feature_vector" | "canonicalize"
         | "content_hash" | "validate_event",
    "payload": { ... }
  }

Response (one JSON object on stdout):
  {
    "contract": "quack.babelcodec.v1",
    "id": "<request-id>",
    "ok": true | false,
    "result": { ... },
    "error": { "code": "...", "message": "..." }
  }

Diagnostics and logs go to stderr only. Never to stdout.
"""

from __future__ import annotations

CONTRACT = "quack.babelcodec.v1"
PROTOCOL_VERSION = "1"

ALLOWED_OPS = frozenset(
    {
        "health",
        "validate_feature_vector",
        "canonicalize",
        "content_hash",
        "validate_event",
    }
)

FEATURE_VECTOR_DOMAIN = "feature.vector.v1"

MAX_REQUEST_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT_S = 15.0
MIN_BABELCODEC_VERSION = (0, 12, 1)
