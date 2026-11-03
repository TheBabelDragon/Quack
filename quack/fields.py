"""Runtime Field values — everything is a Field. Rank-N layout contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Tuple, Union

from .shape import (
    Shape,
    coords_from_offset,
    format_shape,
    is_scalar,
    offset,
    size as shape_size,
    strides,
    validate_shape,
)
from .topology import Topology, topology_for_shape
from .types import ElementType, FieldType
from .units import Unit, Dimensionless


@dataclass
class Field:
    """
    A Field value: typed elements with shape, topology, and optional unit.

    Storage is contiguous row-major (C-order). Scalars use shape () with
    a single element in `data`. Shape metadata and storage length are
    kept consistent by construction; divergence raises ValueError.
    """

    data: List[Any]
    field_type: FieldType
    topology: Topology = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        expected = self.field_type.size
        if len(self.data) != expected:
            raise ValueError(
                f"Field data length {len(self.data)} does not match "
                f"shape {format_shape(self.field_type.shape)} "
                f"(expected {expected} elements)"
            )
        if self.topology is None:
            self.topology = topology_for_shape(self.field_type.shape)

    @property
    def shape(self) -> Shape:
        return self.field_type.shape

    @property
    def rank(self) -> int:
        return self.field_type.rank

    @property
    def size(self) -> int:
        return self.field_type.size

    @property
    def unit(self) -> Unit:
        return self.field_type.unit

    @property
    def element(self) -> ElementType:
        return self.field_type.element

    @property
    def strides(self) -> Tuple[int, ...]:
        return self.field_type.strides

    @classmethod
    def scalar(
        cls,
        value: Any,
        *,
        element: Optional[ElementType] = None,
        unit: Unit = Dimensionless,
    ) -> "Field":
        if element is None:
            if isinstance(value, float):
                element = ElementType.FLOAT
            elif isinstance(value, int):
                element = ElementType.INT
            else:
                element = ElementType.DUCK
        ft = FieldType(element, (), unit)
        return cls([value], ft)

    @classmethod
    def from_values(
        cls,
        values: Sequence[Any],
        shape: Shape,
        *,
        element: ElementType = ElementType.INT,
        unit: Unit = Dimensionless,
        topology: Optional[Topology] = None,
    ) -> "Field":
        shape = validate_shape(shape)
        ft = FieldType(element, shape, unit)
        f = cls(list(values), ft)
        if topology is not None:
            f.topology = topology
        return f

    def get(self, index: int) -> Any:
        """Linear (flattened) access. Valid for any rank including scalar."""
        if not isinstance(index, int):
            raise TypeError(f"linear index must be int, got {type(index).__name__}")
        n = self.size
        if index < 0 or index >= n:
            raise IndexError(
                f"index {index} out of range for shape {format_shape(self.shape)} "
                f"(size {n})"
            )
        return self.data[index]

    def get_at(self, *coords: int) -> Any:
        """Multi-dimensional coordinate access (row-major).

        For scalar, call with no arguments or with 0.
        For rank-N, pass exactly N integer coordinates.
        """
        if is_scalar(self.shape):
            if len(coords) == 0 or (len(coords) == 1 and coords[0] == 0):
                return self.data[0]
            raise IndexError(f"scalar field has no multi-index; got {coords}")
        lin = offset(self.shape, coords)
        return self.data[lin]

    def coords_of(self, linear: int) -> Tuple[int, ...]:
        """Map a linear index back to multi-dimensional coordinates."""
        return coords_from_offset(self.shape, linear)

    def __repr__(self) -> str:
        if is_scalar(self.shape):
            return f"Field({self.data[0]!r} : {self.field_type})"
        return f"Field({self.data!r} : {self.field_type})"
