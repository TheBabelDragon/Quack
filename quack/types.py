"""Element and field types for Quack."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .units import Unit, Dimensionless


class ElementType(str, Enum):
    INT = "int"
    FLOAT = "float"
    DUCK = "duck"  # typed one-element semantic value (MetaField Duck concept)


@dataclass(frozen=True)
class FieldType:
    """
    Complete type of a Field value.

    shape: tuple of positive ints; () means scalar (one-element field)
    element: numeric or duck
    unit: dimensional annotation (default dimensionless)
    """

    element: ElementType
    shape: Tuple[int, ...]
    unit: Unit = Dimensionless

    @property
    def rank(self) -> int:
        return len(self.shape)

    @property
    def size(self) -> int:
        n = 1
        for d in self.shape:
            n *= d
        return n

    @property
    def is_scalar(self) -> bool:
        return self.shape == () or self.shape == (1,)

    def with_shape(self, shape: Tuple[int, ...]) -> "FieldType":
        return FieldType(self.element, shape, self.unit)

    def with_unit(self, unit: Unit) -> "FieldType":
        return FieldType(self.element, self.shape, unit)

    def __str__(self) -> str:
        if self.shape == ():
            shape_s = "()"
        else:
            shape_s = str(self.shape)
        unit_s = f" : {self.unit.name}" if self.unit is not Dimensionless else ""
        return f"Field[{self.element.value}, {shape_s}]{unit_s}"
