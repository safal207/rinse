import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rinse import reflection_graph as rg


class ReflectionGraphTests(unittest.TestCase):
    def base_record(self, **overrides):
        params = {
            "subject_id": "case-001",
            "statement": "The observed association does not yet establish causality.",
            "status": "SUPPORTED_WITH_LIMITS",
            "source_trace_ids": ["trace-2", "trace-1", "trace-1"],
            "evidence_relations": [
                {"type": "SUPPORTED_BY", "ref": "proofpath:C10"},
            ],
            "recorded_time": "2026-07-31T09:00:00Z",
            "reviewed_time": "2026-07-31T09:05:00Z",
            "valid_from": "2026-07-31T09:00:00Z",
            "proposed_target_state": "request missing causal evidence",
            "confidence": 0.81,
            "missing_evidence": ["cellular effect", "expression change"],
        }
        params.update(overrides)
        return rg.create_reflection_record(**params)

    def test_record_is_deterministic_and_normalized(self):
        first = self.base_record()
        second = self.base_record()
        self.assertEqual(first, second)
        self.assertEqual(first["source_trace_ids"], ["trace-1", "trace-2"])
        self.assertEqual(
            first["missing_evidence"], ["cellular effect", "expression change"]
        )
        self.assertTrue(first["digest"].startswith("sha256:"))

    def test_input_collections_are_not_mutated(self):
        traces = ["trace-b", "trace-a"]
        evidence = [{"type": "SUPPORTED_BY", "ref": "evidence-1"}]
        missing = ["phenotype", "expression"]
        before = copy.deepcopy((traces, evidence, missing))
        self.base_record(
            source_trace_ids=traces,
            evidence_relations=evidence,
            missing_evidence=missing,
        )
        self.assertEqual((traces, evidence, missing), before)

    def test_kairos_candidate_cannot_authorize_execution(self):
        record = self.base_record()
        record["proposed_transition"]["execution_allowed"] = True
        record["digest"] = rg._sha256_ref(rg._semantic_body(record))
        with self.assertRaisesRegex(rg.ReflectionGraphError, "non-executable"):
            rg.validate_reflection_record(record)

    def test_authority_escalation_fails_closed(self):
        record = self.base_record()
        record["authority"]["truth_authorized"] = True
        record["digest"] = rg._sha256_ref(rg._semantic_body(record))
        with self.assertRaisesRegex(rg.ReflectionGraphError, "authority boundary"):
            rg.validate_reflection_record(record)

    def test_supported_with_limits_requires_missing_evidence(self):
        with self.assertRaisesRegex(rg.ReflectionGraphError, "missing_evidence"):
            self.base_record(missing_evidence=[])

    def test_contested_requires_contradicting_evidence(self):
        with self.assertRaisesRegex(rg.ReflectionGraphError, "CONTRADICTING"):
            self.base_record(status="CONTESTED", missing_evidence=[])

    def test_missing_predecessor_is_rejected(self):
        record = self.base_record(
            interpretation_relations=[
                {
                    "type": "SUPERSEDES",
                    "target_id": "rinse-reflection-0000000000000000",
                }
            ]
        )
        with self.assertRaisesRegex(rg.ReflectionGraphError, "missing interpretation"):
            rg.build_reflection_graph([record])

    def test_supersession_cycle_is_rejected(self):
        first_seed = self.base_record(
            statement="First reading.",
            status="PROPOSED",
            evidence_relations=[],
            missing_evidence=[],
            recorded_time="2026-07-31T09:00:00Z",
            reviewed_time="2026-07-31T09:00:00Z",
            valid_from="2026-07-31T09:00:00Z",
        )
        second_seed = self.base_record(
            statement="Second reading.",
            status="PROPOSED",
            evidence_relations=[],
            missing_evidence=[],
            recorded_time="2026-07-31T09:00:00Z",
            reviewed_time="2026-07-31T09:00:00Z",
            valid_from="2026-07-31T09:00:00Z",
        )
        first = self.base_record(
            statement="First reading.",
            status="PROPOSED",
            evidence_relations=[],
            missing_evidence=[],
            recorded_time="2026-07-31T09:00:00Z",
            reviewed_time="2026-07-31T09:02:00Z",
            valid_from="2026-07-31T09:00:00Z",
            interpretation_relations=[
                {"type": "SUPERSEDES", "target_id": second_seed["id"]}
            ],
        )
        second = self.base_record(
            statement="Second reading.",
            status="PROPOSED",
            evidence_relations=[],
            missing_evidence=[],
            recorded_time="2026-07-31T09:00:00Z",
            reviewed_time="2026-07-31T09:02:00Z",
            valid_from="2026-07-31T09:00:00Z",
            interpretation_relations=[
                {"type": "SUPERSEDES", "target_id": first_seed["id"]}
            ],
        )
        self.assertEqual(first["id"], first_seed["id"])
        self.assertEqual(second["id"], second_seed["id"])
        with self.assertRaisesRegex(rg.ReflectionGraphError, "cycle"):
            rg.build_reflection_graph([first, second])

    def test_trace_example_supersedes_overclaim(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "examples/rinse/trace_reinterpretation_v0.2.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        graph = rg.build_reflection_graph(payload["records"])
        self.assertEqual(graph["verdict"], "ACCEPT_WITH_LIMITS")
        self.assertEqual(len(graph["active_interpretation_ids"]), 1)
        statuses = {
            node["statement"]: node["effective_status"] for node in graph["nodes"]
        }
        self.assertEqual(
            statuses["Archaic regions near immune genes establish adaptive benefit."],
            "SUPERSEDED",
        )
        self.assertFalse(graph["candidate_handoffs"][0]["execution_allowed"])
        self.assertFalse(graph["authority"]["truth_authorized"])

    def test_cli_writes_deterministic_graph(self):
        root = Path(__file__).resolve().parents[1]
        source = root / "examples/rinse/trace_reinterpretation_v0.2.json"
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            for output in (first, second):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "rinse.reflection_graph",
                        str(source),
                        "--output",
                        str(output),
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
