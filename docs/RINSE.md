# RINSE — Reflective Integrative Neural Self-Evolver

RINSE is a reflective interpretation layer that sits above trace and memory
substrates. It does not own the truth of what happened; it owns the
understanding of what it may mean.

## Architectural boundary

```text
T-Trace        remembers what happened.
TTM / LiminalDB preserves what became traceable.
RINSE          understands what it may mean.
```

RINSE reads from substrates below it. It writes only to its own derived store.
A trace is never rewritten, redacted, or deleted by RINSE.

## Invariant

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

This is the only hard rule. Everything else is policy.

## Pipeline

The reference pipeline is intentionally small and synchronous.

1. **Ingest.** Receive a normalized trace event or batch.
2. **Noise filter.** Drop low-signal entries by simple heuristics
   (length, repetition, content-free tokens).
3. **Signal detection.** Identify candidate salient spans.
4. **Emotion tagging.** Attach coarse affective labels using a lexicon.
5. **Causal pattern extraction.** Link cause-like and effect-like fragments
   within a window.
6. **Insight synthesis.** Compose a short interpretation record.
7. **Clarity scoring.** Score how well-supported the interpretation is by the
   trace.
8. **Next-step suggestion.** Propose one concrete follow-up.
9. **Persist derived record.** Write the interpretation to the RINSE store
   with a back-reference to the source trace ids. Source traces are not
   modified.

## Data contracts

### Input: trace event

```json
{
  "id": "trace-...",
  "ts": "2026-05-07T12:00:00Z",
  "actor": "human|agent|system",
  "kind": "utterance|action|observation|state",
  "text": "...",
  "context": { "...": "..." }
}
```

### Output: interpretation record

```json
{
  "id": "rinse-...",
  "source_trace_ids": ["trace-..."],
  "emotions": ["..."],
  "signals": ["..."],
  "causal_links": [{"cause": "...", "effect": "..."}],
  "insight": "...",
  "clarity": 0.0,
  "next_step": "...",
  "produced_at": "2026-05-07T12:00:01Z"
}
```

## Non-goals (initial version)

- No LLM API calls.
- No external dependencies.
- No mutation of source traces.
- No cross-actor identity resolution.
- No long-term memory consolidation.

## Relation to other modules

- **T-Trace**: source of immutable event records.
- **TTM / LiminalDB**: durable substrate of what became traceable.
- **RINSE**: derives interpretations on top of both, without write-back.

## Roadmap (sketch)

- Reference pipeline with deterministic heuristics.
- Memory bridge adapter interface (read-only).
- Pluggable emotion lexicon and causal cue list.
- Optional LLM-backed synthesis as a separate, opt-in module.
