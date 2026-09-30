"""Runtime Field values — everything is a Field."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Tuple

from .topology import Topology, topology_for_shape
from .types import ElementType, FieldType
from .units import Unit, Dimensionless


@dataclass
class Field:
    """
    A Field value: typed elements with shape, topology, and optional unit.

    Scalars are represented as shape () with a single value in `data`.
    """

    data: List[Any]
    field_type: FieldType
    topology: Topology = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.topology is None:
            self.topology = topology_for_shape(self.field_type.shape)
        expected = self.field_type.size if self.field_type.shape != () else 1
        if len(self.data) != expected:
            raise ValueError(
                f"Field data length {len(self.data)} does not match "
                f"shape {self.field_type.shape} (expected {expected})"
            )

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.field_type.shape

    @property
    def unit(self) -> Unit:
        return self.field_type.unit

    @property
    def element(self) -> ElementType:
        return self.field_type.element

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
        shape: Tuple[int, ...],
        *,
        element: ElementType = ElementType.INT,
        unit: Unit = Dimensionless,
    ) -> "Field":
        ft = FieldType(element, shape, unit)
        return cls(list(values), ft)

    def get(self, index: int) -> Any:
        if self.field_type.shape == ():
            if index != 0:
                raise IndexError(f"scalar field index {index} out of range")
            return self.data[0]
        if index < 0 or index >= len(self.data):
            raise IndexError(
                f"index {index} out of range for shape {self.field_type.shape}"
            )
        return self.data[index]

    def __repr__(self) -> str:
        if self.field_type.shape == ():
            return f"Field({self.data[0]!r} : {self.field_type})"
        return f"Field({self.data!r} : {self.field_type})"
