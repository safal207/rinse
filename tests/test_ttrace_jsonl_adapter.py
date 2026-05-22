"""Tests for the read-only T-Trace JSONL source adapter."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rinse import run
from rinse.adapters import TTraceJsonLinesSource

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "sample_ttrace.jsonl"


class TTraceJsonLinesSourceTests(unittest.TestCase):
    def test_reads_jsonl_as_normalized_rinse_traces(self):
        original = FIXTURE.read_text(encoding="utf-8")
        traces = list(TTraceJsonLinesSource(FIXTURE).read_traces())

        self.assertEqual(len(traces), 3)
        self.assertEqual(traces[0]["id"], "trace-jsonl-001")
        self.assertEqual(traces[0]["ts"], "2026-05-07T10:00:00Z")
        self.assertEqual(traces[0]["actor"], "human")
        self.assertEqual(traces[0]["kind"], "utterance")
        self.assertEqual(traces[0]["text"], "I am anxious because the deadline is close.")
        self.assertEqual(traces[0]["context"]["channel"], "jsonl")
        self.assertEqual(traces[0]["context"]["ttrace_line"], 1)

        self.assertEqual(traces[1]["id"], "trace-jsonl-002")
        self.assertEqual(traces[1]["ts"], "2026-05-07T10:01:00Z")
        self.assertEqual(traces[1]["kind"], "observation")
        self.assertEqual(traces[1]["text"], "The spec is clear so the work can continue.")
        self.assertEqual(traces[1]["context"]["ttrace_line"], 2)

        self.assertEqual(traces[2]["id"], "trace-jsonl-003")
        self.assertEqual(traces[2]["kind"], "state")
        self.assertEqual(traces[2]["text"], "asdfgh")
        self.assertEqual(traces[2]["context"]["ttrace_line"], 4)

        self.assertEqual(FIXTURE.read_text(encoding="utf-8"), original)

    def test_adapter_output_can_feed_rinse_run(self):
        traces = list(TTraceJsonLinesSource(FIXTURE).read_traces())
        records = run(traces)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["source_trace_ids"], ["trace-jsonl-001"])
        self.assertEqual(records[1]["source_trace_ids"], ["trace-jsonl-002"])

    def test_invalid_jsonl_raises_value_error_with_line_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text('{"id":"ok","text":"valid"}\nnot-json\n', encoding="utf-8")

            source = TTraceJsonLinesSource(path)
            with self.assertRaisesRegex(ValueError, "line 2"):
                list(source.read_traces())

    def test_missing_required_fields_raise_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.jsonl"
            path.write_text(json.dumps({"id": "trace-missing"}) + "\n", encoding="utf-8")

            source = TTraceJsonLinesSource(path)
            with self.assertRaisesRegex(ValueError, "missing trace text"):
                list(source.read_traces())


if __name__ == "__main__":
    unittest.main()
