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
docs/RINSE.md
specs/rinse.module.yaml
schemas/interpretation_record.schema.json
examples/rinse/rinse_core.py
examples/rinse/memory_bridge.py
examples/rinse/sample_input.json
examples/rinse/expected_output_shape.json
tests/test_rinse_core.py
```

## Quick start

```bash
python examples/rinse/rinse_core.py examples/rinse/sample_input.json
```

For a stable contract example, see:

```text
examples/rinse/expected_output_shape.json
schemas/interpretation_record.schema.json
```

The first implementation is dependency-free Python. No LLM calls. No mutation
of source traces. Only derived interpretation records are written.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Status

Experimental scaffold.
