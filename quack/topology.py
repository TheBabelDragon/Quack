"""Field topology — geometry is semantic, not a comment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Topology:
    """Abstract spatial arrangement of field elements."""

    name: str

    def __str__(self) -> str:
        return self.name


Linear = Topology("linear")
Grid2D = Topology("grid2d")
Point = Topology("point")  # scalar / one-element


def topology_for_shape(shape: Tuple[int, ...]) -> Topology:
    if shape == () or shape == (1,):
        return Point
    if len(shape) == 1:
        return Linear
    if len(shape) == 2:
        return Grid2D
    return Topology(f"rank{len(shape)}")
