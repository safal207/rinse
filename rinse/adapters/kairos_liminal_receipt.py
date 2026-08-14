"""Read an exact Kairos/LiminalDB replay receipt into RINSE reflection records.

The adapter is deliberately narrow. It accepts only the pinned TRACE receipt
validated on Kairos PR #60, treats every upstream artifact as immutable evidence,
and emits a non-executable reinterpretation candidate for later Kairos review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from rinse.reflection_graph import (
    ReflectionGraphError,
    build_reflection_graph,
    create_reflection_record,
)


RECEIPT_SCHEMA = "rinse.kairos-liminal-receipt.v0.1"
LOOP_SCHEMA = "rinse.kairos-reflection-loop.v0.1"
CASE_ID = "trace-archaic-introgression-2026"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")

EXPECTED_SOURCE = {
    "kairos_repository": "safal207/Kairos-Gate-for-X-Cell",
    "kairos_pull_request": 60,
    "kairos_commit": "03dbc036513be236cd30e7542145a35b27d41fe7",
    "trace_package_commit": "31959a573724d0fd7ef1ac620a47d46355797b2f",
    "liminaldb_repository": "safal207/LiminalDB",
    "liminaldb_commit": "b8cf0528187c6d3fac3b28dbb9e90f1a2fb740e7",
}
EXPECTED_CODE_PINS = {
    ".github/workflows/trace-liminaldb-rust-replay.yml": "d1683ef0e1d0c7e346c53cb878a04762249af69f",
    "kairos_gate/trace_evidence_bridge.py": "8ba40e4257c3750d34a89e324c3adf7480c82fbb",
    "manifests/trace-evidence-package-pr55.v0.1.json": "e25e1d074a5c2bb16e5611283c3dd33a234e7074",
    "scripts/derive_trace_ecosystem_receipt.py": "437abd9537a44a58fa5d8b7fb0aa553293a35a3e",
    "tools/liminaldb_bridge/trace_ecosystem_replay.rs": "ce3b66178f937f603cd84ee44a598e3157a24fdb",
}
EXPECTED_TRACE_FILE_PINS = {
    "claim_map": (
        "evidence/trace-archaic-introgression-2026/claim-map.v0.1.json",
        "589a1501af228237764878b30759424e0e1055b1",
    ),
    "causal_transition_map": (
        "evidence/trace-archaic-introgression-2026/causal-transition-map.v0.1.json",
        "8a9221580483a3b2ce09a7d9e4046171bbbcf5e1",
    ),
    "disposition": (
        "evidence/trace-archaic-introgression-2026/disposition.v0.1.json",
        "a19e1f50238d3598833045fbbd4bb6e4e423f889",
    ),
    "source_manifest": (
        "evidence/trace-archaic-introgression-2026/source-manifest.v0.1.json",
        "a0de89d556dfb9dbca80a02844068206264338ff",
    ),
    "reproducibility_contract": (
        "evidence/trace-archaic-introgression-2026/reproducibility-contract.v0.1.json",
        "1827d24bfcf4d85c9420ef75ba1a1032bea96155",
    ),
    "phase_compatibility": (
        "evidence/trace-archaic-introgression-2026/phase-compatibility.v0.1.json",
        "45ffc0a36f935bfce2ecc0646c191edb8c1733bc",
    ),
}
EXPECTED_EVIDENCE_DIGESTS = {
    "source_ecosystem_receipt": "sha256:24fda69778ce488180e28ece2e6a893400092fbf872b0cc7850a87378dd98386",
    "rust_replay_receipt": "sha256:412b378cabc62b08978bd38ff9b1b7a674f6eb3a6842ae076c358db4c0070a16",
    "wal": "sha256:74167e0af526925859587cd6cb9cdb34b76f959d11935ecb0c57ba788318d6ed",
    "snapshot_file": "sha256:39cf07f1b18151a75573a43d72fab4ab3ad2b2d2bbc83fc66b2418ca71376a9b",
    "semantic_snapshot": "sha256:c73d9594c1553c4b85040ba8ba87e5afba937a2040d89ea151864b318e7b80aa",
    "final_event": "sha256:e0b7a48ebd49d1b232b8ce0030b66f495f5cedfd5edea1c8100ff65f7d49a8a5",
    "workflow_artifact": "sha256:96b48012c754df81b28134e15e3049740576a36536608d1a1e658acc217f80b3",
}
EXPECTED_REPLAY = {
    "verdict": "RUST_REPLAY_RECOVERED_REPORT_ONLY",
    "source_verdict": "ACCEPT_WITH_LIMITS",
    "event_count_before_reopen": 5,
    "event_count_after_reopen": 5,
    "snapshot_event_count": 5,
    "projection_count": 1,
    "projection_equal_after_reopen": True,
    "final_side_effect_committed": False,
    "adds_scientific_verdict": False,
    "final_dimensions": {
        "authority": "VALID",
        "execution": "OBSERVED_EXECUTED",
        "response_integrity": "VERIFIED",
        "causal_validity": "NOT_EVALUATED",
        "continuity_posture": "REPORT_ONLY",
    },
}
EXPECTED_AUTHORITY = {
    "classification": "REFLECTION_SOURCE_ONLY",
    "source_mutation_authorized": False,
    "scientific_truth_authorized": False,
    "causal_authorization": False,
    "execution_authorized": False,
    "deployment_authorized": False,
    "merge_authorized": False,
}


class KairosLiminalReceiptError(ValueError):
    """Raised when a receipt differs from the exact validated upstream contract."""


def _canonical(value: Any) -> bytes:
    """Serialize a value into stable JSON bytes for digesting."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise KairosLiminalReceiptError(f"non-canonical receipt value: {exc}") from exc


def _digest(value: Any) -> str:
    """Return a prefixed SHA-256 digest of canonical JSON."""

    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    """Require an object value."""

    if not isinstance(value, Mapping):
        raise KairosLiminalReceiptError(f"{label} must be an object")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    """Require a non-string array value."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KairosLiminalReceiptError(f"{label} must be an array")
    return value


def _pin_index(values: Any, *, key: str, label: str) -> dict[str, Mapping[str, Any]]:
    """Build a unique index for code or evidence file pins."""

    index: dict[str, Mapping[str, Any]] = {}
    for position, raw in enumerate(_sequence(values, label)):
        item = _mapping(raw, f"{label}[{position}]")
        identity = item.get(key)
        if not isinstance(identity, str) or not identity:
            raise KairosLiminalReceiptError(f"{label}[{position}].{key} is invalid")
        if identity in index:
            raise KairosLiminalReceiptError(f"duplicate {label} identity: {identity}")
        index[identity] = item
    return index


def validate_kairos_liminal_receipt(value: Any) -> None:
    """Validate exact source pins, replay results, and authority boundaries."""

    receipt = _mapping(value, "receipt")
    expected_fields = {
        "schema",
        "case_id",
        "source",
        "code_pins",
        "trace_file_pins",
        "evidence_digests",
        "workflow_artifact_id",
        "replay",
        "authority",
    }
    if set(receipt) != expected_fields:
        raise KairosLiminalReceiptError("receipt fields differ from the pinned contract")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise KairosLiminalReceiptError("unsupported receipt schema")
    if receipt.get("case_id") != CASE_ID:
        raise KairosLiminalReceiptError("TRACE case_id changed")
    if dict(_mapping(receipt.get("source"), "source")) != EXPECTED_SOURCE:
        raise KairosLiminalReceiptError("upstream repository or commit pin changed")
    for field in ("kairos_commit", "trace_package_commit", "liminaldb_commit"):
        if not HEX40.fullmatch(EXPECTED_SOURCE[field]):
            raise KairosLiminalReceiptError(f"internal invalid commit pin: {field}")

    code_pins = _pin_index(receipt.get("code_pins"), key="path", label="code_pins")
    if set(code_pins) != set(EXPECTED_CODE_PINS):
        raise KairosLiminalReceiptError("Kairos code pin paths changed")
    for path, expected_blob in EXPECTED_CODE_PINS.items():
        item = code_pins[path]
        if set(item) != {"path", "git_blob_sha"}:
            raise KairosLiminalReceiptError(f"unexpected code pin fields: {path}")
        actual = item.get("git_blob_sha")
        if actual != expected_blob or not isinstance(actual, str) or not HEX40.fullmatch(actual):
            raise KairosLiminalReceiptError(f"Git blob mismatch for {path}")

    trace_pins = _pin_index(
        receipt.get("trace_file_pins"), key="role", label="trace_file_pins"
    )
    if set(trace_pins) != set(EXPECTED_TRACE_FILE_PINS):
        raise KairosLiminalReceiptError("TRACE evidence roles changed")
    for role, (expected_path, expected_blob) in EXPECTED_TRACE_FILE_PINS.items():
        item = trace_pins[role]
        if set(item) != {"role", "path", "git_blob_sha"}:
            raise KairosLiminalReceiptError(f"unexpected TRACE pin fields: {role}")
        if item.get("path") != expected_path or item.get("git_blob_sha") != expected_blob:
            raise KairosLiminalReceiptError(f"TRACE file pin mismatch for {role}")

    digests = dict(_mapping(receipt.get("evidence_digests"), "evidence_digests"))
    if digests != EXPECTED_EVIDENCE_DIGESTS:
        raise KairosLiminalReceiptError("replay evidence digest changed")
    if any(not SHA256_REF.fullmatch(value) for value in digests.values()):
        raise KairosLiminalReceiptError("invalid SHA-256 evidence reference")
    if receipt.get("workflow_artifact_id") != 8787651246:
        raise KairosLiminalReceiptError("workflow artifact ID changed")
    if dict(_mapping(receipt.get("replay"), "replay")) != EXPECTED_REPLAY:
        raise KairosLiminalReceiptError("Rust replay result or boundary changed")
    if dict(_mapping(receipt.get("authority"), "authority")) != EXPECTED_AUTHORITY:
        raise KairosLiminalReceiptError("source authority boundary was escalated")


def derive_trace_reflection_loop(value: Any) -> dict[str, Any]:
    """Derive a versioned bounded interpretation and Kairos review candidate."""

    source_snapshot = deepcopy(value)
    validate_kairos_liminal_receipt(source_snapshot)
    digests = source_snapshot["evidence_digests"]

    earlier = create_reflection_record(
        subject_id="trace:functional-adaptation-claim",
        statement=(
            "Functional enrichment near immune-related loci establishes an "
            "adaptive benefit from archaic introgression."
        ),
        status="CONTESTED",
        source_trace_ids=[
            "kairos:trace-evidence-package-pr55",
            "liminaldb:trace-pr55-rust-replay",
        ],
        evidence_relations=[
            {
                "type": "CONTRADICTED_BY",
                "ref": "kairos:claim:C10",
                "digest": digests["source_ecosystem_receipt"],
                "note": "Kairos rejects the direct causal-adaptation overclaim.",
            }
        ],
        recorded_time="2026-07-31T08:30:00Z",
        reviewed_time="2026-07-31T08:30:00Z",
        valid_from="2026-01-01T00:00:00Z",
        valid_to="2026-07-31T08:35:00Z",
        proposed_target_state="trace-adaptive-benefit-overclaim-under-review",
        confidence=0.35,
    )
    bounded = create_reflection_record(
        subject_id="trace:functional-adaptation-claim",
        statement=(
            "Functional enrichment is an association; adaptive causality "
            "remains unresolved."
        ),
        status="SUPPORTED_WITH_LIMITS",
        source_trace_ids=[
            "kairos:trace-evidence-package-pr55",
            "liminaldb:trace-pr55-rust-replay",
        ],
        evidence_relations=[
            {
                "type": "SUPPORTED_BY",
                "ref": "kairos:trace-ecosystem-receipt",
                "digest": digests["source_ecosystem_receipt"],
            },
            {
                "type": "SUPPORTED_BY",
                "ref": "liminaldb:rust-replay-receipt",
                "digest": digests["rust_replay_receipt"],
            },
            {
                "type": "SUPPORTED_BY",
                "ref": "liminaldb:semantic-snapshot",
                "digest": digests["semantic_snapshot"],
            },
            {
                "type": "SUPPORTED_BY",
                "ref": "liminaldb:final-event",
                "digest": digests["final_event"],
            },
        ],
        interpretation_relations=[
            {"type": "SUPERSEDES", "target_id": earlier["id"]}
        ],
        missing_evidence=[
            "cellular effect",
            "expression change",
            "fitness advantage",
            "organism phenotype",
        ],
        recorded_time="2026-07-31T08:35:00Z",
        reviewed_time="2026-07-31T08:35:00Z",
        valid_from="2026-07-31T08:35:00Z",
        proposed_target_state=(
            "trace-functional-association-with-unresolved-adaptive-causality"
        ),
        confidence=0.78,
    )
    graph = build_reflection_graph([earlier, bounded])
    if graph["verdict"] != "ACCEPT_WITH_LIMITS":
        raise KairosLiminalReceiptError("unexpected RINSE graph verdict")
    if graph["active_interpretation_ids"] != [bounded["id"]]:
        raise KairosLiminalReceiptError("bounded interpretation is not uniquely active")
    handoffs = graph["candidate_handoffs"]
    if len(handoffs) != 1 or handoffs[0].get("execution_allowed") is not False:
        raise KairosLiminalReceiptError("RINSE handoff exceeded reflection authority")

    body = {
        "schema": LOOP_SCHEMA,
        "case_id": CASE_ID,
        "source_receipt_digest": _digest(source_snapshot),
        "upstream": deepcopy(source_snapshot["source"]),
        "upstream_evidence_digests": deepcopy(digests),
        "reflection_graph": graph,
        "active_reflection_id": bounded["id"],
        "kairos_handoff": deepcopy(handoffs[0]),
        "authority": {
            "classification": "REFLECTION_ONLY",
            "source_mutation_authorized": False,
            "scientific_truth_authorized": False,
            "causal_authorization": False,
            "execution_authorized": False,
            "deployment_authorized": False,
            "merge_authorized": False,
        },
    }
    return {**body, "digest": _digest(body)}


def main(argv: list[str] | None = None) -> int:
    """Run the exact-receipt adapter with bounded `BLOCK:` failures."""

    parser = argparse.ArgumentParser(
        description="Derive a RINSE reflection loop from a pinned Kairos receipt"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        source = json.loads(args.input.read_text(encoding="utf-8"))
        result = derive_trace_reflection_loop(source)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KairosLiminalReceiptError,
        ReflectionGraphError,
    ) as exc:
        print(f"BLOCK: {exc}")
        return 2

    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
