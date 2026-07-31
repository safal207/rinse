"""Tests for the deterministic Career RINSE pipeline."""

from __future__ import annotations

import copy
import unittest

from rinse.career import (
    build_contact_queue,
    classify_evidence,
    normalize_career_event,
    run_career_rinse,
)


def _trace(
    trace_id: str,
    event_type: str,
    *,
    occurred_at: str = "2022-01-01T00:00:00Z",
    contact: str = "recruiter@example.com",
    summary: str = "",
):
    return {
        "id": trace_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "company": "Example Co",
        "role": "QA Engineer",
        "skills": ["SQL", "REST API"],
        "summary": summary,
        "contact": contact,
        "source": {
            "kind": "gmail",
            "locator": f"gmail://message/{trace_id}",
        },
    }


class CareerRinseTests(unittest.TestCase):
    def test_normalization_does_not_mutate_trace(self):
        trace = _trace("t1", "assignment_received")
        snapshot = copy.deepcopy(trace)
        normalize_career_event(trace)
        self.assertEqual(trace, snapshot)

    def test_direct_message_event_is_confirmed(self):
        event = normalize_career_event(_trace("t1", "assignment_acknowledged"))
        self.assertEqual(classify_evidence(event), "confirmed")

    def test_derived_event_is_inferred_even_with_locator(self):
        trace = _trace("t2", "assignment_acknowledged")
        trace["derived_from"] = ["t1"]
        event = normalize_career_event(trace)
        self.assertEqual(classify_evidence(event), "inferred")

    def test_no_offer_claim_without_offer_trace(self):
        traces = [
            _trace("t1", "assignment_received"),
            _trace("t2", "assignment_acknowledged"),
            _trace("t3", "interview_invited"),
        ]
        output = run_career_rinse(traces)
        insight = output["interpretations"][0]["insight"]
        self.assertIn("No offer trace is present", insight)
        self.assertNotIn("offer recorded", insight)

    def test_contact_queue_never_allows_execution(self):
        event = normalize_career_event(_trace("t1", "positive_feedback"))
        item = build_contact_queue([event], include_contact=True)[0]
        self.assertFalse(item["execution_allowed"])
        self.assertTrue(item["requires_human_review"])
        self.assertEqual(item["contact"], "recruiter@example.com")

    def test_default_contact_queue_redacts_contact(self):
        output = run_career_rinse([_trace("t1", "interview_invited")])
        self.assertEqual(output["contact_queue"][0]["contact"], "[redacted-contact]")

    def test_source_traces_remain_unchanged(self):
        traces = [_trace("t1", "assignment_received")]
        snapshot = copy.deepcopy(traces)
        run_career_rinse(traces)
        self.assertEqual(traces, snapshot)

    def test_public_case_redacts_personal_data_and_secret(self):
        summary = (
            "Contact recruiter@example.com at +7 999 123-45-67; "
            "token=abc123 and card 4111111111111111"
        )
        output = run_career_rinse([_trace("t1", "positive_feedback", summary=summary)])
        case_summary = output["portfolio_cases"][0]["summary"]
        self.assertNotIn("recruiter@example.com", case_summary)
        self.assertNotIn("abc123", case_summary)
        self.assertNotIn("4111111111111111", case_summary)
        self.assertIn("[redacted-email]", case_summary)
        self.assertIn("[redacted-secret]", case_summary)


if __name__ == "__main__":
    unittest.main()
