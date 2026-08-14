# LiminalDB Durable Proof Source v0.1

**Role:** read-only adapter from the canonical SYSTEM-005 durable ProofPath record into the existing RINSE reflection graph v0.2.

## Boundary

```text
LiminalDB ProofPathDurableLedger record
        ↓
validate exact durable source bundle
        ↓
normalized immutable RINSE source trace
        ↓
existing create_reflection_record()
        ↓
existing build_reflection_graph()
        ↓
REFLECTION_ONLY / execution_allowed=false
```

This adapter does not define a new interpretation engine, reflection identity or authority class.

## Canonical source identity

The v0.1 adapter accepts only the currently verified SYSTEM-005 source contract:

```text
LiminalDB durable consumer
61b02fc81e0cb5cf1f1ed4658ecff58f683cb728

LiminalDB artifact import contract
00580ff097dee61b45ad3c8a3c36ae5f548f572d

AuditEvent contract blob
fd733971aaae089df770062bcf7f2c2d6d19ca1d

ProofPath capability
685d50e256a5125a21f4c4584b326411caaa64ad

persistence_scope
local_test_only
```

The durable record hash remains the source identity. RINSE does not replace it with a new source identifier:

```text
source_trace.id = liminaldb-proof-durable:<record_hash>
```

## Validation

The adapter checks:

- source-event and admission-report bytes match their durable SHA-256 references;
- `logical_operation_id` matches the AuditEvent `correlationId`;
- event timestamp matches durable `valid_time_ms`;
- ProofPath capability identity and native `VALID` result remain pinned;
- the original artifact event still says `artifact_only`, not durable memory;
- the original artifact admission still says `dry_run`, `write_performed=false` and grants no durable/execution authority;
- the separate durable summary remains `local_test_only`, with storage write true but execution/mutation/external effects false;
- `transaction_time_ms >= valid_time_ms`;
- durable record / ingestion identities are SHA-256 references.

This preserves the causal split introduced by SYSTEM-005:

```text
artifact acceptance
≠ storage admission
≠ durable state
≠ interpretation
≠ execution authority
```

## Reflection semantics

The adapter emits a bounded statement only:

> The pinned local/test LiminalDB record establishes that canonical ProofPath verification evidence was durably recorded and restart-replayable; it does not establish the underlying real-world claim as true or grant execution authority.

It uses the existing core with:

```text
status = SUPPORTED_WITH_LIMITS
source_trace_ids = [exact durable record trace]
evidence relation = SUPPORTED_BY exact durable record hash
missing evidence = production persistence authorization + real-world outcome truth
```

Expected graph verdict:

```text
ACCEPT_WITH_LIMITS
```

Authority remains the canonical core boundary:

```text
classification = REFLECTION_ONLY
source_trace_mutation_authorized = false
evidence_mutation_authorized = false
truth_authorized = false
execution_authorized = false
```

Every candidate handoff remains:

```text
execution_allowed = false
```

## Time mapping

SYSTEM-005 durable fields remain distinct:

```text
valid_time_ms       → reflection.valid_time.from
transaction_time_ms → reflection.recorded_time
reviewed_time       → explicit RINSE review time
```

`reviewed_time` is not inferred from storage time and may not precede `recorded_time`.

## Immutability

The adapter deep-copies structured inputs and reads source bytes only. It performs no write-back into LiminalDB.

Tests assert that the source summary and source bytes are unchanged after deterministic derivation.

## Negative controls

The v0.1 contract fails closed on:

- source byte / durable digest mismatch;
- logical-operation drift;
- unsupported durable consumer revision;
- non-`local_test_only` source;
- execution authority on the durable summary;
- semantic escalation of the original artifact event even when its durable digest is updated;
- invalid temporal order;
- review time before durable recorded time.

The semantic escalation control is intentionally not a whitespace mutation. It changes:

```text
event.details.persistence.durable_memory
false → true
```

and recomputes the source digest, proving the adapter checks the contract meaning as well as the bytes.

## Non-goals

This adapter does not prove:

- production LiminalDB persistence authorization;
- truth of the underlying incident;
- RINSE write-back to LiminalDB;
- a second interpretation authority;
- executable Kairos transitions;
- distributed durability;
- production downstream automation.

## Parent invariant

> **Meaning may change. Trace must not.**

The durable source stays the durable source. RINSE adds a derived, bounded interpretation above it.
