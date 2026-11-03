"""Element and field types for Quack — rank-N aware."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from .shape import (
    Shape,
    format_shape,
    is_scalar as shape_is_scalar,
    rank as shape_rank,
    size as shape_size,
    strides as shape_strides,
    validate_shape,
)
from .units import Unit, Dimensionless


class ElementType(str, Enum):
    INT = "int"
    FLOAT = "float"
    DUCK = "duck"  # typed one-element semantic value (MetaField Duck concept)


@dataclass(frozen=True)
class FieldType:
    """
    Complete type of a Field value.

    shape: () for scalar; (D1, ..., Dn) for rank-N. All Di >= 1.
    element: numeric or duck
    unit: dimensional annotation (default dimensionless)

    Invariants:
      - shape is validated at construction
      - size == product of dimensions (1 for scalar)
      - scalar is strictly shape == ()
      - (1,) is a one-element vector, distinct from scalar
    """

    element: ElementType
    shape: Shape
    unit: Unit = Dimensionless

    def __post_init__(self) -> None:
        # frozen dataclass: validate shape
        validated = validate_shape(self.shape)
        if validated != self.shape:
            object.__setattr__(self, "shape", validated)

    @property
    def rank(self) -> int:
        return shape_rank(self.shape)

    @property
    def size(self) -> int:
        return shape_size(self.shape)

    @property
    def is_scalar(self) -> bool:
        """True only for shape (). (1,) is a vector of length 1."""
        return shape_is_scalar(self.shape)

    @property
    def strides(self) -> Tuple[int, ...]:
        return shape_strides(self.shape)

    def with_shape(self, shape: Shape) -> "FieldType":
        return FieldType(self.element, validate_shape(shape), self.unit)

    def with_unit(self, unit: Unit) -> "FieldType":
        return FieldType(self.element, self.shape, unit)

    def with_element(self, element: ElementType) -> "FieldType":
        return FieldType(element, self.shape, self.unit)

    def __str__(self) -> str:
        shape_s = format_shape(self.shape)
        unit_s = f" : {self.unit.name}" if self.unit is not Dimensionless else ""
        return f"Field[{self.element.value}, {shape_s}]{unit_s}"
