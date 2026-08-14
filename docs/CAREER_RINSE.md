# Career RINSE v0.2

Career RINSE turns fragmented career-history traces into evidence-backed reflection records, public-safe portfolio projections, and review-only next actions.

It is designed for archives such as email threads, Drive documents, applicant tracking exports, interview notes, and test assignments.

## One interpretation authority

Career RINSE is a **domain adapter**, not a second RINSE interpretation engine.

```text
career traces
  -> career normalization / evidence classification
  -> rinse.reflection-record.v0.2        # semantic authority
  -> career-friendly interpretation view  # projection
  -> portfolio/contact projections
```

The shared reflection record owns:

- stable interpretation identity and digest;
- status/evidence compatibility;
- missing-evidence semantics;
- valid / recorded / reviewed time;
- confidence;
- non-executable transition boundary;
- `REFLECTION_ONLY` authority.

Career code owns domain-specific event classification, skills, process signals, redaction, portfolio presentation, and contact prioritization.

This is the FCRP-SELF-008 correction: **one interpretation authority, many domain projections**.

## Boundary

Career RINSE does not rewrite career history.

```text
Trace          -> what is directly preserved
Evidence class -> how strongly the trace supports a domain claim
Reflection     -> shared versioned RINSE interpretation record
Projection     -> convenient career-specific reading of that record
Action queue   -> what a human may choose to review next
```

The source traces are never mutated. Reflection records remain bounded and non-executable. The module never sends email, messages recruiters, or authorizes outreach.

```text
Past evidence remains intact.
Meaning may be refined.
Action requires separate authority.
```

## Pipeline

```text
career traces
  -> normalization
  -> evidence classification
  -> company / role grouping
  -> shared reflection record
  -> career interpretation projection
  -> public-safe portfolio cases
  -> redacted warm-contact queue
  -> mandatory human review
```

`run_career_rinse()` returns both:

```text
reflection_records  # authoritative rinse.reflection-record.v0.2 records
interpretations     # domain projections bound to reflection_record_id
```

Every interpretation projection carries:

```text
id == reflection_record_id
semantic_authority == rinse.reflection-record.v0.2
```

so it cannot silently become a parallel semantic identity.

## Evidence classes

- `confirmed`: a supported event type has a direct source locator
- `inferred`: the event was derived from other traces
- `contradicted`: the event explicitly contradicts one or more traces
- `unknown`: direct support is insufficient

Those domain classes map into the shared reflection contract:

```text
confirmed + terminal offer/rejection
  -> SUPPORTED

confirmed + no terminal hiring outcome
  -> SUPPORTED_WITH_LIMITS
     missing_evidence = ["final hiring outcome"]

no confirmed trace
  -> INSUFFICIENT_EVIDENCE
     missing_evidence = ["direct supporting career trace"]

explicit contradiction
  -> CONTESTED
```

Confirmed events become `SUPPORTED_BY career-trace:<id>` relations. Contradicted events become `CONTRADICTED_BY career-trace:<id>` relations.

A later interview invitation may support a claim that the process progressed. It does not support a claim that an offer existed. Career RINSE explicitly says `No offer trace is present` unless an `offer_received` event is confirmed.

## Temporal note

Career v0.2 uses the latest trace timestamp as deterministic pipeline evaluation time for `recorded_time` and `reviewed_time`. This does **not** claim a human review occurred at that instant; it keeps the reference transformation deterministic. A future adapter with an independently evidenced review event can supply a stronger review-time signal.

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

print(result["reflection_records"])
print(result["interpretations"])
print(result["portfolio_cases"])
print(result["contact_queue"])
```

The default contact queue replaces contact values with `[redacted-contact]` and sets both safety fields:

```json
{
  "execution_allowed": false,
  "requires_human_review": true
}
```

Call `build_contact_queue(events, include_contact=True)` only inside a trusted, private execution context. This still does not authorize execution.

## Public portfolio safety

Portfolio cases omit source locators and contact fields. Their summaries redact common values such as:

- email addresses
- phone numbers
- long payment-card-like numbers
- password, token, API-key, and secret assignments

This is a best-effort deterministic guard, not a complete data-loss-prevention system. Human review remains mandatory before publication.

## Adapter direction

Future read-only adapters can normalize traces from:

- Gmail message metadata and thread events
- Google Drive test-assignment documents
- applicant tracking systems
- T-Trace / LiminalDB exports

Adapters should preserve provider identifiers as private locators and must not copy credentials, expired access links, or raw private correspondence into public fixtures.

## FCRP-SELF-008

The first meaningful divergence was architectural, not a bad career inference:

```text
RINSE core reflection graph existed in stacked branch work
        ↓
Career was developed directly from main
        ↓
Career introduced its own interpretation record shape
        ↓
two definitions of "RINSE interpretation"
```

The refactor point is the domain/core boundary:

```text
one core promotion surface (#23)
+ Career stacked on that core
+ authoritative shared reflection records
+ domain projections keyed to reflection_record_id
```

The useful Career features stay. The duplicated interpretation authority does not.

## Product interpretation

A search system may return twenty-four old messages. Career RINSE can instead show that those traces contain repeated selection events, tested skills, acknowledged submissions, process progression, warm relationships, and bounded unknowns.

The difference is not historical revision. It is accountable reinterpretation under one shared evidence contract.
