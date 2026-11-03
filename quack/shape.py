"""
Rank-N shape model for Quack Fields.

Formal layout contract:
  - Dimensions are positive integers (or empty tuple for scalar).
  - Storage is contiguous, row-major (C-order).
  - Scalar shape is strictly ().
  - One-element vector is (1,) — distinct from scalar.
  - Strides, offsets and coordinate conversion are deterministic.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple, Union

Shape = Tuple[int, ...]
Coord = Tuple[int, ...]


def validate_shape(shape: Sequence[int], *, allow_scalar: bool = True) -> Shape:
    """Validate and normalize a shape.

    Raises ValueError on non-positive dimensions or non-integer values.
    Scalar () is allowed only when allow_scalar is True.
    """
    if not isinstance(shape, (tuple, list)):
        raise TypeError(f"shape must be a sequence of ints, got {type(shape).__name__}")
    dims = tuple(int(d) for d in shape)
    if dims == ():
        if not allow_scalar:
            raise ValueError("scalar shape () not allowed in this context")
        return ()
    for d in dims:
        if d < 1:
            raise ValueError(f"invalid dimension {d}: all dimensions must be >= 1")
    return dims


def rank(shape: Shape) -> int:
    return len(shape)


def size(shape: Shape) -> int:
    """Total number of elements (product of dimensions). Scalar () → 1."""
    if shape == ():
        return 1
    n = 1
    for d in shape:
        n *= d
    return n


def is_scalar(shape: Shape) -> bool:
    """True only for the empty tuple (). (1,) is a one-element vector."""
    return shape == ()


def is_vector(shape: Shape) -> bool:
    return len(shape) == 1


def strides(shape: Shape) -> Tuple[int, ...]:
    """Row-major (C-order) strides.

    For shape (D0, D1, ..., Dn-1):
      stride[i] = product of shape[j] for j > i
    Scalar () returns ().
    """
    if shape == ():
        return ()
    s: List[int] = [1] * len(shape)
    for i in range(len(shape) - 2, -1, -1):
        s[i] = s[i + 1] * shape[i + 1]
    return tuple(s)


def offset(shape: Shape, coords: Sequence[int]) -> int:
    """Linear offset of multi-dimensional coordinates (row-major).

    Raises IndexError if any coordinate is out of bounds or rank mismatches.
    """
    shape = validate_shape(shape)
    if shape == ():
        if len(coords) != 0 and not (len(coords) == 1 and coords[0] == 0):
            raise IndexError(f"scalar field has no multi-index; got {coords}")
        return 0
    if len(coords) != len(shape):
        raise IndexError(
            f"coordinate rank {len(coords)} does not match shape rank {len(shape)}"
        )
    offs = 0
    st = strides(shape)
    for c, d, stride in zip(coords, shape, st):
        if not isinstance(c, int):
            raise TypeError(f"coordinate must be int, got {type(c).__name__}")
        if c < 0 or c >= d:
            raise IndexError(f"coordinate {c} out of bounds for dimension size {d}")
        offs += c * stride
    return offs


def coords_from_offset(shape: Shape, linear: int) -> Coord:
    """Inverse of offset: linear index → coordinate tuple (row-major)."""
    shape = validate_shape(shape)
    n = size(shape)
    if linear < 0 or linear >= n:
        raise IndexError(f"linear index {linear} out of range for size {n}")
    if shape == ():
        return ()
    st = strides(shape)
    coords: List[int] = []
    remaining = linear
    for s in st:
        coords.append(remaining // s)
        remaining %= s
    return tuple(coords)


def in_bounds(shape: Shape, coords: Sequence[int]) -> bool:
    try:
        offset(shape, coords)
        return True
    except (IndexError, TypeError, ValueError):
        return False


def linear_index_valid(shape: Shape, index: int) -> bool:
    n = size(shape)
    return 0 <= index < n


def same_shape(a: Shape, b: Shape) -> bool:
    return tuple(a) == tuple(b)


def shape_product_str(shape: Shape) -> str:
    if shape == ():
        return "()"
    return "×".join(str(d) for d in shape)


def format_shape(shape: Shape) -> str:
    if shape == ():
        return "()"
    if len(shape) == 1:
        return f"({shape[0]},)"
    return "(" + ", ".join(str(d) for d in shape) + ")"
