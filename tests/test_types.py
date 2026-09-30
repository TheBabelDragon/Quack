"""Type system tests."""

from quack.types import ElementType, FieldType
from quack.units import Dimensionless, Voltage


def test_scalar_shape():
    ft = FieldType(ElementType.INT, (), Dimensionless)
    assert ft.is_scalar
    assert ft.size == 1
    assert ft.rank == 0


def test_vector_shape():
    ft = FieldType(ElementType.FLOAT, (4,), Voltage)
    assert not ft.is_scalar
    assert ft.size == 4
    assert ft.rank == 1
    assert ft.unit.name == "Voltage"


def test_with_shape():
    ft = FieldType(ElementType.INT, (), Dimensionless)
    ft2 = ft.with_shape((8,))
    assert ft2.shape == (8,)
    assert ft.shape == ()
