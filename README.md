# RINSE

**Reflective Integrative Neural Self-Evolver**

RINSE is a reflective integration layer for human and agent memory systems. It
reads experience traces, filters noise, detects emotional and causal patterns,
and produces structured insights without mutating the underlying ground-truth
memory.

```text
T-Trace remembers what happened.
TTM / LiminalDB preserves what became traceable.
RINSE understands what it may mean.
```

## One-sentence claim

RINSE turns memory into structured understanding while keeping trace truth
immutable.

## Core boundary

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

## Philosophy

RINSE is built on a simple distinction: traces are preserved evidence;
interpretations are provisional readings.

```text
A trace is sacred. An interpretation is provisional.
```

For the philosophical boundary behind the project, see
[`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md).

## Minimal pipeline

```text
experience / trace
  -> noise filtering
  -> signal detection
  -> emotion tagging
  -> causal pattern extraction
  -> insight synthesis
  -> clarity scoring
  -> next-step suggestion
  -> derived interpretation record
```

## Repository layout

```text
rinse/
  __init__.py
  core.py
  bridge.py
  validation.py
  adapters/
    __init__.py
    ttrace_jsonl.py

docs/RINSE.md
docs/PHILOSOPHY.md
specs/rinse.module.yaml
schemas/trace_event.schema.json
schemas/interpretation_record.schema.json
examples/rinse/rinse_core.py          # compatibility wrapper
examples/rinse/memory_bridge.py       # compatibility wrapper
examples/rinse/sample_input.json
examples/rinse/expected_output_shape.json
tests/fixtures/sample_traces.json
tests/fixtures/sample_interpretations.golden.json
tests/fixtures/sample_ttrace.jsonl
tests/test_rinse_core.py
tests/test_golden_outputs.py
tests/test_ttrace_jsonl_adapter.py
tests/test_validation.py
```

## Quick start

Run the importable package module:

```bash
python -m rinse.core examples/rinse/sample_input.json
```

Write derived interpretations to JSONL:

```bash
python -m rinse.bridge examples/rinse/sample_input.json ./rinse_interpretations.jsonl
```

Compatibility wrappers are still available:

```bash
python examples/rinse/rinse_core.py examples/rinse/sample_input.json
python examples/rinse/memory_bridge.py examples/rinse/sample_input.json ./rinse_interpretations.jsonl
```

## Python API

```python
from rinse import interpret, run

trace = {
    "id": "trace-001",
    "text": "I am anxious because the deadline is close.",
}

record = interpret(trace)
records = run([trace])
```

## Structural validation

RINSE includes dependency-free structural validation helpers for project-critical
trace and interpretation fields. These helpers do not implement full JSON Schema
validation; they provide lightweight checks for the reference pipeline.

```python
from rinse import (
    validate_trace_event,
    validate_interpretation_record,
    interpret,
)

trace = {
    "id": "trace-001",
    "text": "I am anxious because the deadline is close.",
    "context": {},
}

validate_trace_event(trace)
record = interpret(trace)
validate_interpretation_record(record)
```

## T-Trace JSONL adapter

RINSE includes a read-only adapter for T-Trace-style JSONL streams:

```python
from rinse import run
from rinse.adapters import TTraceJsonLinesSource

source = TTraceJsonLinesSource("tests/fixtures/sample_ttrace.jsonl")
records = run(list(source.read_traces()))
```

The adapter reads JSONL line by line, skips blank lines, normalizes common field
names such as `id` / `trace_id` / `event_id` and `text` / `message` / `content`,
and never writes to the source file.

For stable contract examples, see:

```text
schemas/trace_event.schema.json
schemas/interpretation_record.schema.json
examples/rinse/expected_output_shape.json
```

The first implementation is dependency-free Python. No LLM calls. No mutation
of source traces. Only derived interpretation records are written.

## Tests

```bash
python -m compileall rinse examples
python -m unittest discover -s tests -v
python -m rinse.core examples/rinse/sample_input.json
```

## Golden-output workflow

Golden-output tests lock down deterministic interpretation behavior. They
normalize generated fields such as `id` and `produced_at`, then compare stable
fields like emotions, signals, causal links, insight, clarity, next step, and
source trace ids.

Only update `tests/fixtures/sample_interpretations.golden.json` when a pipeline
change intentionally changes interpretation behavior. Generated fields should
remain represented as `<generated>`.

## Status

Experimental scaffold.
