# ADR 005: Versioned reflection graph

## Status

Accepted.

## Context

RINSE v0.1 creates one derived interpretation from one trace. That is useful for
a deterministic scaffold, but it cannot express how an interpretation changes
when new evidence arrives. It also cannot distinguish a stable interpretation
identity from the digest of its current evidence and relations.

The project invariant remains:

```text
Meaning may change.
Trace must not.
```

RINSE needs to model reinterpretation without mutating the source trace, the
prior interpretation, CML/ProofPath evidence, or any durable LiminalDB record.

## Decision

RINSE v0.2 adds an immutable reflection-record model and a deterministic graph
projection.

Each reflection record contains:

- a stable content-derived version identity;
- a full digest that binds evidence, relations, time, confidence, candidate
  transition, and authority boundaries;
- one or more immutable source trace references;
- explicit `SUPPORTED_BY` and `CONTRADICTED_BY` evidence relations;
- explicit `SUPERSEDES` and `REFINES` interpretation relations;
- valid, recorded, and reviewed time;
- an explicit missing-evidence set;
- a non-executable candidate transition for a governing layer such as Kairos.

The graph projection derives the effective `SUPERSEDED` state. It does not
rewrite the old record.

```text
old interpretation record  -- remains immutable
          ^
          |
       SUPERSEDES
          |
new interpretation record  -- new immutable version
```

Stable IDs and full digests serve different purposes:

```text
stable id -> which interpretation version is this?
full digest -> exactly which evidence and relations did it contain?
```

The engine rejects:

- source or evidence mutation authority;
- truth or execution authority;
- executable candidate transitions;
- invalid status/evidence combinations;
- missing predecessors;
- cross-subject reinterpretation links;
- reinterpretation of a later record;
- self-links and supersession/refinement cycles;
- digest or stable-identity mismatches.

## Kairos boundary

RINSE may propose a transition, but it may not authorize it:

```text
RINSE reflection
  -> REINTERPRETATION_CANDIDATE
  -> execution_allowed: false
  -> Kairos review
```

RINSE interprets. Kairos governs transition admissibility.

## Consequences

### Positive

- interpretations can mature without falsifying history;
- evidence support and contradiction remain inspectable;
- multiple traces can contribute to one reading;
- supersession is explicit and reversible;
- graph outputs are deterministic and digest-bound;
- RINSE can close the reflective loop with Kairos, CML, ProofPath, and
  LiminalDB while preserving layer ownership.

### Negative

- callers must supply explicit timestamps;
- richer records require more validation and documentation;
- competing successors can create a fork that requires review;
- RINSE still does not determine scientific truth or authorize action.
