# ADR 002: Deterministic-first pipeline

## Status

Accepted.

## Context

RINSE interprets traces into derived records. The first version must be easy to inspect, easy to test, and safe for contributors to modify.

The project intentionally starts without runtime dependencies, LLM API calls, or hidden model behavior.

The core invariant is:

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

A deterministic-first pipeline makes it possible to verify that this invariant is preserved and that interpretation changes are intentional.

## Decision

RINSE v0 uses deterministic mechanisms first:

- pure Python standard library code;
- explicit lexicons;
- explicit signal patterns;
- explicit causal cue extraction;
- JSON fixtures;
- golden-output regression tests;
- source immutability tests.

Changes to deterministic interpretation behavior should be visible through tests and golden fixture diffs.

## Consequences

### Positive

- Contributors can understand the full pipeline without external services.
- CI can run without secrets, network calls, or model access.
- Golden-output tests make behavioral drift visible.
- RINSE can serve as a stable reference implementation for later adapters.

### Negative

- The v0 pipeline is intentionally limited.
- Some interpretations will be coarse or incomplete.
- Heuristic parsing may miss valid patterns.
- Model-backed synthesis may eventually outperform the reference heuristics for expressiveness.

## Notes

Deterministic-first does not mean deterministic-only forever.

It means the project establishes a stable, auditable base before adding probabilistic or model-backed interpretation layers.

```text
Reference behavior first. Expressive synthesis later.
```
