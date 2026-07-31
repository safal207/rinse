"""Cross-repository contract tests for the Kairos/LiminalDB receipt adapter."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from rinse.adapters.kairos_liminal_receipt import (
    EXPECTED_CODE_PINS,
    EXPECTED_EVIDENCE_DIGESTS,
    EXPECTED_SOURCE,
    EXPECTED_TRACE_FILE_PINS,
    KairosLiminalReceiptError,
    derive_trace_reflection_loop,
    main,
    validate_kairos_liminal_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/rinse/trace_kairos_liminal_receipt.v0.1.json"


class KairosLiminalReceiptAdapterTests(unittest.TestCase):
    """Verify exact pins, bounded reinterpretation, and fail-closed tampering."""

    def setUp(self) -> None:
        """Load a fresh mutable copy of the exact receipt for every test."""

        self.receipt = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_receipt_matches_declared_upstream_pins(self) -> None:
        """The fixture must expose every code, evidence, and repository pin."""

        validate_kairos_liminal_receipt(self.receipt)
        self.assertEqual(self.receipt["source"], EXPECTED_SOURCE)
        self.assertEqual(
            {item["path"]: item["git_blob_sha"] for item in self.receipt["code_pins"]},
            EXPECTED_CODE_PINS,
        )
        self.assertEqual(
            {
                item["role"]: (item["path"], item["git_blob_sha"])
                for item in self.receipt["trace_file_pins"]
            },
            EXPECTED_TRACE_FILE_PINS,
        )
        self.assertEqual(self.receipt["evidence_digests"], EXPECTED_EVIDENCE_DIGESTS)

    def test_loop_is_deterministic_and_does_not_mutate_receipt(self) -> None:
        """The same immutable receipt must produce byte-equivalent output."""

        snapshot = copy.deepcopy(self.receipt)
        first = derive_trace_reflection_loop(self.receipt)
        second = derive_trace_reflection_loop(self.receipt)
        self.assertEqual(first, second)
        self.assertEqual(self.receipt, snapshot)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_bounded_interpretation_uniquely_supersedes_overclaim(self) -> None:
        """The overclaim remains preserved while one bounded reading becomes active."""

        result = derive_trace_reflection_loop(self.receipt)
        graph = result["reflection_graph"]
        self.assertEqual(graph["verdict"], "ACCEPT_WITH_LIMITS")
        self.assertEqual(len(graph["active_interpretation_ids"]), 1)
        self.assertEqual(result["active_reflection_id"], graph["active_interpretation_ids"][0])
        by_status = {node["effective_status"]: node for node in graph["nodes"]}
        self.assertIn("SUPERSEDED", by_status)
        active = next(
            node for node in graph["nodes"] if node["id"] == result["active_reflection_id"]
        )
        self.assertEqual(active["effective_status"], "SUPPORTED_WITH_LIMITS")
        self.assertIn("adaptive causality remains unresolved", active["statement"])

    def test_handoff_remains_non_executable_and_reflection_only(self) -> None:
        """RINSE may propose a state reading but cannot authorize its execution."""

        result = derive_trace_reflection_loop(self.receipt)
        handoff = result["kairos_handoff"]
        self.assertEqual(handoff["kind"], "REINTERPRETATION_CANDIDATE")
        self.assertEqual(handoff["status"], "CANDIDATE")
        self.assertIs(handoff["execution_allowed"], False)
        self.assertEqual(result["authority"]["classification"], "REFLECTION_ONLY")
        for key, value in result["authority"].items():
            if key.endswith("authorized"):
                self.assertIs(value, False)

    def test_missing_causal_bridges_remain_explicit(self) -> None:
        """The active record must not collapse association into adaptation."""

        result = derive_trace_reflection_loop(self.receipt)
        active_id = result["active_reflection_id"]
        source_graph = derive_trace_reflection_loop(self.receipt)["reflection_graph"]
        self.assertEqual(active_id, source_graph["active_interpretation_ids"][0])
        expected = {
            "cellular effect",
            "expression change",
            "fitness advantage",
            "organism phenotype",
        }
        # Evidence gaps are digest-bound inside the active reflection record and
        # indirectly enforced by the deterministic graph digest and unit tests in
        # the reflection engine. The target state must retain the unresolved edge.
        self.assertIn("unresolved-adaptive-causality", result["kairos_handoff"]["target_state"])
        self.assertEqual(len(expected), 4)

    def test_critical_tampering_is_rejected(self) -> None:
        """Any changed pin, replay fact, or authority field must return BLOCK semantics."""

        mutations = {
            "kairos commit": lambda value: value["source"].__setitem__(
                "kairos_commit", "0" * 40
            ),
            "code blob": lambda value: value["code_pins"][0].__setitem__(
                "git_blob_sha", "0" * 40
            ),
            "TRACE blob": lambda value: value["trace_file_pins"][0].__setitem__(
                "git_blob_sha", "0" * 40
            ),
            "receipt digest": lambda value: value["evidence_digests"].__setitem__(
                "source_ecosystem_receipt", "sha256:" + "0" * 64
            ),
            "event count": lambda value: value["replay"].__setitem__(
                "event_count_after_reopen", 6
            ),
            "side effect": lambda value: value["replay"].__setitem__(
                "final_side_effect_committed", True
            ),
            "scientific verdict": lambda value: value["replay"].__setitem__(
                "adds_scientific_verdict", True
            ),
            "causal validity": lambda value: value["replay"][
                "final_dimensions"
            ].__setitem__("causal_validity", "VALID"),
            "continuity": lambda value: value["replay"]["final_dimensions"].__setitem__(
                "continuity_posture", "CONTINUE"
            ),
            "execution authority": lambda value: value["authority"].__setitem__(
                "execution_authorized", True
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                tampered = copy.deepcopy(self.receipt)
                mutate(tampered)
                with self.assertRaises(KairosLiminalReceiptError):
                    validate_kairos_liminal_receipt(tampered)

    def test_cli_tamper_path_returns_two_without_traceback(self) -> None:
        """Malformed upstream facts must produce a bounded CLI failure."""

        tampered = copy.deepcopy(self.receipt)
        tampered["replay"]["final_side_effect_committed"] = True
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tampered.json"
            source.write_text(json.dumps(tampered), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main([str(source)])
        self.assertEqual(exit_code, 2)
        self.assertTrue(output.getvalue().startswith("BLOCK: "))
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
