# Career RINSE

Career RINSE turns fragmented career-history traces into evidence-backed,
provisional interpretations and review-only next actions.

It is designed for archives such as email threads, Drive documents, applicant
tracking exports, interview notes, and test assignments.

## Boundary

Career RINSE does not rewrite career history.

```text
Trace          -> what is directly preserved
Evidence class -> how strongly the trace supports a claim
Interpretation -> what the grouped traces may mean
Action queue   -> what a human may choose to do next
```

The source traces are never mutated. Derived interpretations remain provisional.
The module never sends email, messages recruiters, or authorizes outreach.

```text
Past evidence remains intact.
Meaning may be refined.
Action requires review.
```

## Pipeline

```text
career traces
  -> normalization
  -> evidence classification
  -> company / role grouping
  -> interpretation synthesis
  -> public-safe portfolio cases
  -> redacted warm-contact queue
  -> mandatory human review
```

## Evidence classes

- `confirmed`: a supported event type has a direct source locator
- `inferred`: the event was derived from other traces
- `contradicted`: the event explicitly contradicts one or more traces
- `unknown`: direct support is insufficient

A later interview invitation may support a claim that the process progressed. It
does not support a claim that an offer existed. Career RINSE explicitly says
`No offer trace is present` unless an `offer_received` event is confirmed.

## Supported event types

```text
assignment_received
assignment_submitted
assignment_acknowledged
interview_invited
positive_feedback
hiring_paused
rejected
offer_received
outreach_sent
reply_received
```

## Python API

```python
import json
from pathlib import Path

from rinse.career import run_career_rinse

payload = json.loads(
    Path("examples/rinse/career_traces_sample.json").read_text(encoding="utf-8")
)
result = run_career_rinse(payload["traces"])

print(result["interpretations"])
print(result["portfolio_cases"])
print(result["contact_queue"])
```

The default contact queue replaces contact values with `[redacted-contact]` and
sets both safety fields:

```json
{
  "execution_allowed": false,
  "requires_human_review": true
}
```

Call `build_contact_queue(events, include_contact=True)` only inside a trusted,
private execution context. This still does not authorize execution.

## Public portfolio safety

Portfolio cases omit source locators and contact fields. Their summaries redact
common values such as:

- email addresses
- phone numbers
- long payment-card-like numbers
- password, token, API-key, and secret assignments

This is a best-effort deterministic guard, not a complete data-loss-prevention
system. Human review remains mandatory before publication.

## Adapter direction

Future read-only adapters can normalize traces from:

- Gmail message metadata and thread events
- Google Drive test-assignment documents
- applicant tracking systems
- T-Trace / LiminalDB exports

Adapters should preserve provider identifiers as private locators and must not
copy credentials, expired access links, or raw private correspondence into public
fixtures.

## Product interpretation

A search system may return twenty-four old messages. Career RINSE can instead
show that those traces contain repeated selection events, tested skills,
acknowledged submissions, process progression, warm relationships, and bounded
unknowns.

The difference is not historical revision. It is accountable reinterpretation.
