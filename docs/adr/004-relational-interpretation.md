# ADR 004: Relational interpretation model

## Status

Accepted.

## Context

RINSE derives interpretations from traces. It may include emotional signals, but
it should not be framed as an emotional intelligence system or emotion analyzer.

The core invariant remains:

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

A trace often marks more than an isolated event. It can also show that a
relation occurred between a subject and an object: a person and a task, an agent
and a decision, a human and a message, a system and a state change.

## Decision

RINSE is framed as a relational interpretation layer.

It does not decide what something means. It helps reveal what became significant
between a subject and an object.

RINSE should model interpretation using this conceptual sequence:

```text
Subject
Object
Relation
Trace
Significance
Interpretation
Action
```

RINSE may use emotion as a signal, but emotion is not the authority over meaning.

```text
Emotion is signal, not sovereignty.
```

## Consequences

### Positive

- RINSE is not reduced to sentiment or emotion analysis.
- The project can represent human meaning-making without claiming to replace it.
- Objects are not reduced to inert data; they can be understood through their relation to subjects.
- The existing trace immutability invariant remains central.
- The framing supports human-AI workflows where meaning is proposed, reviewed, and refined.

### Negative

- The philosophy becomes more ambitious and requires careful language.
- Contributors may need guidance to avoid making RINSE sound like it has final access to meaning.
- Future APIs may need to distinguish emotional signals from relational significance.

## Notes

RINSE does not take meaning away from the human.
It helps reveal where meaning began to appear.

```text
Meaning emerges between subject and object.
```
