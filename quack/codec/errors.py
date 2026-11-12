"""Explicit codec conversion and validation errors."""

from __future__ import annotations

from typing import Any, Optional


class CodecError(Exception):
    def __init__(self, message: str, *, code: str = "CODEC_ERROR", detail: Any = None):
        super().__init__(message)
        self.code = code
        self.detail = detail


class CodecUnavailable(CodecError):
    def __init__(self, message: str, *, code: str = "CODEC_UNAVAILABLE", detail: Any = None):
        super().__init__(message, code=code, detail=detail)


class CodecValidationError(CodecError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "CODEC_VALIDATION",
        errors: Optional[list[str]] = None,
        detail: Any = None,
    ):
        super().__init__(message, code=code, detail=detail)
        self.errors = list(errors or [])
