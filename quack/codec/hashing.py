"""Domain-separated content identity (SHA-256), pure Python.

Matches BabelCodec neural/hash.js:
  hex = SHA-256( domain_sep_bytes || canonicalizeBytes(value) )
  domain_sep = "babelcodec:" + schema + "\\0"
"""

from __future__ import annotations

import hashlib
from typing import Any

from .canonical import canonicalize_bytes, serialization_version
from .errors import CodecValidationError

HASH_ALGORITHM = "sha-256"

_DOMAIN_SEP = {
    "signal.observation.v1": "babelcodec:signal.observation.v1\0",
    "neural.inference.v1": "babelcodec:neural.inference.v1\0",
    "feedback.decision.v1": "babelcodec:feedback.decision.v1\0",
    "feature.vector.v1": "babelcodec:feature.vector.v1\0",
}


def content_hash(domain: str, value: Any) -> dict[str, str]:
    if not isinstance(domain, str) or not domain:
        raise CodecValidationError(
            "content_hash requires non-empty domain string",
            code="BAD_DOMAIN",
        )
    sep = _DOMAIN_SEP.get(domain)
    if sep is None:
        raise CodecValidationError(
            f"no domain separator for schema: {domain}",
            code="BAD_DOMAIN",
        )
    if isinstance(value, dict):
        body_obj = {
            k: v
            for k, v in value.items()
            if k not in ("content_hash", "content_identity")
        }
    else:
        body_obj = value
    body = canonicalize_bytes(body_obj)
    domain_bytes = sep.encode("utf-8")
    digest = hashlib.sha256(domain_bytes + body).hexdigest()
    return {
        "algorithm": HASH_ALGORITHM,
        "serialization": serialization_version(),
        "domain": domain,
        "hex": digest,
    }
