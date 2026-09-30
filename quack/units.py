"""
Minimal dimensional / unit system for Quack v0.1.

Units participate in typing. Incompatible dimensions are rejected
at semantic analysis time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Unit:
    name: str
    dims: Tuple[int, int, int, int]  # L, M, T, I

    def compatible(self, other: "Unit") -> bool:
        return self.dims == other.dims

    def mul(self, other: "Unit") -> "Unit":
        d = tuple(a + b for a, b in zip(self.dims, other.dims))
        return Unit(_name_for(d), d)  # type: ignore[arg-type]

    def div(self, other: "Unit") -> "Unit":
        d = tuple(a - b for a, b in zip(self.dims, other.dims))
        return Unit(_name_for(d), d)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.name


Dimensionless = Unit("Dimensionless", (0, 0, 0, 0))
Voltage = Unit("Voltage", (2, 1, -3, -1))
Resistance = Unit("Resistance", (2, 1, -3, -2))
Current = Unit("Current", (0, 0, 0, 1))
Mass = Unit("Mass", (0, 1, 0, 0))
Length = Unit("Length", (1, 0, 0, 0))
Time = Unit("Time", (0, 0, 1, 0))

_KNOWN: Dict[Tuple[int, int, int, int], str] = {
    (0, 0, 0, 0): "Dimensionless",
    (2, 1, -3, -1): "Voltage",
    (2, 1, -3, -2): "Resistance",
    (0, 0, 0, 1): "Current",
    (0, 1, 0, 0): "Mass",
    (1, 0, 0, 0): "Length",
    (0, 0, 1, 0): "Time",
}


def _name_for(dims: Tuple[int, int, int, int]) -> str:
    if dims in _KNOWN:
        return _KNOWN[dims]
    parts = []
    for label, e in zip(("L", "M", "T", "I"), dims):
        if e == 0:
            continue
        if e == 1:
            parts.append(label)
        else:
            parts.append(f"{label}^{e}")
    return "*".join(parts) if parts else "Dimensionless"


UNIT_BY_NAME: Dict[str, Unit] = {
    "Dimensionless": Dimensionless,
    "Voltage": Voltage,
    "Resistance": Resistance,
    "Current": Current,
    "Mass": Mass,
    "Length": Length,
    "Time": Time,
}


def lookup_unit(name: str) -> Unit:
    if name not in UNIT_BY_NAME:
        raise KeyError(f"Unknown unit: {name}")
    return UNIT_BY_NAME[name]
