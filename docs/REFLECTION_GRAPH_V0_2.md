# RINSE Reflection Graph Engine v0.2

RINSE v0.2 adds a deterministic graph for revising interpretations while
preserving source traces and prior readings.

## Layer role

```text
LiminalDB  preserves what became traceable.
CML        preserves causal memory.
ProofPath  binds claims to evidence paths.
RINSE      revises what the preserved history may mean.
Kairos     evaluates whether a proposed transition is admissible.
```

RINSE does not replace any of those layers. It produces a bounded reflection
candidate.

## Record lifecycle

A record declares one current reading:

```text
source traces
  -> evidence relations
  -> interpretation statement
  -> status and confidence
  -> missing evidence
  -> proposed transition candidate
```

A later record can point to an earlier record using:

- `SUPERSEDES`: the new reading replaces the earlier reading in the active graph;
- `REFINES`: the new reading narrows or clarifies the earlier reading without
  necessarily replacing it;
- `SUPPORTED_BY`: evidence supports the record;
- `CONTRADICTED_BY`: evidence weakens or disputes the record.

The prior record remains immutable. The graph derives its effective status as
`SUPERSEDED` when a later valid record points to it.

## Time model

Every record distinguishes:

- `valid_time`: when the interpretation is intended to apply;
- `recorded_time`: when the record was created;
- `reviewed_time`: when the interpretation was reviewed.

This prevents a later reinterpretation from pretending it was known earlier.

## Deterministic identity

The stable record ID binds:

- schema;
- subject;
- statement;
- validity window;
- recorded time.

The full digest additionally binds:

- status and confidence;
- source traces;
- evidence and interpretation relations;
- missing evidence;
- review time;
- proposed transition;
- authority boundaries.

This lets a version retain a stable identity while any evidence or relation
change produces a different digest.

## Status rules

| Declared status | Required boundary |
|---|---|
| `PROPOSED` | no truth claim |
| `SUPPORTED` | at least one `SUPPORTED_BY` relation |
| `SUPPORTED_WITH_LIMITS` | supporting evidence plus explicit missing evidence |
| `CONTESTED` | at least one `CONTRADICTED_BY` relation |
| `INSUFFICIENT_EVIDENCE` | explicit missing evidence |
| `RETIRED` | excluded from active candidates |

`SUPERSEDED` is an effective graph status, not a mutation of the source record.

## Graph verdicts

```text
ACCEPT              active readings are supported
ACCEPT_WITH_LIMITS  active reading is supported but evidence gaps remain
REVIEW              contest, insufficiency, or a supersession fork exists
HOLD                no active supported reading is ready
```

These verdicts describe interpretation readiness only. They are not scientific
truth verdicts and do not authorize execution.

## Kairos handoff

Every active record emits:

```json
{
  "kind": "REINTERPRETATION_CANDIDATE",
  "status": "CANDIDATE",
  "execution_allowed": false
}
```

Kairos may evaluate that candidate. RINSE cannot promote it to an action.

## TRACE example

Run:

```bash
python -m rinse.reflection_graph \
  examples/rinse/trace_reinterpretation_v0.2.json
```

The example preserves an earlier adaptive-benefit overclaim, then creates a new
bounded interpretation:

```text
functional enrichment is an association;
adaptive causality remains unresolved
```

The new record supersedes the old reading while retaining explicit missing
bridges:

```text
expression change
cellular effect
organism phenotype
fitness advantage
```

Expected graph verdict:

```text
ACCEPT_WITH_LIMITS
```

## Authority boundary

```text
classification: REFLECTION_ONLY
source_trace_mutation_authorized: false
evidence_mutation_authorized: false
truth_authorized: false
execution_authorized: false
```

RINSE cleans the reading, not the history.
