# LiminalDB / Mirror Timeline reader sketch

## Purpose

This document sketches a read-only path from LiminalDB / Mirror Timeline-style
memory exports into normalized RINSE traces.

RINSE is substrate-neutral. It reads preserved evidence from lower layers and
writes only derived interpretation records.

## Core invariant

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

For this integration, that means:

- LiminalDB / Mirror Timeline owns the source memory export.
- RINSE may read the export.
- RINSE may normalize records into its trace input shape.
- RINSE may write derived interpretation records to a separate store.
- RINSE must not mutate, redact, reorder, or delete the source export.

## Boundary

```text
LiminalDB / Mirror Timeline export
  -> read-only reader
  -> normalized RINSE trace events
  -> RINSE interpretation pipeline
  -> derived RINSE interpretation records
```

The reader is a translation boundary, not an ownership boundary.

RINSE does not become the system of record for the memory substrate. It becomes
a derived interpretation layer above it.

## Example source export shape

A LiminalDB / Mirror Timeline export may look like this:

```json
{
  "timeline_id": "mirror-timeline-demo",
  "records": [
    {
      "memory_id": "mem-001",
      "created_at": "2026-05-07T12:00:00Z",
      "speaker": "human",
      "event_kind": "utterance",
      "body": "I am anxious because the deadline is close.",
      "metadata": {
        "channel": "journal",
        "project": "RINSE"
      }
    }
  ]
}
```

## Normalized RINSE trace shape

The reader should map each source record into the minimal RINSE trace shape:

```json
{
  "id": "mem-001",
  "ts": "2026-05-07T12:00:00Z",
  "actor": "human",
  "kind": "utterance",
  "text": "I am anxious because the deadline is close.",
  "context": {
    "source": "liminaldb",
    "timeline_id": "mirror-timeline-demo",
    "project": "RINSE",
    "channel": "journal"
  }
}
```

## Suggested field mapping

| Source field | RINSE field | Notes |
|---|---|---|
| `memory_id` | `id` | Stable source identifier. |
| `created_at` | `ts` | Source timestamp. |
| `speaker` | `actor` | Should map to `human`, `agent`, or `system` when possible. |
| `event_kind` | `kind` | Should map to `utterance`, `action`, `observation`, or `state` when possible. |
| `body` | `text` | Human-readable content interpreted by RINSE. |
| `metadata` | `context` | Source-specific metadata carried through without ownership transfer. |
| `timeline_id` | `context.timeline_id` | Preserves export lineage. |

## Derived output location

Derived interpretation records should be written somewhere separate from the
source export, for example:

```text
rinse_interpretations.jsonl
```

or a dedicated derived store:

```text
rinse/derived_interpretations/*
```

A derived record should keep `source_trace_ids` pointing back to the normalized
source ids. It should not replace or rewrite the original memory records.

## Non-goals

This sketch does not define:

- the full LiminalDB export schema;
- a production storage adapter;
- write-back into LiminalDB;
- retention, deletion, or redaction policy;
- cross-actor identity resolution.

Those belong to their owning layers.

## Future implementation path

A future adapter could be added as:

```text
rinse/adapters/liminaldb_export.py
```

Possible API:

```python
class LiminalDbExportSource:
    def __init__(self, path): ...
    def read_traces(self): ...
```

Acceptance criteria for that future adapter:

- opens the source export only for reading;
- validates required fields;
- maps records into normalized RINSE traces;
- includes fixture data and tests;
- verifies the source export is unchanged after reading;
- writes derived interpretations only through a separate sink.
