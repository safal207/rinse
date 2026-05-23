# CML / DRP evidence-linking example

## Purpose

This document shows how RINSE interpretation records can link back to CML /
DRP-style evidence without becoming the owner of that evidence.

RINSE derives provisional meaning from preserved traces. It does not own causal
truth, decision authority, or source evidence.

## Core invariant

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

For CML / DRP integrations, that means:

- CML / DRP owns the causal or decision evidence.
- RINSE may read normalized evidence traces.
- RINSE may produce derived interpretation records.
- RINSE must preserve source trace ids.
- RINSE must not rewrite CML causes, DRP decisions, or evidence lineage.

## Layer distinction

```text
CML / DRP evidence
  -> normalized RINSE trace
  -> RINSE derived interpretation
```

The layers answer different questions:

| Layer | Question | Ownership |
|---|---|---|
| CML | Why was this state/action permitted? | Causal permission and responsibility evidence. |
| DRP | Which decision/resolution path was taken? | Decision protocol evidence. |
| RINSE | What may this evidence mean for reflection or next action? | Provisional interpretation only. |

## Example source evidence

A CML / DRP-style record might preserve a decision with explicit evidence links:

```json
{
  "id": "evidence-001",
  "ts": "2026-05-07T12:00:00Z",
  "actor": "agent",
  "kind": "decision",
  "decision": "HOLD",
  "reason": "missing human confirmation",
  "permitted_by": "policy-human-review-required",
  "parent_cause": "trace-user-request-001",
  "text": "The action was held because human confirmation was missing.",
  "context": {
    "source": "cml-drp",
    "cml_record_id": "cml-001",
    "drp_decision_id": "drp-001"
  }
}
```

This source evidence remains owned by the CML / DRP layer.

## Normalized RINSE trace

RINSE can consume the record as a normal trace event:

```json
{
  "id": "evidence-001",
  "ts": "2026-05-07T12:00:00Z",
  "actor": "agent",
  "kind": "decision",
  "text": "The action was held because human confirmation was missing.",
  "context": {
    "source": "cml-drp",
    "decision": "HOLD",
    "reason": "missing human confirmation",
    "permitted_by": "policy-human-review-required",
    "parent_cause": "trace-user-request-001",
    "cml_record_id": "cml-001",
    "drp_decision_id": "drp-001"
  }
}
```

The normalization step may move CML / DRP-specific fields into `context`, but it
must not change the source evidence itself.

## Derived RINSE interpretation

A derived RINSE interpretation can then point back to the evidence trace:

```json
{
  "id": "rinse-example-001",
  "source_trace_ids": ["evidence-001"],
  "emotions": [],
  "signals": [],
  "causal_links": [
    {
      "cause": "human confirmation was missing",
      "effect": "The action was held"
    }
  ],
  "insight": "pattern: human confirmation was missing -> The action was held",
  "clarity": 0.6,
  "next_step": "note the trace and revisit tomorrow",
  "produced_at": "2026-05-07T12:00:01Z"
}
```

This interpretation is not a replacement for the source evidence. It is a
reading of that evidence.

## What RINSE must not do

RINSE must not:

- overwrite `permitted_by`;
- change the DRP decision;
- replace `parent_cause`;
- delete the evidence trace;
- claim final authority over why the action was allowed or held.

If a later interpretation is better, RINSE may supersede its own derived record,
but the source evidence remains intact.

## Useful framing

```text
CML preserves why permission existed.
DRP preserves which decision path was taken.
RINSE derives what the evidence may mean.
```

RINSE can help humans and agents reflect on patterns in evidence, but it must not
become the evidence ledger.
