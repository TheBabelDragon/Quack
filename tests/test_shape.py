"""Rank-N shape model: products, strides, coordinates, bounds."""

import pytest

from quack.shape import (
    coords_from_offset,
    format_shape,
    in_bounds,
    is_scalar,
    is_vector,
    offset,
    rank,
    size,
    strides,
    validate_shape,
)


def test_scalar_shape():
    assert validate_shape(()) == ()
    assert size(()) == 1
    assert rank(()) == 0
    assert is_scalar(())
    assert not is_vector(())
    assert strides(()) == ()
    assert offset((), ()) == 0
    assert coords_from_offset((), 0) == ()


def test_vector_shape():
    s = validate_shape((4,))
    assert size(s) == 4
    assert rank(s) == 1
    assert not is_scalar(s)
    assert is_vector(s)
    assert strides(s) == (1,)
    assert offset(s, (2,)) == 2
    assert coords_from_offset(s, 3) == (3,)


def test_matrix_shape():
    s = validate_shape((2, 3))
    assert size(s) == 6
    assert rank(s) == 2
    assert strides(s) == (3, 1)
    assert offset(s, (1, 2)) == 5
    assert coords_from_offset(s, 5) == (1, 2)
    assert coords_from_offset(s, 0) == (0, 0)
    assert coords_from_offset(s, 3) == (1, 0)


def test_rank3_shape():
    s = validate_shape((2, 3, 4))
    assert size(s) == 24
    assert rank(s) == 3
    assert strides(s) == (12, 4, 1)
    assert offset(s, (1, 2, 3)) == 1 * 12 + 2 * 4 + 3
    assert coords_from_offset(s, 23) == (1, 2, 3)


def test_invalid_dimensions():
    with pytest.raises(ValueError):
        validate_shape((0,))
    with pytest.raises(ValueError):
        validate_shape((2, -1))
    with pytest.raises(ValueError):
        validate_shape((2, 0, 3))


def test_offset_bounds():
    s = (2, 3)
    with pytest.raises(IndexError):
        offset(s, (2, 0))
    with pytest.raises(IndexError):
        offset(s, (0, 3))
    with pytest.raises(IndexError):
        offset(s, (0,))
    with pytest.raises(IndexError):
        offset(s, (0, 1, 2))


def test_in_bounds():
    s = (2, 3)
    assert in_bounds(s, (0, 0))
    assert in_bounds(s, (1, 2))
    assert not in_bounds(s, (2, 0))
    assert not in_bounds(s, (0, 3))


def test_format_shape():
    assert format_shape(()) == "()"
    assert format_shape((4,)) == "(4,)"
    assert format_shape((2, 3)) == "(2, 3)"


def test_one_element_vector_distinct_from_scalar():
    assert is_scalar(())
    assert not is_scalar((1,))
    assert size((1,)) == 1
    assert rank((1,)) == 1
    assert strides((1,)) == (1,)
