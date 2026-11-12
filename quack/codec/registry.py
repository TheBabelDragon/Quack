"""Shared codec operation registry for Babel-Stack consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class Operation:
    name: str
    description: str
    provider: str
    pure: bool


@dataclass
class CodecRegistry:
    _ops: Dict[str, Operation] = field(default_factory=dict)
    _handlers: Dict[str, Callable[..., Any]] = field(default_factory=dict)

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        *,
        description: str,
        provider: str,
        pure: bool,
    ) -> None:
        self._ops[name] = Operation(
            name=name, description=description, provider=provider, pure=pure
        )
        self._handlers[name] = handler

    def get(self, name: str) -> Optional[Operation]:
        return self._ops.get(name)

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self._handlers:
            raise KeyError(f"unknown codec operation: {name}")
        return self._handlers[name](*args, **kwargs)

    def list_ops(self) -> List[Operation]:
        return [self._ops[k] for k in sorted(self._ops)]


_REGISTRY: Optional[CodecRegistry] = None


def get_registry() -> CodecRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = CodecRegistry()
        _install_defaults(_REGISTRY)
    return _REGISTRY


def _install_defaults(reg: CodecRegistry) -> None:
    from . import canonical as canon
    from . import hashing
    from .ops import encode_field, inspect_field, validate_feature

    reg.register(
        "canonicalize",
        lambda value: {
            "serialization": canon.serialization_version(),
            "text": canon.canonicalize(value),
            "bytes": canon.canonicalize_bytes(value),
        },
        description="Canonical JSON text + UTF-8 bytes (babelcodec.canonical-json.v1)",
        provider="quack.codec.pure",
        pure=True,
    )
    reg.register(
        "content_hash",
        lambda value, domain="feature.vector.v1": hashing.content_hash(domain, value),
        description="Domain-separated SHA-256 content identity",
        provider="quack.codec.pure",
        pure=True,
    )
    reg.register(
        "encode_field",
        encode_field,
        description="Quack Field \u2192 feature.vector.v1 descriptor",
        provider="quack.codec.pure",
        pure=True,
    )
    reg.register(
        "inspect_field",
        inspect_field,
        description="Structured Field inspection record",
        provider="quack.codec.pure",
        pure=True,
    )
    reg.register(
        "validate_feature",
        validate_feature,
        description="Validate feature descriptor (pure subset or BabelCodec)",
        provider="quack.codec",
        pure=False,
    )
