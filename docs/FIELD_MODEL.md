# Field Model

Everything is a Field.

A scalar is a one-element Field with shape `()`.

## Rank-N shape contract

| Rank | Shape example | Meaning |
|------|---------------|---------|
| 0 | `()` | Scalar (strict) |
| 1 | `(N,)` | Vector / 1-D field |
| 2 | `(R, C)` | Matrix / 2-D field |
| N | `(D1, …, Dn)` | Higher-rank regular grid |

**Invariants**

- Dimensions are positive integers; `0` or negative dimensions are rejected.
- Total element count = product of dimensions (`()` → 1).
- Storage is contiguous and **row-major** (last index varies fastest).
- Shape metadata and storage length are kept consistent; divergence raises.
- Scalar shape is strictly `()`. The one-element vector `(1,)` is distinct.

### Indexing

```
m[i, j]     # multi-index matching rank
m[k]        # single linear index (flattened row-major) for any rank
```

Result is always a scalar field.

### Topology

| Topology | Typical shape |
|----------|---------------|
| `point`  | `()` |
| `linear` | `(N,)` |
| `grid2d` | `(R, C)` |
| `grid3d` | `(D1, D2, D3)` |

Topology is logical metadata; physical storage remains contiguous row-major.
