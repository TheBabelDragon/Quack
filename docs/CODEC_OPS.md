# Native Quack codec operations

Quack can express codec work without a Node subprocess.

**Principle:** BabelCodec owns the *definition* of transformations.
Quack owns computational expression and may run a compatible pure
implementation for the subset it needs offline.

## Package: `quack.codec`

| Operation | Pure | Notes |
|-----------|------|--------|
| `encode_field` | yes | Field \u2192 feature.vector.v1 |
| `inspect_field` | yes | Shape / unit / preview |
| `canonicalize` | yes | babelcodec.canonical-json.v1 |
| `content_hash` | yes | Domain-separated SHA-256 |
| `validate_feature` | hybrid | Pure structural subset; escalates to BabelCodec when available |

## Registry

```python
from quack.codec import get_registry

reg = get_registry()
for op in reg.list_ops():
    print(op.name, op.provider, op.pure)
```

## Parity

When `BABELCODEC_ROOT` is set, tests assert pure canonicalize text and
content hashes match the BabelCodec Node worker for the same feature
descriptor.

## Contract versioning

- Integration protocol: `quack.babelcodec.v1` (subprocess worker)
- Native codec surface: `quack.codec.v1` (pure / registry)
