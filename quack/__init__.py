"""
Quack — field-oriented programming language.

Everything is a Field. Scalars are one-element fields.
Geometry and physical units are semantic information.
"""

__version__ = "0.1.0"

from .fields import Field
from .types import ElementType, FieldType
from .units import Unit, Voltage, Resistance, Current, Mass, Dimensionless
from .topology import Topology, Linear

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
    "__version__",
]
