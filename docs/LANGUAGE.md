# Quack Language (v0.1)

## Syntax overview

```
# comment
name := expression
name : Unit := expression
print(expression)
```

Programs are sequences of statements. There is no separate expression statement form beyond assignment and print.

## Expressions

| Form | Meaning |
|------|---------|
| `42` / `3.14` | Scalar field (shape `()`) |
| `name` | Reference to a previously bound field |
| `a + b` / `-` / `*` / `/` | Element-wise arithmetic; shapes must match |
| `field[N](e1, …, eN)` | Construct 1-D field of shape `(N,)` |
| `broadcast(x, N)` | Explicit scalar → length-N field |
| `duck_field(v)` | Typed one-element Duck field |
| `f[i]` | Index; result is a scalar field |

Unary minus is supported: `-x`.

## No silent broadcasting

```
y := field[4](1, 2, 3, 4)
x := 4
# r := y + x   # ERROR — shapes () and (4,) differ
r := y + broadcast(x, 4)   # OK
```

## Units

```
v : Voltage := 12
r : Resistance := 4
i := v / r          # result unit is Current
# bad := v + mass   # ERROR: incompatible dimensions
```

Unit annotations are checked at semantic analysis. Arithmetic operators respect dimensional rules for the small fixed set of units shipped in v0.1.

## Duck

```
duck := duck_field(1)
```

Produces a one-element field with element type `duck`. This is the same shared semantic concept as MetaField's Duck — a legitimate field value that flows through AST → IR → simulator like every other field.

## Determinism

Execution is deterministic. The simulator uses plain Python data structures; given the same source, the same Field IR and the same outputs are produced.
