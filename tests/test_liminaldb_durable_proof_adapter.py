from __future__ import annotations

import copy
import hashlib
import json
import unittest

from rinse.adapters.liminaldb_durable_proof import (
    DurableProofSourceError,
    LIMINALDB_DURABLE_COMMIT,
    build_durable_source_trace,
    derive_durable_proof_reflection,
)
from rinse.reflection_graph import ReflectionGraphError

LOGICAL_OPERATION = "crossmint-public-example-001"
VALID_TIME_MS = 1_786_694_400_000
TRANSACTION_TIME_MS = 1_786_694_460_000


def sha256_ref(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def event_bytes(*, durable_memory: bool = False) -> bytes:
    event = {
        "id": "proofpath-system-005-example",
        "ts": "2026-08-14T08:00:00Z",
        "correlationId": LOGICAL_OPERATION,
        "kind": "audit",
        "actor": "proofpath-scig-native-verifier",
        "action": "proofpath.scig.verification.observed",
        "details": {
            "schema_version": "liminaldb-proofpath-audit-event-v0.1",
            "logical_operation_id": LOGICAL_OPERATION,
            "source": {
                "repository": "safal207/ProofPath",
                "capability_id": "proofpath.scig.v0.1",
                "capability_commit": "685d50e256a5125a21f4c4584b326411caaa64ad",
                "incident_id": "CGQA-PROOFPATH-example",
                "scig_sha256": "1" * 64,
                "native_result": "VALID",
                "native_verifier": "proofpath-scig",
                "bridge_receipt_sha256": "2" * 64,
                "verification_class": "native_recomputed",
            },
            "evidence": {
                "bounded": True,
                "replayable": True,
                "source_receipt_bound": True,
            },
            "authority": {
                "mode": "evidence_only",
                "execution": False,
                "mutation": False,
                "persistence": False,
                "deployment": False,
                "merge": False,
            },
            "persistence": {
                "write_mode": "artifact_only",
                "durable_memory": durable_memory,
                "live_ingestion": False,
                "namespace_mutation": False,
            },
            "adapter": {
                "repository": "safal207/LiminalDB",
                "commit": "00580ff097dee61b45ad3c8a3c36ae5f548f572d",
                "contract_path": "sdk/ts/src/protocol-types.ts",
                "contract_blob_sha": "fd733971aaae089df770062bcf7f2c2d6d19ca1d",
                "event_contract": "AuditEvent",
                "write_mode": "artifact_only",
            },
            "event_sha256": "3" * 64,
        },
    }
    return (json.dumps(event, sort_keys=True) + "\n").encode()


def admission_bytes() -> bytes:
    admission = {
        "schema_version": "liminaldb-proofpath-import-check-v0.1",
        "mode": "dry_run",
        "write_performed": False,
        "event_count": 1,
        "logical_operation_ids": [LOGICAL_OPERATION],
        "authority": {
            "execution_authorized": False,
            "mutation_authorized": False,
            "durable_memory_accepted": False,
            "live_ingestion_performed": False,
        },
        "compatibility": {
            "current_contract_blob_sha": "fd733971aaae089df770062bcf7f2c2d6d19ca1d",
            "contract_blob_matches_current_checkout": True,
            "historical_snapshot_is_semantic_key": False,
        },
    }
    return (json.dumps(admission, indent=2, sort_keys=True) + "\n").encode()


def summary(event: bytes | None = None, admission: bytes | None = None) -> dict:
    event = event or event_bytes()
    admission = admission or admission_bytes()
    return {
        "namespace": "system-005-independent",
        "event_count": 1,
        "logical_operation_id": LOGICAL_OPERATION,
        "ingestion_key": "sha256:" + "4" * 64,
        "record_hash": "sha256:" + "5" * 64,
        "source_event_sha256": sha256_ref(event),
        "source_receipt_ref": "sha256:" + "6" * 64,
        "admission_report_sha256": sha256_ref(admission),
        "producer_capability_commit": "685d50e256a5125a21f4c4584b326411caaa64ad",
        "consumer_import_commit": "00580ff097dee61b45ad3c8a3c36ae5f548f572d",
        "consumer_contract_blob_sha": "fd733971aaae089df770062bcf7f2c2d6d19ca1d",
        "valid_time_ms": VALID_TIME_MS,
        "transaction_time_ms": TRANSACTION_TIME_MS,
        "persistence_scope": "local_test_only",
        "storage_write_authorized": True,
        "execution_authorized": False,
        "mutation_authorized": False,
        "external_effects_authorized": False,
    }


class DurableProofAdapterTests(unittest.TestCase):
    def test_builds_immutable_trace_from_durable_identity(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        trace = build_durable_source_trace(summary(event, admission), event, admission)

        self.assertEqual(
            trace["id"], "liminaldb-proof-durable:sha256:" + "5" * 64
        )
        self.assertEqual(trace["ts"], "2026-08-14T08:00:00.000Z")
        self.assertEqual(trace["actor"], "system")
        self.assertEqual(trace["kind"], "observation")
        self.assertEqual(trace["context"]["logical_operation_id"], LOGICAL_OPERATION)
        self.assertEqual(trace["context"]["durable_consumer_commit"], LIMINALDB_DURABLE_COMMIT)
        self.assertFalse(trace["context"]["source_trace_mutation_authorized"])
        self.assertFalse(trace["context"]["execution_authorized"])

    def test_uses_existing_reflection_graph_authority_only(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        loop = derive_durable_proof_reflection(
            summary(event, admission),
            event,
            admission,
            reviewed_time="2026-08-14T08:02:00Z",
        )

        reflection = loop["reflection"]
        graph = loop["graph"]
        self.assertEqual(reflection["status"], "SUPPORTED_WITH_LIMITS")
        self.assertEqual(graph["verdict"], "ACCEPT_WITH_LIMITS")
        self.assertEqual(reflection["authority"]["classification"], "REFLECTION_ONLY")
        self.assertFalse(reflection["authority"]["truth_authorized"])
        self.assertFalse(reflection["authority"]["execution_authorized"])
        self.assertTrue(all(not item["execution_allowed"] for item in graph["candidate_handoffs"]))
        self.assertFalse(loop["source_mutated"])
        self.assertFalse(loop["write_back_performed"])

    def test_derivation_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        source_summary = summary(event, admission)
        before_summary = copy.deepcopy(source_summary)
        before_event = bytes(event)
        before_admission = bytes(admission)

        first = derive_durable_proof_reflection(
            source_summary,
            event,
            admission,
            reviewed_time="2026-08-14T08:02:00Z",
        )
        second = derive_durable_proof_reflection(
            source_summary,
            event,
            admission,
            reviewed_time="2026-08-14T08:02:00Z",
        )

        self.assertEqual(first, second)
        self.assertEqual(source_summary, before_summary)
        self.assertEqual(event, before_event)
        self.assertEqual(admission, before_admission)

    def test_rejects_event_digest_tamper(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        source_summary = summary(event, admission)
        tampered = event + b" "
        with self.assertRaisesRegex(DurableProofSourceError, "source event bytes"):
            build_durable_source_trace(source_summary, tampered, admission)

    def test_rejects_semantic_authority_escalation_even_when_digest_is_updated(self) -> None:
        event = event_bytes(durable_memory=True)
        admission = admission_bytes()
        source_summary = summary(event, admission)
        with self.assertRaisesRegex(DurableProofSourceError, "durable_memory"):
            build_durable_source_trace(source_summary, event, admission)

    def test_rejects_execution_authority_on_durable_summary(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        source_summary = summary(event, admission)
        source_summary["execution_authorized"] = True
        with self.assertRaisesRegex(DurableProofSourceError, "execution_authorized"):
            build_durable_source_trace(source_summary, event, admission)

    def test_rejects_non_local_persistence_scope(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        source_summary = summary(event, admission)
        source_summary["persistence_scope"] = "production"
        with self.assertRaisesRegex(DurableProofSourceError, "local_test_only"):
            build_durable_source_trace(source_summary, event, admission)

    def test_rejects_unsupported_durable_consumer_revision(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        with self.assertRaisesRegex(DurableProofSourceError, "durable consumer commit"):
            build_durable_source_trace(
                summary(event, admission),
                event,
                admission,
                liminaldb_durable_commit="0" * 40,
            )

    def test_review_time_cannot_precede_durable_recorded_time(self) -> None:
        event = event_bytes()
        admission = admission_bytes()
        with self.assertRaisesRegex(ReflectionGraphError, "reviewed_time"):
            derive_durable_proof_reflection(
                summary(event, admission),
                event,
                admission,
                reviewed_time="2026-08-14T08:00:30Z",
            )


if __name__ == "__main__":
    unittest.main()
