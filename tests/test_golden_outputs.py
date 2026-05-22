"""Golden-output regression tests for the deterministic RINSE pipeline.

To intentionally update the golden fixture:

1. Review the pipeline change and confirm the new interpretation behavior is expected.
2. Run RINSE against tests/fixtures/sample_traces.json.
3. Replace only deterministic fields in sample_interpretations.golden.json.
4. Keep generated fields normalized as "<generated>".
5. Verify source traces are still unchanged.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from rinse import run

ROOT = Path(__file__).resolve().parent.parent
TRACE_FIXTURE = ROOT / "tests" / "fixtures" / "sample_traces.json"
GOLDEN_FIXTURE = ROOT / "tests" / "fixtures" / "sample_interpretations.golden.json"

GENERATED_PLACEHOLDER = "<generated>"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_generated_fields(records: list[dict]) -> list[dict]:
    normalized = copy.deepcopy(records)
    for record in normalized:
        record["id"] = GENERATED_PLACEHOLDER
        record["produced_at"] = GENERATED_PLACEHOLDER
    return normalized


class GoldenOutputTests(unittest.TestCase):
    def test_sample_traces_match_golden_interpretations(self):
        payload = _load_json(TRACE_FIXTURE)
        expected = _load_json(GOLDEN_FIXTURE)
        traces = payload["traces"]
        trace_snapshot = copy.deepcopy(traces)

        actual = {"interpretations": _normalize_generated_fields(run(traces))}

        self.assertEqual(actual, expected)
        self.assertEqual(traces, trace_snapshot)


if __name__ == "__main__":
    unittest.main()
