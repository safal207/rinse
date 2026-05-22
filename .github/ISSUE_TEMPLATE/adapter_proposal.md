---
name: Adapter proposal
about: Propose a read-only source adapter for RINSE
labels: adapter
---

## Source substrate type

What kind of source should RINSE read from?

Examples:

- T-Trace JSONL
- local JSON file
- append-only event log
- memory export

## Read-only guarantee

How will the adapter avoid mutating the source substrate?

- [ ] Adapter only opens the source for reading.
- [ ] Adapter writes derived records somewhere else.
- [ ] Tests verify source content is unchanged.

RINSE must never mutate, redact, or delete source traces.

## Output sink behavior

Where should derived interpretation records be written?

Examples:

- stdout
- JSONL file
- separate derived store

## Example input

```json
{
  "id": "trace-...",
  "text": "..."
}
```

## Expected normalized RINSE trace shape

```json
{
  "id": "trace-...",
  "ts": "2026-05-07T12:00:00Z",
  "actor": "human|agent|system",
  "kind": "utterance|action|observation|state",
  "text": "...",
  "context": {}
}
```

## Acceptance criteria

- [ ] Adapter is read-only.
- [ ] Invalid input handling is documented.
- [ ] Fixture data is included.
- [ ] Tests verify source content remains unchanged.
- [ ] README or docs include a short usage example.
