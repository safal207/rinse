"""Read-only LiminalDB durable ProofPath source adapter for RINSE.

The adapter validates the durable source bundle produced by the pinned local/test
LiminalDB ProofPathDurableLedger, projects it into one normalized immutable RINSE
trace, and delegates interpretation identity / authority semantics to the existing
reflection_graph v0.2 core.

It never mutates source bytes, never writes back to LiminalDB, and never grants
truth or execution authority.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from rinse.reflection_graph import build_reflection_graph, create_reflection_record

SOURCE_SCHEMA = "rinse.liminaldb-proof-durable-source.v0.1"
LOOP_SCHEMA = "rinse.liminaldb-proof-durable-reflection-loop.v0.1"
LIMINALDB_REPOSITORY = "safal207/LiminalDB"
LIMINALDB_DURABLE_COMMIT = "61b02fc81e0cb5cf1f1ed4658ecff58f683cb728"
LIMINALDB_ARTIFACT_IMPORT_COMMIT = "00580ff097dee61b45ad3c8a3c36ae5f548f572d"
LIMINALDB_AUDIT_EVENT_BLOB = "fd733971aaae089df770062bcf7f2c2d6d19ca1d"
PROOFPATH_REPOSITORY = "safal207/ProofPath"
PROOFPATH_CAPABILITY_ID = "proofpath.scig.v0.1"
PROOFPATH_CAPABILITY_COMMIT = "685d50e256a5125a21f4c4584b326411caaa64ad"
PERSISTENCE_SCOPE = "local_test_only"
HEX64_REF_PREFIX = "sha256:"


class DurableProofSourceError(ValueError):
    """Raised when the durable source bundle violates the read-only contract."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DurableProofSourceError(f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DurableProofSourceError(f"{label} must be a non-empty string")
    return value.strip()


def _false(value: Any, label: str) -> None:
    if value is not False:
        raise DurableProofSourceError(f"{label} must be false")


def _true(value: Any, label: str) -> None:
    if value is not True:
        raise DurableProofSourceError(f"{label} must be true")


def _sha256_ref_bytes(value: bytes) -> str:
    return HEX64_REF_PREFIX + hashlib.sha256(value).hexdigest()


def _is_sha256_ref(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith(HEX64_REF_PREFIX)
        and len(value) == 71
        and all(ch in "0123456789abcdef" for ch in value[7:])
    )


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DurableProofSourceError(f"value is not canonical JSON: {exc}") from exc


def _parse_json_bytes(value: bytes, label: str) -> Mapping[str, Any]:
    if not isinstance(value, bytes) or not value:
        raise DurableProofSourceError(f"{label} must be non-empty bytes")
    try:
        decoded = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DurableProofSourceError(f"{label} must contain UTF-8 JSON") from exc
    return _mapping(decoded, label)


def _ms_to_iso(value: Any, label: str) -> str:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise DurableProofSourceError(f"{label} must be a positive integer")
    return (
        datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _iso_to_ms(value: Any, label: str) -> int:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DurableProofSourceError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise DurableProofSourceError(f"{label} must include a timezone")
    return int(parsed.timestamp() * 1000)


def validate_durable_bundle(
    summary: Mapping[str, Any],
    event_bytes: bytes,
    admission_bytes: bytes,
    *,
    liminaldb_durable_commit: str = LIMINALDB_DURABLE_COMMIT,
) -> dict[str, Any]:
    """Validate one canonical durable ProofPath source bundle without mutating it."""

    summary = deepcopy(dict(_mapping(summary, "summary")))
    if liminaldb_durable_commit != LIMINALDB_DURABLE_COMMIT:
        raise DurableProofSourceError("unsupported LiminalDB durable consumer commit")

    logical_operation_id = _text(
        summary.get("logical_operation_id"), "summary.logical_operation_id"
    )
    namespace = _text(summary.get("namespace"), "summary.namespace")
    record_hash = _text(summary.get("record_hash"), "summary.record_hash")
    ingestion_key = _text(summary.get("ingestion_key"), "summary.ingestion_key")
    if not _is_sha256_ref(record_hash):
        raise DurableProofSourceError("summary.record_hash must be sha256:<64 hex>")
    if not _is_sha256_ref(ingestion_key):
        raise DurableProofSourceError("summary.ingestion_key must be sha256:<64 hex>")

    source_event_sha256 = _text(
        summary.get("source_event_sha256"), "summary.source_event_sha256"
    )
    admission_report_sha256 = _text(
        summary.get("admission_report_sha256"), "summary.admission_report_sha256"
    )
    if source_event_sha256 != _sha256_ref_bytes(event_bytes):
        raise DurableProofSourceError("source event bytes do not match durable digest")
    if admission_report_sha256 != _sha256_ref_bytes(admission_bytes):
        raise DurableProofSourceError("admission report bytes do not match durable digest")

    if summary.get("producer_capability_commit") != PROOFPATH_CAPABILITY_COMMIT:
        raise DurableProofSourceError("unsupported ProofPath capability identity")
    if summary.get("consumer_import_commit") != LIMINALDB_ARTIFACT_IMPORT_COMMIT:
        raise DurableProofSourceError("unsupported LiminalDB artifact import identity")
    if summary.get("consumer_contract_blob_sha") != LIMINALDB_AUDIT_EVENT_BLOB:
        raise DurableProofSourceError("unsupported LiminalDB AuditEvent contract identity")
    if summary.get("persistence_scope") != PERSISTENCE_SCOPE:
        raise DurableProofSourceError("durable source must remain local_test_only")
    _true(summary.get("storage_write_authorized"), "summary.storage_write_authorized")
    _false(summary.get("execution_authorized"), "summary.execution_authorized")
    _false(summary.get("mutation_authorized"), "summary.mutation_authorized")
    _false(
        summary.get("external_effects_authorized"),
        "summary.external_effects_authorized",
    )

    valid_time_ms = summary.get("valid_time_ms")
    transaction_time_ms = summary.get("transaction_time_ms")
    if (
        not isinstance(valid_time_ms, int)
        or isinstance(valid_time_ms, bool)
        or valid_time_ms <= 0
    ):
        raise DurableProofSourceError("summary.valid_time_ms must be positive")
    if (
        not isinstance(transaction_time_ms, int)
        or isinstance(transaction_time_ms, bool)
        or transaction_time_ms < valid_time_ms
    ):
        raise DurableProofSourceError(
            "summary.transaction_time_ms must be >= valid_time_ms"
        )

    event = _parse_json_bytes(event_bytes, "event")
    if event.get("correlationId") != logical_operation_id:
        raise DurableProofSourceError("event correlationId must match logical operation")
    if event.get("actor") != "proofpath-scig-native-verifier":
        raise DurableProofSourceError("unexpected durable source actor")
    if event.get("action") != "proofpath.scig.verification.observed":
        raise DurableProofSourceError("unexpected durable source action")
    if _iso_to_ms(event.get("ts"), "event.ts") != valid_time_ms:
        raise DurableProofSourceError("event timestamp must match durable valid_time_ms")

    details = _mapping(event.get("details"), "event.details")
    source = _mapping(details.get("source"), "event.details.source")
    if source.get("repository") != PROOFPATH_REPOSITORY:
        raise DurableProofSourceError("event source repository mismatch")
    if source.get("capability_id") != PROOFPATH_CAPABILITY_ID:
        raise DurableProofSourceError("event ProofPath capability id mismatch")
    if source.get("capability_commit") != PROOFPATH_CAPABILITY_COMMIT:
        raise DurableProofSourceError("event ProofPath capability commit mismatch")
    if source.get("native_result") != "VALID":
        raise DurableProofSourceError("event must represent native ProofPath VALID")
    if source.get("verification_class") != "native_recomputed":
        raise DurableProofSourceError("event must remain native_recomputed")

    event_authority = _mapping(details.get("authority"), "event.details.authority")
    if event_authority.get("mode") != "evidence_only":
        raise DurableProofSourceError("event authority mode must remain evidence_only")
    for key in ("execution", "mutation", "persistence", "deployment", "merge"):
        _false(event_authority.get(key), f"event.details.authority.{key}")

    persistence = _mapping(details.get("persistence"), "event.details.persistence")
    if persistence.get("write_mode") != "artifact_only":
        raise DurableProofSourceError("source event must preserve artifact_only write mode")
    for key in ("durable_memory", "live_ingestion", "namespace_mutation"):
        _false(persistence.get(key), f"event.details.persistence.{key}")

    admission = _parse_json_bytes(admission_bytes, "admission")
    if admission.get("mode") != "dry_run":
        raise DurableProofSourceError("artifact admission must remain dry_run")
    _false(admission.get("write_performed"), "admission.write_performed")
    logical_ids = admission.get("logical_operation_ids")
    if logical_ids != [logical_operation_id]:
        raise DurableProofSourceError(
            "artifact admission must bind exactly one matching logical operation"
        )
    admission_authority = _mapping(admission.get("authority"), "admission.authority")
    for key in (
        "execution_authorized",
        "mutation_authorized",
        "durable_memory_accepted",
        "live_ingestion_performed",
    ):
        _false(admission_authority.get(key), f"admission.authority.{key}")

    bundle_material = {
        "summary": summary,
        "event_sha256": source_event_sha256,
        "admission_sha256": admission_report_sha256,
        "liminaldb_durable_commit": liminaldb_durable_commit,
    }
    bundle_digest = _sha256_ref_bytes(_canonical_json(bundle_material))
    return {
        "schema": SOURCE_SCHEMA,
        "repository": LIMINALDB_REPOSITORY,
        "durable_consumer_commit": liminaldb_durable_commit,
        "namespace": namespace,
        "logical_operation_id": logical_operation_id,
        "record_hash": record_hash,
        "ingestion_key": ingestion_key,
        "source_event_sha256": source_event_sha256,
        "admission_report_sha256": admission_report_sha256,
        "valid_time_ms": valid_time_ms,
        "transaction_time_ms": transaction_time_ms,
        "bundle_digest": bundle_digest,
    }


def build_durable_source_trace(
    summary: Mapping[str, Any],
    event_bytes: bytes,
    admission_bytes: bytes,
    *,
    liminaldb_durable_commit: str = LIMINALDB_DURABLE_COMMIT,
) -> dict[str, Any]:
    """Project a validated durable source bundle into one immutable RINSE trace."""

    validated = validate_durable_bundle(
        summary,
        event_bytes,
        admission_bytes,
        liminaldb_durable_commit=liminaldb_durable_commit,
    )
    logical = validated["logical_operation_id"]
    return {
        "id": f"liminaldb-proof-durable:{validated['record_hash']}",
        "ts": _ms_to_iso(validated["valid_time_ms"], "valid_time_ms"),
        "actor": "system",
        "kind": "observation",
        "text": (
            "Canonical ProofPath verification evidence for logical operation "
            f"{logical} is present in the pinned local/test LiminalDB durable record."
        ),
        "context": {
            "source": "liminaldb-proof-durable",
            **validated,
            "source_trace_mutation_authorized": False,
            "execution_authorized": False,
        },
    }


def derive_durable_proof_reflection(
    summary: Mapping[str, Any],
    event_bytes: bytes,
    admission_bytes: bytes,
    *,
    reviewed_time: str,
    liminaldb_durable_commit: str = LIMINALDB_DURABLE_COMMIT,
) -> dict[str, Any]:
    """Create one reflection through the canonical RINSE v0.2 core only."""

    trace = build_durable_source_trace(
        summary,
        event_bytes,
        admission_bytes,
        liminaldb_durable_commit=liminaldb_durable_commit,
    )
    context = _mapping(trace["context"], "trace.context")
    logical = _text(context.get("logical_operation_id"), "logical_operation_id")
    recorded_time = _ms_to_iso(
        context.get("transaction_time_ms"), "transaction_time_ms"
    )
    valid_from = _ms_to_iso(context.get("valid_time_ms"), "valid_time_ms")

    reflection = create_reflection_record(
        subject_id=f"logical-operation:{logical}",
        statement=(
            "The pinned local/test LiminalDB record establishes that canonical "
            f"ProofPath verification evidence for logical operation {logical} was "
            "durably recorded and restart-replayable; it does not establish the "
            "underlying real-world claim as true or grant execution authority."
        ),
        status="SUPPORTED_WITH_LIMITS",
        source_trace_ids=[trace["id"]],
        evidence_relations=[
            {
                "type": "SUPPORTED_BY",
                "ref": trace["id"],
                "digest": context["record_hash"],
                "note": "Pinned LiminalDB durable record identity",
            }
        ],
        recorded_time=recorded_time,
        reviewed_time=reviewed_time,
        valid_from=valid_from,
        proposed_target_state="durable-evidence-reflection-reviewed",
        confidence=1.0,
        missing_evidence=[
            "production-persistence-authorization",
            "underlying-real-world-outcome-truth",
        ],
    )
    graph = build_reflection_graph([reflection])
    if graph["verdict"] != "ACCEPT_WITH_LIMITS":
        raise DurableProofSourceError("durable proof reflection must remain bounded")
    if graph["authority"]["classification"] != "REFLECTION_ONLY":
        raise DurableProofSourceError("RINSE graph created a parallel authority class")
    if any(item["execution_allowed"] for item in graph["candidate_handoffs"]):
        raise DurableProofSourceError("RINSE candidate handoff became executable")

    return {
        "schema": LOOP_SCHEMA,
        "source_trace": trace,
        "reflection": reflection,
        "graph": graph,
        "source_mutated": False,
        "write_back_performed": False,
    }
