"""Tests for the RINSE reference pipeline.

Stdlib only. Runs via `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from rinse import bridge as bridge_records
from rinse import detect_signals, extract_causal_links, filter_noise, interpret, run, tag_emotions
from rinse.bridge import main as bridge_main


def _trace(text, trace_id="trace-x", actor="human", kind="utterance"):
    return {
        "id": trace_id,
        "ts": "2026-05-07T00:00:00Z",
        "actor": actor,
        "kind": kind,
        "text": text,
        "context": {},
    }


class FilterNoiseTests(unittest.TestCase):
    def test_short_garbage_is_filtered(self):
        self.assertFalse(filter_noise(_trace("asdfgh")))

    def test_meaningful_text_passes(self):
        self.assertTrue(filter_noise(_trace("I finished the spec today.")))


class CausalLinkTests(unittest.TestCase):
    def test_because_creates_causal_link(self):
        text = "I am tired because I slept badly"
        links = extract_causal_links(text)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["cause"], "I slept badly")
        self.assertEqual(links[0]["effect"], "I am tired")


class SignalAndEmotionTests(unittest.TestCase):
    def test_deadline_anxious_yields_pressure_and_fear(self):
        text = "I am anxious because the deadline is close"
        self.assertIn("deadline_pressure", detect_signals(text))
        self.assertIn("fear", tag_emotions(text))

    def test_word_boundary_does_not_overmatch(self):
        text = "the nuclear option"
        self.assertNotIn("clarity", tag_emotions(text))

        text2 = "a single droplet of water"
        self.assertNotIn("incomplete_followthrough", detect_signals(text2))


class InterpretRecordTests(unittest.TestCase):
    def test_record_carries_source_trace_id(self):
        trace = _trace("I am anxious because the deadline is close", trace_id="trace-42")
        record = interpret(trace)
        self.assertEqual(record["source_trace_ids"], ["trace-42"])
        self.assertIn("insight", record)
        self.assertIn("clarity", record)
        self.assertIn("next_step", record)

    def test_source_trace_is_not_mutated(self):
        trace = _trace("I am anxious because the deadline is close", trace_id="trace-42")
        snapshot = copy.deepcopy(trace)
        interpret(trace)
        self.assertEqual(trace, snapshot)

    def test_run_filters_noise_before_interpreting(self):
        traces = [
            _trace("asdfgh", trace_id="n1"),
            _trace("I finished the spec today.", trace_id="ok1"),
        ]
        snapshot = copy.deepcopy(traces)
        records = run(traces)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_trace_ids"], ["ok1"])
        self.assertEqual(traces, snapshot)


class MemoryBridgeTests(unittest.TestCase):
    def test_public_bridge_is_importable(self):
        self.assertTrue(callable(bridge_records))

    def test_bridge_writes_only_non_noise_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "in.json"
            output_path = tmp_path / "out.jsonl"
            payload = {
                "traces": [
                    _trace("asdfgh", trace_id="n1"),
                    _trace("I finished the spec today.", trace_id="ok1"),
                ]
            }
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            written = bridge_main([
                "rinse-bridge",
                str(input_path),
                str(output_path),
            ])
            self.assertEqual(written, 0)

            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["source_trace_ids"], ["ok1"])

            reread = json.loads(input_path.read_text(encoding="utf-8"))
            self.assertEqual(reread, payload)


if __name__ == "__main__":
    unittest.main()
