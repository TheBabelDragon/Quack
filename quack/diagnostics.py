"""Compiler diagnostics with optional source locations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SourceLocation:
    line: int
    column: int
    filename: Optional[str] = None

    def __str__(self) -> str:
        prefix = f"{self.filename}:" if self.filename else ""
        return f"{prefix}{self.line}:{self.column}"


@dataclass
class Diagnostic:
    message: str
    location: Optional[SourceLocation] = None
    severity: str = "error"  # error | warning | note

    def __str__(self) -> str:
        loc = f"{self.location}: " if self.location else ""
        return f"{loc}{self.severity}: {self.message}"


class DiagnosticCollector:
    def __init__(self) -> None:
        self.items: List[Diagnostic] = []

    def error(self, message: str, location: Optional[SourceLocation] = None) -> None:
        self.items.append(Diagnostic(message, location, "error"))

    def warning(self, message: str, location: Optional[SourceLocation] = None) -> None:
        self.items.append(Diagnostic(message, location, "warning"))

    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.items)

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return len(self.items) > 0


class QuackError(Exception):
    """Base Quack error carrying optional diagnostics."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None) -> None:
        super().__init__(message)
        self.location = location
        self.message = message

    def __str__(self) -> str:
        if self.location:
            return f"{self.location}: error: {self.message}"
        return f"error: {self.message}"
