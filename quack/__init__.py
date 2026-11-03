"""
Quack — field-oriented programming language.

Everything is a Field. Scalars are one-element fields.
Geometry and physical units are semantic information.
"""

__version__ = "0.2.0"

from .fields import Field
from .types import ElementType, FieldType
from .units import Unit, Voltage, Resistance, Current, Mass, Dimensionless
from .topology import Topology, Linear, Point, Grid2D
from .shape import size, strides, offset

__all__ = [
    "Field",
    "ElementType",
    "FieldType",
    "Unit",
    "Voltage",
    "Resistance",
    "Current",
    "Mass",
    "Dimensionless",
    "Topology",
    "Linear",
    "Point",
    "Grid2D",
    "size",
    "strides",
    "offset",
    "__version__",
]
