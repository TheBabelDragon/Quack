# Hardware Direction (not implemented in v0.1)

Intended future lowering:

```
Quack source
    ↓
Field IR          ← inspectable, shape- and unit-explicit
    ↓
scheduling / dataflow
    ↓
tensor / dataflow representation
    ↓
FPGA backend
```

## Why the IR is explicit

Field IR records:

- Constants and field constructions with concrete shapes
- Explicit broadcasts (never implicit)
- Arithmetic with preserved shape and unit metadata
- Indexing
- Unit annotations

A future hardware or tensor backend can therefore schedule operations, allocate buffers, and lower to dataflow without reconstructing shape or unit information from the source AST.

## Relationship to the ecosystem

```
Field IR
    → Simulator          (implemented)
    → Tensor/dataflow    (future)
    → MetaField adapter  (future)
    → FPGA backend       (future)
```

v0.1 ships only the simulator. No FPGA toolchain, no MetaField import, and no fake hardware path is present.
