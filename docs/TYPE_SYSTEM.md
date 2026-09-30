# Type System

## FieldType

```
FieldType(element, shape, unit)
```

- `element`: `int` | `float` | `duck`
- `shape`: `()` or `(n,)` (higher rank representable; v0.1 focuses on rank 0–1)
- `unit`: dimensional unit (default `Dimensionless`)

## Checking rules (v0.1)

1. Arithmetic requires equal shapes (no silent broadcast).
2. `+` / `-` require compatible units; result keeps that unit.
3. `*` multiplies dimensions; `/` divides dimensions (e.g. Voltage / Resistance → Current).
4. `broadcast` requires a scalar source; result shape is `(size,)`.
5. `field[N](...)` requires exactly `N` elements.
6. Indexing with a constant checks bounds statically when possible; runtime checks otherwise.
7. Unit annotations must be compatible with the expression's unit (or the expression must be dimensionless).

## Units provided

| Name | Role |
|------|------|
| Dimensionless | Default |
| Voltage | Electric potential |
| Resistance | Ohm |
| Current | Ampere (derived: Voltage / Resistance) |
| Mass | Mass |
| Length | Length |
| Time | Time |

This is a deliberately small dimensional system sufficient to demonstrate semantic checking. It is not a complete SI algebra.
