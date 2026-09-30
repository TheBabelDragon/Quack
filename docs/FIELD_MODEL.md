# Field Model

Everything is a Field.

A scalar is a one-element Field with shape `()`.

## Components

| Aspect | Role |
|--------|------|
| Element type | `int`, `float`, or `duck` |
| Shape | Tuple of dimensions; `()` for scalar |
| Topology | Geometric arrangement (point, linear, …) |
| Unit | Dimensional annotation |
| Values | Contiguous element storage |

## Scalar as field

```
x := 4
```

semantically becomes a field with shape `()`, one value, and topology `point`.

This is not a special case bolted on later — it is the default representation of every numeric literal and every index result.

## Construction

```
y := field[4](1, 2, 3, 4)
```

produces a rank-1 field with shape `(4,)`. The element count must match the declared size; mismatches are diagnosed at semantic analysis.

## Broadcasting

Broadcasting is always explicit:

```
z := broadcast(x, 4)
```

The resulting shape is recorded in the Field IR. Silent broadcasting of mismatched shapes is rejected.

## Duck

`duck_field(v)` produces a typed one-element field with element type `duck`.

Duck is the same shared semantic concept as in MetaField: a legitimate field value, not a parser joke. It flows through AST → IR → simulator like any other field.

## Topology

Topology records geometric intent (point for scalars, linear for 1-D fields). In v0.1 it is carried as metadata; non-trivial geometric operations are deferred.
