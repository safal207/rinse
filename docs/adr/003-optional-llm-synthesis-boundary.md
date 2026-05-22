# ADR 003: Optional LLM synthesis boundary

## Status

Accepted.

## Context

RINSE may eventually benefit from model-backed synthesis: richer summaries, more nuanced interpretations, better language, or higher-level pattern recognition.

However, RINSE's core role is not to produce impressive prose. Its core role is to derive accountable interpretations from preserved traces.

The core invariant is:

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

An LLM-backed synthesis layer must not weaken this invariant or hide provenance.

## Decision

LLM-backed synthesis is allowed only as an optional, separate, opt-in layer.

The deterministic reference pipeline remains the baseline.

Any future LLM synthesis module must:

- be disabled by default;
- never mutate source traces;
- preserve source trace ids in every derived record;
- make model involvement explicit in metadata;
- keep prompts, model identifiers, and synthesis parameters inspectable where practical;
- produce derived interpretations, not source truth;
- remain replaceable by the deterministic reference path.

The core package should not require an LLM provider, API key, or network access.

## Consequences

### Positive

- RINSE can later support richer interpretation without compromising the reference implementation.
- Users can choose between deterministic baseline behavior and experimental synthesis.
- Auditors can identify which records were produced by heuristics and which used model-backed synthesis.
- The project avoids vendor lock-in at the core layer.

### Negative

- LLM-backed output cannot be treated as deterministic reference behavior.
- Additional provenance metadata will be required.
- Tests for model-backed synthesis must avoid pretending nondeterministic output is stable.
- Some users may expect model-backed synthesis to be the default; RINSE intentionally does not do that in core.

## Notes

LLMs may help refine language. They must not become the hidden owner of meaning.

```text
Model synthesis may assist interpretation.
It must not replace provenance.
```
