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
rinse/
  __init__.py
  core.py
  bridge.py

docs/RINSE.md
specs/rinse.module.yaml
examples/rinse/rinse_core.py          # compatibility wrapper
examples/rinse/memory_bridge.py       # compatibility wrapper
examples/rinse/sample_input.json
tests/test_rinse_core.py
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

The first implementation is dependency-free Python. No LLM calls. No mutation
of source traces. Only derived interpretation records are written.

## Status

Experimental scaffold.
