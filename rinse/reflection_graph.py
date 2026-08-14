"""Deterministic, evidence-bound reflection graph for RINSE v0.2.

The module keeps source traces immutable and treats interpretations as derived,
versioned records. It never grants truth or execution authority; it only emits
review candidates that another governing layer, such as Kairos, may assess.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "rinse.reflection-record.v0.2"
GRAPH_SCHEMA = "rinse.reflection-graph.v0.2"
RECORD_STATUSES = {
    "PROPOSED",
    "SUPPORTED",
    "SUPPORTED_WITH_LIMITS",
    "CONTESTED",
    "INSUFFICIENT_EVIDENCE",
    "RETIRED",
}
EFFECTIVE_STATUSES = RECORD_STATUSES | {"SUPERSEDED"}
EVIDENCE_RELATIONS = {"SUPPORTED_BY", "CONTRADICTED_BY"}
INTERPRETATION_RELATIONS = {"SUPERSEDES", "REFINES"}
HEX64_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^rinse-reflection-[0-9a-f]{16}$")


class ReflectionGraphError(ValueError):
    """Raised when a reflection record or graph violates a fail-closed boundary."""


def _canonical(value: Any) -> bytes:
    """Serialize a value into stable canonical JSON bytes."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReflectionGraphError(f"value is not canonical JSON: {exc}") from exc


def _sha256_ref(value: Any) -> str:
    """Return a prefixed SHA-256 reference for canonical JSON content."""

    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    """Require and return an object-like mapping."""

    if not isinstance(value, Mapping):
        raise ReflectionGraphError(f"{label} must be an object")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    """Require and return a non-string sequence."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ReflectionGraphError(f"{label} must be an array")
    return value


def _text(value: Any, label: str) -> str:
    """Require a non-empty string and normalize surrounding whitespace."""

    if not isinstance(value, str) or not value.strip():
        raise ReflectionGraphError(f"{label} must be a non-empty string")
    return value.strip()


def _iso_datetime(value: Any, label: str) -> datetime:
    """Parse a timezone-aware ISO-8601 date-time."""

    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReflectionGraphError(f"{label} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ReflectionGraphError(f"{label} must include a timezone")
    return parsed


def _unique_sorted_strings(values: Iterable[Any], label: str) -> list[str]:
    """Normalize an iterable into sorted unique non-empty strings."""

    result: set[str] = set()
    for index, value in enumerate(values):
        result.add(_text(value, f"{label}[{index}]"))
    return sorted(result)


def _normalized_evidence_relations(values: Iterable[Any]) -> list[dict[str, Any]]:
    """Validate, deduplicate, and deterministically order evidence relations."""

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(values):
        item = _mapping(raw, f"evidence_relations[{index}]")
        relation = _text(item.get("type"), f"evidence_relations[{index}].type")
        if relation not in EVIDENCE_RELATIONS:
            raise ReflectionGraphError(f"unsupported evidence relation: {relation}")
        ref = _text(item.get("ref"), f"evidence_relations[{index}].ref")
        key = (relation, ref)
        if key in seen:
            raise ReflectionGraphError(f"duplicate evidence relation: {relation} {ref}")
        seen.add(key)
        normalized_item: dict[str, Any] = {"type": relation, "ref": ref}
        digest = item.get("digest")
        if digest is not None:
            digest = _text(digest, f"evidence_relations[{index}].digest")
            if not HEX64_REF.fullmatch(digest):
                raise ReflectionGraphError(
                    f"evidence_relations[{index}].digest must be sha256:<64 hex>"
                )
            normalized_item["digest"] = digest
        note = item.get("note")
        if note is not None:
            normalized_item["note"] = _text(
                note, f"evidence_relations[{index}].note"
            )
        normalized.append(normalized_item)
    return sorted(normalized, key=lambda item: (item["type"], item["ref"]))


def _normalized_interpretation_relations(values: Iterable[Any]) -> list[dict[str, str]]:
    """Validate and order links between versioned interpretations."""

    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(values):
        item = _mapping(raw, f"interpretation_relations[{index}]")
        relation = _text(item.get("type"), f"interpretation_relations[{index}].type")
        if relation not in INTERPRETATION_RELATIONS:
            raise ReflectionGraphError(f"unsupported interpretation relation: {relation}")
        target_id = _text(
            item.get("target_id"), f"interpretation_relations[{index}].target_id"
        )
        if not ID_RE.fullmatch(target_id):
            raise ReflectionGraphError(
                f"interpretation_relations[{index}].target_id is invalid"
            )
        key = (relation, target_id)
        if key in seen:
            raise ReflectionGraphError(
                f"duplicate interpretation relation: {relation} {target_id}"
            )
        seen.add(key)
        normalized.append({"type": relation, "target_id": target_id})
    return sorted(normalized, key=lambda item: (item["type"], item["target_id"]))


def _authority_boundary() -> dict[str, Any]:
    """Return the immutable reflection-only authority boundary."""

    return {
        "classification": "REFLECTION_ONLY",
        "source_trace_mutation_authorized": False,
        "evidence_mutation_authorized": False,
        "truth_authorized": False,
        "execution_authorized": False,
    }


def _candidate_transition(target_state: str) -> dict[str, Any]:
    """Build a non-executable reinterpretation candidate for Kairos review."""

    return {
        "kind": "REINTERPRETATION_CANDIDATE",
        "target_state": _text(target_state, "proposed_target_state"),
        "status": "CANDIDATE",
        "execution_allowed": False,
    }


def create_reflection_record(
    *,
    subject_id: str,
    statement: str,
    status: str,
    source_trace_ids: Iterable[str],
    evidence_relations: Iterable[Mapping[str, Any]],
    recorded_time: str,
    reviewed_time: str,
    valid_from: str,
    proposed_target_state: str,
    confidence: float,
    valid_to: str | None = None,
    interpretation_relations: Iterable[Mapping[str, Any]] = (),
    missing_evidence: Iterable[str] = (),
) -> dict[str, Any]:
    """Create one deterministic reflection record.

    All time values are caller-supplied so identical semantic input produces an
    identical identifier and digest. The function copies and normalizes inputs;
    it never mutates caller-owned traces or evidence objects.
    """

    if status not in RECORD_STATUSES:
        raise ReflectionGraphError(f"unsupported status: {status}")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise ReflectionGraphError("confidence must be a number")
    confidence = round(float(confidence), 6)
    if confidence < 0 or confidence > 1:
        raise ReflectionGraphError("confidence must be between 0 and 1")

    valid_time: dict[str, str] = {"from": _text(valid_from, "valid_from")}
    if valid_to is not None:
        valid_time["to"] = _text(valid_to, "valid_to")

    semantic_body: dict[str, Any] = {
        "schema": SCHEMA,
        "subject_id": _text(subject_id, "subject_id"),
        "statement": _text(statement, "statement"),
        "status": status,
        "source_trace_ids": _unique_sorted_strings(
            list(source_trace_ids), "source_trace_ids"
        ),
        "evidence_relations": _normalized_evidence_relations(
            deepcopy(list(evidence_relations))
        ),
        "interpretation_relations": _normalized_interpretation_relations(
            deepcopy(list(interpretation_relations))
        ),
        "missing_evidence": _unique_sorted_strings(
            list(missing_evidence), "missing_evidence"
        ),
        "valid_time": valid_time,
        "recorded_time": _text(recorded_time, "recorded_time"),
        "reviewed_time": _text(reviewed_time, "reviewed_time"),
        "confidence": confidence,
        "proposed_transition": _candidate_transition(proposed_target_state),
        "authority": _authority_boundary(),
    }
    identity = {
        "schema": SCHEMA,
        "subject_id": semantic_body["subject_id"],
        "statement": semantic_body["statement"],
        "valid_time": semantic_body["valid_time"],
        "recorded_time": semantic_body["recorded_time"],
    }
    identity_digest = _sha256_ref(identity)
    digest = _sha256_ref(semantic_body)
    record = {
        **semantic_body,
        "id": f"rinse-reflection-{identity_digest.split(':', 1)[1][:16]}",
        "digest": digest,
    }
    validate_reflection_record(record)
    return record


def _semantic_body(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the digest-bearing record body without generated identity fields."""

    return {
        key: deepcopy(value)
        for key, value in record.items()
        if key not in {"id", "digest"}
    }


def validate_reflection_record(value: Any) -> None:
    """Validate one reflection record and its authority boundaries."""

    record = _mapping(value, "reflection")
    expected_fields = {
        "schema",
        "id",
        "digest",
        "subject_id",
        "statement",
        "status",
        "source_trace_ids",
        "evidence_relations",
        "interpretation_relations",
        "missing_evidence",
        "valid_time",
        "recorded_time",
        "reviewed_time",
        "confidence",
        "proposed_transition",
        "authority",
    }
    if set(record) != expected_fields:
        missing = sorted(expected_fields - set(record))
        extra = sorted(set(record) - expected_fields)
        raise ReflectionGraphError(
            f"reflection fields mismatch; missing={missing}, extra={extra}"
        )
    if record.get("schema") != SCHEMA:
        raise ReflectionGraphError("unsupported reflection schema")
    record_id = _text(record.get("id"), "reflection.id")
    if not ID_RE.fullmatch(record_id):
        raise ReflectionGraphError("reflection.id is invalid")
    digest = _text(record.get("digest"), "reflection.digest")
    if not HEX64_REF.fullmatch(digest):
        raise ReflectionGraphError("reflection.digest must be sha256:<64 hex>")

    _text(record.get("subject_id"), "reflection.subject_id")
    _text(record.get("statement"), "reflection.statement")
    status = _text(record.get("status"), "reflection.status")
    if status not in RECORD_STATUSES:
        raise ReflectionGraphError(f"unsupported reflection.status: {status}")

    trace_ids = _sequence(record.get("source_trace_ids"), "source_trace_ids")
    normalized_trace_ids = _unique_sorted_strings(trace_ids, "source_trace_ids")
    if not normalized_trace_ids:
        raise ReflectionGraphError("source_trace_ids must not be empty")
    if list(trace_ids) != normalized_trace_ids:
        raise ReflectionGraphError("source_trace_ids must be sorted and unique")

    evidence = _sequence(record.get("evidence_relations"), "evidence_relations")
    if list(evidence) != _normalized_evidence_relations(evidence):
        raise ReflectionGraphError("evidence_relations are not normalized")
    interpretation_relations = _sequence(
        record.get("interpretation_relations"), "interpretation_relations"
    )
    if list(interpretation_relations) != _normalized_interpretation_relations(
        interpretation_relations
    ):
        raise ReflectionGraphError("interpretation_relations are not normalized")

    missing_evidence = _sequence(record.get("missing_evidence"), "missing_evidence")
    normalized_missing = _unique_sorted_strings(missing_evidence, "missing_evidence")
    if list(missing_evidence) != normalized_missing:
        raise ReflectionGraphError("missing_evidence must be sorted and unique")

    valid_time = _mapping(record.get("valid_time"), "valid_time")
    if set(valid_time) not in ({"from"}, {"from", "to"}):
        raise ReflectionGraphError("valid_time must contain from and optional to")
    valid_from = _iso_datetime(valid_time.get("from"), "valid_time.from")
    if "to" in valid_time:
        valid_to = _iso_datetime(valid_time.get("to"), "valid_time.to")
        if valid_to < valid_from:
            raise ReflectionGraphError("valid_time.to must not precede valid_time.from")
    recorded = _iso_datetime(record.get("recorded_time"), "recorded_time")
    reviewed = _iso_datetime(record.get("reviewed_time"), "reviewed_time")
    if reviewed < recorded:
        raise ReflectionGraphError("reviewed_time must not precede recorded_time")

    confidence = record.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise ReflectionGraphError("confidence must be a number")
    if confidence < 0 or confidence > 1:
        raise ReflectionGraphError("confidence must be between 0 and 1")

    evidence_types = {item["type"] for item in evidence}
    if status == "SUPPORTED" and "SUPPORTED_BY" not in evidence_types:
        raise ReflectionGraphError("SUPPORTED requires SUPPORTING evidence")
    if status == "SUPPORTED_WITH_LIMITS":
        if "SUPPORTED_BY" not in evidence_types:
            raise ReflectionGraphError(
                "SUPPORTED_WITH_LIMITS requires SUPPORTING evidence"
            )
        if not missing_evidence:
            raise ReflectionGraphError(
                "SUPPORTED_WITH_LIMITS requires explicit missing_evidence"
            )
    if status == "CONTESTED" and "CONTRADICTED_BY" not in evidence_types:
        raise ReflectionGraphError("CONTESTED requires CONTRADICTING evidence")
    if status == "INSUFFICIENT_EVIDENCE" and not missing_evidence:
        raise ReflectionGraphError(
            "INSUFFICIENT_EVIDENCE requires explicit missing_evidence"
        )

    transition = _mapping(record.get("proposed_transition"), "proposed_transition")
    if transition != _candidate_transition(transition.get("target_state")):
        raise ReflectionGraphError(
            "proposed_transition must remain a non-executable Kairos candidate"
        )
    authority = _mapping(record.get("authority"), "authority")
    if authority != _authority_boundary():
        raise ReflectionGraphError("reflection authority boundary was escalated")

    expected_digest = _sha256_ref(_semantic_body(record))
    if digest != expected_digest:
        raise ReflectionGraphError("reflection digest mismatch")
    identity = {
        "schema": SCHEMA,
        "subject_id": record["subject_id"],
        "statement": record["statement"],
        "valid_time": record["valid_time"],
        "recorded_time": record["recorded_time"],
    }
    identity_digest = _sha256_ref(identity)
    expected_id = f"rinse-reflection-{identity_digest.split(':', 1)[1][:16]}"
    if record_id != expected_id:
        raise ReflectionGraphError("reflection id does not match stable identity")


def _detect_cycles(index: Mapping[str, Mapping[str, Any]], relation_type: str) -> None:
    """Reject cycles in a chosen interpretation-relation subgraph."""

    adjacency: dict[str, list[str]] = {record_id: [] for record_id in index}
    for record_id, record in index.items():
        for relation in record["interpretation_relations"]:
            if relation["type"] == relation_type:
                adjacency[record_id].append(relation["target_id"])

    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> None:
        """Depth-first walk that detects a back edge."""

        if node in visiting:
            raise ReflectionGraphError(f"{relation_type} cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency[node]:
            walk(target)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        walk(node)


def validate_reflection_graph(records: Sequence[Any]) -> None:
    """Validate record references, chronology, subjects, and graph acyclicity."""

    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ReflectionGraphError("records must be an array")
    index: dict[str, Mapping[str, Any]] = {}
    for position, raw in enumerate(records):
        validate_reflection_record(raw)
        record = _mapping(raw, f"records[{position}]")
        record_id = record["id"]
        if record_id in index:
            raise ReflectionGraphError(f"duplicate reflection id: {record_id}")
        index[record_id] = record

    for record_id, record in index.items():
        recorded = _iso_datetime(record["recorded_time"], f"{record_id}.recorded_time")
        for relation in record["interpretation_relations"]:
            target_id = relation["target_id"]
            if target_id == record_id:
                raise ReflectionGraphError("reflection cannot relate to itself")
            target = index.get(target_id)
            if target is None:
                raise ReflectionGraphError(
                    f"{record_id} references missing interpretation {target_id}"
                )
            if target["subject_id"] != record["subject_id"]:
                raise ReflectionGraphError(
                    "interpretation relations cannot cross subject boundaries"
                )
            target_recorded = _iso_datetime(
                target["recorded_time"], f"{target_id}.recorded_time"
            )
            if recorded < target_recorded:
                raise ReflectionGraphError(
                    f"{record_id} cannot revise a later interpretation {target_id}"
                )

    _detect_cycles(index, "SUPERSEDES")
    _detect_cycles(index, "REFINES")


def build_reflection_graph(records: Sequence[Any]) -> dict[str, Any]:
    """Build a deterministic graph projection from immutable reflection records."""

    validate_reflection_graph(records)
    index = {record["id"]: record for record in records}
    superseded_by: dict[str, list[str]] = {record_id: [] for record_id in index}
    graph_edges: list[dict[str, str]] = []

    for record in records:
        for relation in record["interpretation_relations"]:
            graph_edges.append(
                {
                    "from": record["id"],
                    "to": relation["target_id"],
                    "type": relation["type"],
                }
            )
            if relation["type"] == "SUPERSEDES":
                superseded_by[relation["target_id"]].append(record["id"])
        for relation in record["evidence_relations"]:
            graph_edges.append(
                {
                    "from": record["id"],
                    "to": relation["ref"],
                    "type": relation["type"],
                }
            )

    nodes: list[dict[str, Any]] = []
    active_ids: list[str] = []
    for record_id in sorted(index):
        record = index[record_id]
        incoming = sorted(superseded_by[record_id])
        effective_status = "SUPERSEDED" if incoming else record["status"]
        nodes.append(
            {
                "id": record_id,
                "subject_id": record["subject_id"],
                "statement": record["statement"],
                "declared_status": record["status"],
                "effective_status": effective_status,
                "superseded_by": incoming,
                "confidence": record["confidence"],
                "digest": record["digest"],
            }
        )
        if effective_status not in {"SUPERSEDED", "RETIRED"}:
            active_ids.append(record_id)

    forks = sorted(
        record_id for record_id, incoming in superseded_by.items() if len(incoming) > 1
    )
    active_statuses = {index[record_id]["status"] for record_id in active_ids}
    if forks or active_statuses & {"CONTESTED", "INSUFFICIENT_EVIDENCE"}:
        verdict = "REVIEW"
    elif "SUPPORTED_WITH_LIMITS" in active_statuses:
        verdict = "ACCEPT_WITH_LIMITS"
    elif active_statuses and active_statuses <= {"SUPPORTED"}:
        verdict = "ACCEPT"
    else:
        verdict = "HOLD"

    candidate_handoffs = [
        {
            "reflection_id": record_id,
            **deepcopy(index[record_id]["proposed_transition"]),
        }
        for record_id in active_ids
    ]
    body = {
        "schema": GRAPH_SCHEMA,
        "verdict": verdict,
        "nodes": nodes,
        "edges": sorted(
            graph_edges, key=lambda edge: (edge["type"], edge["from"], edge["to"])
        ),
        "active_interpretation_ids": active_ids,
        "forked_predecessor_ids": forks,
        "candidate_handoffs": candidate_handoffs,
        "authority": _authority_boundary(),
    }
    return {**body, "digest": _sha256_ref(body)}


def main(argv: list[str] | None = None) -> int:
    """Run the fail-closed command-line graph builder."""

    parser = argparse.ArgumentParser(description="Build a RINSE v0.2 reflection graph")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        records = _sequence(_mapping(payload, "input").get("records"), "records")
        graph = build_reflection_graph(records)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ReflectionGraphError,
    ) as exc:
        print(f"BLOCK: {exc}")
        return 2

    rendered = json.dumps(graph, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
