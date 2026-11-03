# Quack Language (v0.2)

## Expressions

| Form | Meaning |
|------|---------|
| `42` / `3.14` | Scalar field (shape `()`) |
| `field[N](e1, …, eN)` | 1-D field of shape `(N,)` |
| `field[R,C](…)` / `field[D1,…,Dn](…)` | Rank-N field (row-major) |
| `broadcast(x, N)` | Explicit scalar → length-N field |
| `f[i]` / `f[i,j,…]` | Linear or multi-index (result is scalar) |

## Rank-N construction and indexing

```
m := field[2,3](1, 2, 3, 4, 5, 6)   # shape (2, 3), row-major
a := m[1, 2]                         # multi-index → 6
b := m[5]                            # linear index → 6
```

Invalid dimensions, element-count mismatches, out-of-bounds constant indices, and rank mismatches on multi-index produce diagnostics with source locations.

## No silent broadcasting

```
y := field[4](1, 2, 3, 4)
x := 4
# r := y + x   # ERROR — shapes () and (4,) differ
r := y + broadcast(x, 4)   # OK
```
