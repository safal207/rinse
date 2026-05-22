"""Tests for dependency-free RINSE structural validation helpers."""

from __future__ import annotations

import copy
import unittest

from rinse import (
    ValidationError,
    interpret,
    validate_interpretation_record,
    validate_interpretation_records,
    validate_trace_event,
    validate_trace_events,
)


def _trace() -> dict:
    return {
        "id": "trace-valid",
        "ts": "2026-05-07T00:00:00Z",
        "actor": "human",
        "kind": "utterance",
        "text": "I am anxious because the deadline is close.",
        "context": {},
    }


def _interpretation() -> dict:
    return interpret(_trace())


class TraceValidationTests(unittest.TestCase):
    def test_valid_trace_event_passes_without_mutation(self):
        trace = _trace()
        snapshot = copy.deepcopy(trace)

        validate_trace_event(trace)

        self.assertEqual(trace, snapshot)

    def test_trace_events_list_passes(self):
        validate_trace_events([_trace()])

    def test_trace_must_be_object(self):
        with self.assertRaisesRegex(ValidationError, "trace must be an object"):
            validate_trace_event([])

    def test_trace_requires_non_empty_id(self):
        trace = _trace()
        trace["id"] = ""

        with self.assertRaisesRegex(ValidationError, "trace.id"):
            validate_trace_event(trace)

    def test_trace_requires_non_empty_text(self):
        trace = _trace()
        trace["text"] = "  "

        with self.assertRaisesRegex(ValidationError, "trace.text"):
            validate_trace_event(trace)

    def test_trace_context_must_be_object_when_present(self):
        trace = _trace()
        trace["context"] = "not-an-object"

        with self.assertRaisesRegex(ValidationError, "trace.context"):
            validate_trace_event(trace)

    def test_trace_events_requires_list(self):
        with self.assertRaisesRegex(ValidationError, "trace events must be a list"):
            validate_trace_events({})


class InterpretationValidationTests(unittest.TestCase):
    def test_valid_interpretation_passes_without_mutation(self):
        record = _interpretation()
        snapshot = copy.deepcopy(record)

        validate_interpretation_record(record)

        self.assertEqual(record, snapshot)

    def test_interpretation_records_list_passes(self):
        validate_interpretation_records([_interpretation()])

    def test_interpretation_requires_all_contract_fields(self):
        record = _interpretation()
        del record["source_trace_ids"]

        with self.assertRaisesRegex(ValidationError, "source_trace_ids"):
            validate_interpretation_record(record)

    def test_source_trace_ids_must_be_non_empty_list(self):
        record = _interpretation()
        record["source_trace_ids"] = []

        with self.assertRaisesRegex(ValidationError, "source_trace_ids"):
            validate_interpretation_record(record)

    def test_emotions_and_signals_must_be_lists_of_strings(self):
        record = _interpretation()
        record["emotions"] = ["fear", 42]

        with self.assertRaisesRegex(ValidationError, "emotions"):
            validate_interpretation_record(record)

    def test_clarity_must_be_number_between_zero_and_one(self):
        record = _interpretation()
        record["clarity"] = 1.5

        with self.assertRaisesRegex(ValidationError, "clarity"):
            validate_interpretation_record(record)

    def test_clarity_must_not_be_bool(self):
        record = _interpretation()
        record["clarity"] = True

        with self.assertRaisesRegex(ValidationError, "clarity"):
            validate_interpretation_record(record)

    def test_causal_links_must_contain_cause_and_effect(self):
        record = _interpretation()
        record["causal_links"] = [{"cause": "deadline"}]

        with self.assertRaisesRegex(ValidationError, "effect"):
            validate_interpretation_record(record)

    def test_interpretation_records_requires_list(self):
        with self.assertRaisesRegex(ValidationError, "interpretation records must be a list"):
            validate_interpretation_records({})


if __name__ == "__main__":
    unittest.main()
