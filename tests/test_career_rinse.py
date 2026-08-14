"""Tests for the deterministic Career RINSE domain adapter."""

from __future__ import annotations

import copy
import unittest

from rinse.career import (
    build_career_reflection_records,
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

    def test_career_uses_shared_reflection_record_as_semantic_authority(self):
        output = run_career_rinse(
            [
                _trace("t1", "assignment_received"),
                _trace("t2", "interview_invited", occurred_at="2022-01-02T00:00:00Z"),
            ]
        )
        record = output["reflection_records"][0]
        projection = output["interpretations"][0]

        self.assertEqual(record["schema"], "rinse.reflection-record.v0.2")
        self.assertEqual(projection["id"], record["id"])
        self.assertEqual(projection["reflection_record_id"], record["id"])
        self.assertEqual(projection["semantic_authority"], record["schema"])
        self.assertEqual(projection["status"], record["status"])
        self.assertEqual(output["policy"]["interpretation_authority"], record["schema"])
        self.assertTrue(output["policy"]["domain_projection_only"])

    def test_unfinished_confirmed_process_is_supported_with_limits(self):
        events = [
            normalize_career_event(_trace("t1", "assignment_acknowledged")),
            normalize_career_event(
                _trace("t2", "interview_invited", occurred_at="2022-01-02T00:00:00Z")
            ),
        ]
        record = build_career_reflection_records(events)[0]

        self.assertEqual(record["status"], "SUPPORTED_WITH_LIMITS")
        self.assertIn("final hiring outcome", record["missing_evidence"])
        self.assertFalse(record["proposed_transition"]["execution_allowed"])
        self.assertEqual(record["authority"]["classification"], "REFLECTION_ONLY")
        self.assertFalse(record["authority"]["execution_authorized"])

    def test_terminal_offer_is_supported_only_when_direct_offer_trace_exists(self):
        events = [
            normalize_career_event(_trace("t1", "interview_invited")),
            normalize_career_event(
                _trace("t2", "offer_received", occurred_at="2022-01-02T00:00:00Z")
            ),
        ]
        record = build_career_reflection_records(events)[0]

        self.assertEqual(record["status"], "SUPPORTED")
        self.assertEqual(record["missing_evidence"], [])
        self.assertIn("offer recorded", record["statement"])

    def test_no_direct_support_is_insufficient_evidence(self):
        trace = _trace("t1", "assignment_acknowledged")
        trace["derived_from"] = ["source-t0"]
        event = normalize_career_event(trace)
        record = build_career_reflection_records([event])[0]

        self.assertEqual(record["status"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("direct supporting career trace", record["missing_evidence"])
        self.assertEqual(record["evidence_relations"], [])

    def test_contradicted_group_uses_core_contested_semantics(self):
        direct = normalize_career_event(_trace("t1", "positive_feedback"))
        contradiction = _trace(
            "t2", "positive_feedback", occurred_at="2022-01-02T00:00:00Z"
        )
        contradiction["contradicts"] = ["t1"]
        record = build_career_reflection_records(
            [direct, normalize_career_event(contradiction)]
        )[0]

        self.assertEqual(record["status"], "CONTESTED")
        self.assertTrue(
            any(rel["type"] == "CONTRADICTED_BY" for rel in record["evidence_relations"])
        )

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
