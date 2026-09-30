"""Runtime Field tests."""

import pytest

from quack.fields import Field
from quack.types import ElementType
from quack.units import Dimensionless


def test_scalar_field():
    f = Field.scalar(4)
    assert f.shape == ()
    assert f.data == [4]
    assert f.get(0) == 4


def test_vector_field():
    f = Field.from_values([1, 2, 3, 4], (4,))
    assert f.shape == (4,)
    assert f.get(2) == 3


def test_index_bounds():
    f = Field.from_values([1, 2], (2,))
    with pytest.raises(IndexError):
        f.get(5)


def test_duck_element():
    f = Field.scalar(1, element=ElementType.DUCK)
    assert f.element is ElementType.DUCK
