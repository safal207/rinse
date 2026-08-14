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

## Reflection Graph Engine v0.2

RINSE now also supports versioned, evidence-bound reinterpretation:

```text
immutable traces
  -> reflection record v1
  -> new evidence
  -> reflection record v2 --SUPERSEDES--> v1
  -> non-executable Kairos candidate
```

The older interpretation remains in history. The graph derives its effective
status as `SUPERSEDED`; no source trace or previous record is rewritten.

Supported relations:

```text
SUPPORTED_BY
CONTRADICTED_BY
SUPERSEDES
REFINES
```

Run the TRACE example:

```bash
python -m rinse.reflection_graph \
  examples/rinse/trace_reinterpretation_v0.2.json
```

Expected verdict:

```text
ACCEPT_WITH_LIMITS
```

The active interpretation remains bounded because expression change, cellular
effect, organism phenotype, and fitness advantage are still missing. Every
handoff remains:

```text
status: CANDIDATE
execution_allowed: false
classification: REFLECTION_ONLY
```

See [`docs/REFLECTION_GRAPH_V0_2.md`](docs/REFLECTION_GRAPH_V0_2.md) and
[`docs/adr/005-versioned-reflection-graph.md`](docs/adr/005-versioned-reflection-graph.md).

## Repository layout

```text
rinse/
  __init__.py
  core.py
  bridge.py
  reflection_graph.py
  validation.py
  adapters/
    __init__.py
    ttrace_jsonl.py

docs/RINSE.md
docs/PHILOSOPHY.md
docs/REFLECTION_GRAPH_V0_2.md
docs/adr/005-versioned-reflection-graph.md
docs/integrations/liminaldb-reader-sketch.md
docs/integrations/cml-drp-evidence-linking.md
specs/rinse.module.yaml
schemas/trace_event.schema.json
schemas/interpretation_record.schema.json
schemas/reflection_record.schema.json
schemas/reflection_graph.schema.json
examples/rinse/rinse_core.py          # compatibility wrapper
examples/rinse/memory_bridge.py       # compatibility wrapper
examples/rinse/sample_input.json
examples/rinse/expected_output_shape.json
examples/rinse/trace_reinterpretation_v0.2.json
examples/rinse/liminaldb_export_sample.json
examples/rinse/cml_drp_evidence_example.json
tests/fixtures/sample_traces.json
tests/fixtures/sample_interpretations.golden.json
tests/fixtures/sample_ttrace.jsonl
tests/test_rinse_core.py
tests/test_reflection_graph.py
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

Build a versioned reflection graph:

```bash
rinse-reflect examples/rinse/trace_reinterpretation_v0.2.json
```

Compatibility wrappers are still available:

```bash
python examples/rinse/rinse_core.py examples/rinse/sample_input.json
python examples/rinse/memory_bridge.py examples/rinse/sample_input.json ./rinse_interpretations.jsonl
```

## Python API

Legacy one-trace interpretation remains available:

```python
from rinse import interpret, run

trace = {
    "id": "trace-001",
    "text": "I am anxious because the deadline is close.",
}

record = interpret(trace)
records = run([trace])
```

Versioned reflection records use explicit timestamps and evidence:

```python
from rinse import create_reflection_record, build_reflection_graph

record = create_reflection_record(
    subject_id="case-001",
    statement="The association does not yet establish causality.",
    status="SUPPORTED_WITH_LIMITS",
    source_trace_ids=["trace-001", "trace-002"],
    evidence_relations=[
        {"type": "SUPPORTED_BY", "ref": "proofpath:C10"},
    ],
    missing_evidence=["cellular effect", "organism phenotype"],
    valid_from="2026-07-31T09:00:00Z",
    recorded_time="2026-07-31T09:00:00Z",
    reviewed_time="2026-07-31T09:05:00Z",
    confidence=0.81,
    proposed_target_state="request missing causal evidence",
)

graph = build_reflection_graph([record])
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

Reflection records have stricter semantic validation through
`validate_reflection_record` and `validate_reflection_graph`. Those checks bind
digests, temporal order, status/evidence combinations, relation targets, cycles,
and the non-executable authority boundary.

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

## LiminalDB / Mirror Timeline sketch

RINSE can also sit above LiminalDB / Mirror Timeline-style memory exports as a
read-only interpretation layer. See
[`docs/integrations/liminaldb-reader-sketch.md`](docs/integrations/liminaldb-reader-sketch.md)
and [`examples/rinse/liminaldb_export_sample.json`](examples/rinse/liminaldb_export_sample.json).

## CML / DRP evidence-linking example

RINSE can link derived interpretations back to CML / DRP-style evidence without
owning or rewriting that evidence. See
[`docs/integrations/cml-drp-evidence-linking.md`](docs/integrations/cml-drp-evidence-linking.md)
and [`examples/rinse/cml_drp_evidence_example.json`](examples/rinse/cml_drp_evidence_example.json).

For stable contract examples, see:

```text
schemas/trace_event.schema.json
schemas/interpretation_record.schema.json
schemas/reflection_record.schema.json
schemas/reflection_graph.schema.json
examples/rinse/expected_output_shape.json
examples/rinse/trace_reinterpretation_v0.2.json
```

The implementation is dependency-free Python. No LLM calls. No mutation of
source traces. Only derived interpretation and reflection records are written.

## Tests

```bash
python -m compileall rinse examples
python -m unittest discover -s tests -v
python -m rinse.core examples/rinse/sample_input.json
python -m rinse.reflection_graph examples/rinse/trace_reinterpretation_v0.2.json
```

## Golden-output workflow

Golden-output tests lock down deterministic interpretation behavior. They
normalize generated fields such as `id` and `produced_at`, then compare stable
fields like emotions, signals, causal links, insight, clarity, next step, and
source trace ids.

Only update `tests/fixtures/sample_interpretations.golden.json` when a pipeline
change intentionally changes interpretation behavior. Generated fields should
remain represented as `<generated>`.

Reflection graph records are deterministic without output normalization because
callers supply all timestamps and stable semantic input.

## Status

Experimental scaffold with a deterministic v0.2 reflection graph layer.
