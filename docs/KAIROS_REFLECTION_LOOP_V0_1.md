# Kairos → LiminalDB → RINSE reflection loop v0.1

## Purpose

This integration closes one bounded reflective cycle without allowing any layer
to rewrite evidence or acquire new authority.

```text
pinned TRACE evidence
  -> Kairos bounded analysis
  -> CML / ProofPath / LiminalDB projections
  -> real LiminalDB WAL + snapshot + reopen
  -> pinned replay receipt
  -> RINSE versioned reinterpretation
  -> non-executable Kairos candidate
```

## Exact upstream pins

The reference receipt fixes:

- Kairos repository: `safal207/Kairos-Gate-for-X-Cell`
- Kairos PR: `#60`
- Kairos commit: `03dbc036513be236cd30e7542145a35b27d41fe7`
- TRACE evidence commit: `31959a573724d0fd7ef1ac620a47d46355797b2f`
- LiminalDB commit: `b8cf0528187c6d3fac3b28dbb9e90f1a2fb740e7`
- exact Git blob SHAs for the workflow, bridge, manifest, derivation script,
  Rust replay example, and all six TRACE evidence files.

The source receipt also fixes independent SHA-256 references for:

- the Kairos ecosystem receipt;
- the Rust replay receipt;
- the WAL;
- the snapshot file;
- the semantic snapshot;
- the final event;
- the GitHub Actions artifact.

## Receipt boundary

The adapter accepts only the exact successful replay facts:

```text
verdict: RUST_REPLAY_RECOVERED_REPORT_ONLY
source verdict: ACCEPT_WITH_LIMITS
before reopen: 5 events
after reopen: 5 events
snapshot events: 5
projection count: 1
projection equal after reopen: true
side effect committed: false
adds scientific verdict: false
```

Final transition dimensions must remain:

```text
authority: VALID
execution: OBSERVED_EXECUTED
response_integrity: VERIFIED
causal_validity: NOT_EVALUATED
continuity_posture: REPORT_ONLY
```

Any changed commit, blob, digest, count, dimension, verdict, side-effect flag, or
authority field blocks the adapter.

## Reinterpretation

RINSE preserves the earlier reading:

```text
Functional enrichment near immune-related loci establishes an adaptive benefit.
```

It remains immutable but becomes effectively `SUPERSEDED` after a later record
is accepted into the reflection graph.

The later reading is:

```text
Functional enrichment is an association;
adaptive causality remains unresolved.
```

It is `SUPPORTED_WITH_LIMITS` and keeps four missing bridges explicit in the
underlying reflection record:

- expression change;
- cellular effect;
- organism phenotype;
- fitness advantage.

## Kairos handoff

The only active handoff is always:

```text
kind: REINTERPRETATION_CANDIDATE
status: CANDIDATE
execution_allowed: false
```

RINSE does not decide whether the target state should become an accepted Kairos
state. A separate Kairos validation step owns that decision.

## Authority boundary

```text
classification: REFLECTION_ONLY
source_mutation_authorized: false
scientific_truth_authorized: false
causal_authorization: false
execution_authorized: false
deployment_authorized: false
merge_authorized: false
```

This integration proves a deterministic, digest-bound reinterpretation path. It
does not prove adaptive causality, scientific truth, production durability,
deployment safety, or permission to execute or merge.

## CLI

```bash
python -m rinse.adapters.kairos_liminal_receipt \
  examples/rinse/trace_kairos_liminal_receipt.v0.1.json \
  --output /tmp/trace-rinse-loop.json
```

Installed entry point:

```bash
rinse-kairos-loop \
  examples/rinse/trace_kairos_liminal_receipt.v0.1.json \
  --output /tmp/trace-rinse-loop.json
```

## Validation

The workflow:

1. checks out the exact RINSE PR head;
2. runs all adapter regressions;
3. downloads upstream files from the two exact Kairos commits;
4. recomputes Git blob SHA values;
5. builds the loop twice and compares the bytes;
6. enforces the bounded graph and non-executable handoff;
7. mutates a side-effect flag and an upstream blob pin and requires `BLOCK`;
8. uploads the exact-head loop receipt as an artifact.
