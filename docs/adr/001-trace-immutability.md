# ADR 001: Trace immutability

## Status

Accepted.

## Context

RINSE sits above trace and memory substrates. It reads source traces, derives interpretations, and writes only derived records.

The core invariant is:

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

If RINSE could rewrite, redact, or delete source traces, it would no longer be a reflective interpretation layer. It would become an owner of history.

That would weaken auditability because later interpretations could make their own evidence disappear.

## Decision

RINSE must treat source traces as immutable input evidence.

RINSE may:

- read trace events;
- filter low-signal traces from interpretation output;
- produce derived interpretation records;
- discard, replace, or supersede its own derived interpretations.

RINSE must not:

- mutate source trace files or source trace stores;
- redact source trace content;
- delete source trace records;
- rewrite source ids;
- hide which source traces produced an interpretation.

Every interpretation record should keep a back-reference to the source trace ids that made the interpretation possible.

## Consequences

### Positive

- RINSE remains auditable.
- Interpretations can evolve without corrupting source history.
- Downstream systems can compare old and new interpretations against the same evidence.
- Human reviewers can distinguish preserved evidence from provisional readings.

### Negative

- RINSE cannot fix bad upstream traces directly.
- Redaction, deletion, and retention policy must be handled by the owning substrate or governance layer, not by RINSE.
- Some workflows may need an explicit derived correction record rather than an in-place edit.

## Notes

This decision makes RINSE a meaning-refinement layer, not a ground-truth memory store.

```text
Clean the lens, not the evidence.
```
