# Quack

**Quack is a field-oriented programming language.**

Everything is a Field.  
Scalars are degenerate fields.  
Geometry is semantic information.  
Physical units participate in typing.  
The compiler lowers programs into an inspectable Field IR.

Quack is the intended field-oriented language / semantic layer for the TheBabelDragon ecosystem. It is designed to eventually express MetaField computations and lower into tensor/dataflow/FPGA-oriented execution — without requiring any of those systems at v0.1.

```
Quack source
    ↓
AST
    ↓
semantic model
    ↓
Field IR
    ↓
┌───────────────┬──────────────────┐
│               │                  │
Simulator    Tensor/Dataflow    future FPGA
               lowering           backend
│               │
└───────→ MetaField ←─────────────┘
               │
           WaveBridge
               │
             Aurora
```

v0.1 is independently installable and testable. It does **not** import MetaField, WaveBridge, TensorGate, or any FPGA toolchain.

## Project purpose

Quack makes the Field the central abstraction:

- A scalar is a one-element field (shape `()`).
- Field construction retains explicit shape.
- Broadcasting is explicit — never silent.
- Units are part of the type system; incompatible dimensions are rejected with diagnostics.
- Duck is a legitimate semantic field value (shared concept with MetaField), not a joke.

The compiler is a real small pipeline: lexer → parser → AST → semantic analysis → Field IR → simulator backend.

## Architecture

```
source
  → lexer
  → parser
  → AST
  → semantic analysis
  → Field IR          ← independent of parser AST
  → backend (simulator today; MetaField/tensor/FPGA later)
```

Field IR is deliberately separate from the parser AST so that future backends can consume a clean, shape- and unit-explicit intermediate representation without redesigning the language.

## Language overview (v0.1)

Deliberately small surface:

```
# comment
x := 4
y := field[4](1, 2, 3, 4)
z := broadcast(x, 4)
result := y + z
print(result)

v : Voltage := 12
r : Resistance := 4
i := v / r          # unit becomes Current

duck := duck_field(1)
```

| Form | Meaning |
|------|---------|
| `42` / `3.14` | Scalar field, shape `()` |
| `name` | Reference |
| `a + b` / `-` / `*` / `/` | Element-wise arithmetic (equal shapes required) |
| `field[N](e1, …, eN)` | 1-D field of shape `(N,)` |
| `broadcast(x, N)` | Explicit scalar → length-N field |
| `duck_field(v)` | Typed one-element Duck field |
| `f[i]` | Index (result is scalar field) |
| `name : Unit := expr` | Declaration with unit annotation |
| `print(expr)` | Emit value (simulator) |

No silent broadcasting. Shape mismatches and unit incompatibilities produce diagnostics with source locations.

## Installation

```bash
# from clone
pip install -e ".[dev]"

# or run without install
PYTHONPATH=. python -m quack.cli run examples/fields.quack
```

Requires Python ≥ 3.10. No runtime dependencies beyond the standard library.

## CLI usage

```bash
quack check examples/fields.quack   # parse + type-check
quack ir    examples/fields.quack   # print Field IR
quack run   examples/fields.quack   # execute with simulator
```

Example IR output:

```
module {
  x : Field[int, ()] = 4
  y : Field[int, (4,)] = field[4](1, 2, 3, 4)
  z : Field[int, (4,)] = broadcast(x, 4)
  result : Field[int, (4,)] = (y + z)
  print result
  ...
}
```

## Examples

| File | Demonstrates |
|------|----------------|
| `examples/hello.quack` | Scalars as fields, arithmetic |
| `examples/fields.quack` | Construction, explicit broadcast, indexing |
| `examples/physics.quack` | Unit annotations (Ohm's law) |
| `examples/duck.quack` | Duck as a typed one-element field |

## Development setup

```bash
git clone https://github.com/TheBabelDragon/Quack.git
cd Quack
pip install -e ".[dev]"
pytest -v
```

## Testing

```bash
pytest -v
```

Coverage includes:

- Lexing and parsing
- Scalar-as-field semantics
- Field construction and shapes
- Indexing bounds
- Explicit broadcasting (and rejection of silent broadcast)
- Unit compatibility / incompatibility
- Semantic diagnostics
- IR generation
- Deterministic simulation
- Duck field execution
- Full pipeline integration (source → AST → semantic → IR → simulator)

## Current limitations (v0.1)

- Rank primarily 0–1; higher ranks are shape-representable but not fully exercised
- Small fixed set of units (Dimensionless, Voltage, Resistance, Current, Mass, Length, Time)
- No control flow, functions, or modules beyond a single program
- Simulator only — no MetaField adapter, no tensor lowering, no FPGA backend
- Topology is recorded but not yet used for non-trivial geometric operations

## Future hardware backend

Intended (not implemented) path:

```
Quack
  ↓
Field IR
  ↓
scheduling / dataflow
  ↓
tensor / dataflow representation
  ↓
FPGA backend
```

The IR keeps shape, unit, and operation structure explicit so a hardware backend can consume it without language redesign.

## MetaField relationship

Quack is designed as the field-oriented language layer that can later lower into MetaField:

```
Quack Field
    ↓
Field IR
    ↓
MetaField adapter / lowering   ← not present in v0.1
    ↓
MetaField state
```

- Quack does **not** depend on MetaField at runtime.
- No MetaField APIs are invented or assumed.
- Duck is intentionally the shared semantic concept with MetaField's Duck/Quack idea: a legitimate typed field value, not a naming collision.
- Integration remains a future boundary, not a fake present dependency.

## License

MIT — see [LICENSE](LICENSE).
