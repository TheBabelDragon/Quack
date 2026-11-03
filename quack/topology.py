"""Field topology — geometry is semantic information, not a comment.

Topology describes the *logical* arrangement of elements. It is distinct
from the physical storage layout (always contiguous row-major). Programs
must not invent physical geometry the source did not specify.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .shape import Shape, format_shape, is_scalar, rank, size


@dataclass(frozen=True)
class Topology:
    """Abstract spatial arrangement of field elements."""

    name: str
    rank: int = 0  # expected shape rank; -1 means any / unconstrained

    def __str__(self) -> str:
        return self.name

    def compatible_with(self, shape: Shape) -> bool:
        """Return True if this topology is valid for the given shape."""
        if self.rank < 0:
            return True
        if is_scalar(shape):
            return self.rank == 0
        return rank(shape) == self.rank


# Canonical topologies
Point = Topology("point", rank=0)       # scalar / zero-dimensional
Linear = Topology("linear", rank=1)     # 1-D sequence
Grid2D = Topology("grid2d", rank=2)     # regular 2-D lattice
Grid3D = Topology("grid3d", rank=3)     # regular 3-D lattice


def topology_for_shape(shape: Shape) -> Topology:
    """Infer a default topology from shape. Does not invent geometry beyond rank."""
    if is_scalar(shape):
        return Point
    r = rank(shape)
    if r == 1:
        return Linear
    if r == 2:
        return Grid2D
    if r == 3:
        return Grid3D
    return Topology(f"grid{r}d", rank=r)


def validate_topology(topology: Topology, shape: Shape) -> None:
    """Raise ValueError if topology is incompatible with shape."""
    if not topology.compatible_with(shape):
        raise ValueError(
            f"topology '{topology.name}' (rank {topology.rank}) is incompatible "
            f"with shape {format_shape(shape)} (rank {rank(shape)})"
        )


def describe_topology(shape: Shape, topology: Optional[Topology] = None) -> str:
    topo = topology or topology_for_shape(shape)
    return f"{topo.name} over {format_shape(shape)} ({size(shape)} elements)"
