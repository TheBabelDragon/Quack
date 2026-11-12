# Quack \u00d7 BabelCodec Field Interoperability

Optional integration layer. Quack remains an independently usable field-oriented language. BabelCodec remains the authoritative implementation of its own encoding, canonicalization, hashing, and feature-validation operations.

## Requirements (optional)

| Requirement | Notes |
|-------------|--------|
| Node.js \u2265 18 | On `PATH` |
| BabelCodec \u2265 0.12.1 | Local checkout |
| `BABELCODEC_ROOT` | Absolute path to that checkout |

Ordinary Quack (`check` / `ir` / `run`) does **not** need Node or BabelCodec.

## Protocol

Contract: `quack.babelcodec.v1`

Transport: single-shot JSON request on stdin \u2192 one JSON response on stdout. Diagnostics on stderr only. Subprocess, no shell, size + time bounds.

### Operations

| Op | Purpose |
|----|---------|
| `health` | Runtime version + capability probe |
| `validate_feature_vector` | BabelCodec `validateFeatureVector` |
| `canonicalize` | Canonical JSON text + bytes |
| `content_hash` | Domain-separated content identity |
| `validate_event` | BabelCodec neural event validation |

## Field \u2192 feature mapping

| Quack | BabelCodec `type` |
|-------|-------------------|
| INT scalar `()` | `int64` |
| FLOAT scalar `()` | `float64` |
| INT vector/tensor | `vector_fixed` + `dimensions` |
| FLOAT vector/tensor | `vector_fixed` + `dimensions` |
| DUCK | **rejected** |

Shape `(1,)` stays a vector. Large scalar ints use `{$i:"..."}`. Non-finite floats rejected. No silent clip/normalize.

## CLI

```bash
export BABELCODEC_ROOT=/path/to/BabelCodec
quack babelcodec health
quack babelcodec validate-field examples/fields.quack --field result
```

## Offline

No network access required. Worker imports BabelCodec from the local filesystem.
