"""Deterministic Career RINSE pipeline.

The pipeline converts immutable career traces into evidence-backed,
provisional interpretations. It never mutates source traces and never
executes outreach. Contact suggestions always require human review.
"""

from __future__ import annotations

import copy
import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

CareerTrace = dict[str, Any]
CareerEvent = dict[str, Any]

CONFIRMED_EVENT_TYPES = {
    "assignment_received",
    "assignment_submitted",
    "assignment_acknowledged",
    "interview_invited",
    "positive_feedback",
    "hiring_paused",
    "rejected",
    "offer_received",
    "outreach_sent",
    "reply_received",
}

CONTACT_PRIORITY_WEIGHTS = {
    "positive_feedback": 5,
    "interview_invited": 4,
    "assignment_acknowledged": 3,
    "hiring_paused": 3,
    "assignment_submitted": 2,
    "assignment_received": 1,
}

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{13,19}(?!\d)")
_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|token|api[_-]?key|secret)\b\s*[:=]\s*([^\s,;]+)"
)


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _normalize_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("skills must be a list of strings")
    normalized = []
    for item in value:
        text = _require_text(item, "skills item")
        if text not in normalized:
            normalized.append(text)
    return normalized


def _canonical_timestamp(value: Any) -> str:
    text = _require_text(value, "occurred_at")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("occurred_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_sensitive_text(text: str) -> str:
    """Remove common credentials and personal contact values from text."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    redacted = _SECRET_RE.sub(lambda m: f"{m.group(1)}=[redacted-secret]", text)
    redacted = _EMAIL_RE.sub("[redacted-email]", redacted)
    redacted = _PHONE_RE.sub("[redacted-phone]", redacted)
    redacted = _LONG_NUMBER_RE.sub("[redacted-number]", redacted)
    return redacted


def redact_url(url: str) -> str:
    """Preserve a URL origin and path while stripping query and fragment data."""

    if not url:
        return ""
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return "[redacted-locator]"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def normalize_career_event(trace: CareerTrace) -> CareerEvent:
    """Normalize one source trace without mutating it."""

    if not isinstance(trace, dict):
        raise TypeError("career trace must be a dictionary")

    source = trace.get("source") or {}
    if not isinstance(source, dict):
        raise ValueError("source must be an object")

    return {
        "id": _require_text(trace.get("id"), "id"),
        "event_type": _require_text(trace.get("event_type"), "event_type"),
        "occurred_at": _canonical_timestamp(trace.get("occurred_at")),
        "company": _require_text(trace.get("company"), "company"),
        "role": (trace.get("role") or "").strip(),
        "skills": _normalize_str_list(trace.get("skills")),
        "summary": (trace.get("summary") or "").strip(),
        "contact": (trace.get("contact") or "").strip(),
        "source": {
            "kind": (source.get("kind") or "unknown").strip(),
            "locator": (source.get("locator") or "").strip(),
        },
        "derived_from": list(trace.get("derived_from") or []),
        "contradicts": list(trace.get("contradicts") or []),
    }


def classify_evidence(event: CareerEvent) -> str:
    """Classify an event as confirmed, inferred, contradicted, or unknown."""

    if event.get("contradicts"):
        return "contradicted"
    if event.get("derived_from"):
        return "inferred"
    source = event.get("source") or {}
    if event.get("event_type") in CONFIRMED_EVENT_TYPES and source.get("locator"):
        return "confirmed"
    return "unknown"


def _group_key(event: CareerEvent) -> tuple[str, str]:
    return event["company"], event.get("role") or "unspecified role"


def _confidence(events: list[CareerEvent]) -> float:
    statuses = [classify_evidence(event) for event in events]
    confirmed = statuses.count("confirmed")
    inferred = statuses.count("inferred")
    contradicted = statuses.count("contradicted")
    score = min(0.95, 0.25 + confirmed * 0.12 + inferred * 0.05)
    score -= contradicted * 0.15
    return round(max(0.0, score), 2)


def _stable_id(prefix: str, values: list[str]) -> str:
    material = "\x1f".join(sorted(values)).encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:12]
    return f"rinse-{prefix}-{digest}"


def derive_career_interpretations(events: Iterable[CareerEvent]) -> list[dict[str, Any]]:
    """Create evidence-backed interpretations grouped by company and role."""

    grouped: dict[tuple[str, str], list[CareerEvent]] = defaultdict(list)
    for event in events:
        grouped[_group_key(event)].append(event)

    interpretations = []
    for (company, role), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda item: (item["occurred_at"], item["id"]))
        confirmed = [event for event in ordered if classify_evidence(event) == "confirmed"]
        confirmed_types = {event["event_type"] for event in confirmed}
        skills = sorted({skill for event in ordered for skill in event.get("skills", [])})

        result_signals = []
        if "assignment_acknowledged" in confirmed_types:
            result_signals.append("submission acknowledged")
        if "interview_invited" in confirmed_types:
            result_signals.append("progressed to another interview stage")
        if "positive_feedback" in confirmed_types:
            result_signals.append("positive feedback recorded")
        if "hiring_paused" in confirmed_types:
            result_signals.append("hiring process paused")
        if "rejected" in confirmed_types:
            result_signals.append("rejection recorded")
        if "offer_received" in confirmed_types:
            result_signals.append("offer recorded")

        if confirmed:
            insight = f"Verified career activity with {len(confirmed)} confirmed event(s)"
        else:
            insight = "Career activity is present, but direct supporting evidence is incomplete"
        if result_signals:
            insight += ": " + "; ".join(result_signals)
        if "offer_received" not in confirmed_types:
            insight += ". No offer trace is present."

        interpretations.append(
            {
                "id": _stable_id("interpretation", [event["id"] for event in ordered]),
                "company": company,
                "role": role,
                "source_trace_ids": [event["id"] for event in ordered],
                "confirmed_trace_ids": [event["id"] for event in confirmed],
                "skills": skills,
                "insight": insight,
                "possible_reframe": (
                    "An unfinished hiring process can still be evidence of selection, "
                    "tested capability, or relationship history; it must not be promoted "
                    "to an offer or success claim without a supporting trace."
                ),
                "confidence": _confidence(ordered),
                "provisional": True,
            }
        )
    return interpretations


def build_contact_queue(
    events: Iterable[CareerEvent], *, include_contact: bool = False
) -> list[dict[str, Any]]:
    """Rank warm-contact candidates without authorizing or executing outreach."""

    grouped: dict[tuple[str, str], list[CareerEvent]] = defaultdict(list)
    for event in events:
        contact = event.get("contact") or ""
        if contact:
            grouped[(event["company"], contact)].append(event)

    queue = []
    for (company, contact), group in grouped.items():
        ordered = sorted(group, key=lambda item: (item["occurred_at"], item["id"]))
        confirmed = [event for event in ordered if classify_evidence(event) == "confirmed"]
        priority_score = sum(
            CONTACT_PRIORITY_WEIGHTS.get(event["event_type"], 0) for event in confirmed
        )
        evidence_ids = [event["id"] for event in confirmed]
        if not evidence_ids:
            continue

        latest = ordered[-1]
        queue.append(
            {
                "company": company,
                "contact": contact if include_contact else "[redacted-contact]",
                "priority_score": priority_score,
                "latest_trace_at": latest["occurred_at"],
                "evidence_trace_ids": evidence_ids,
                "reason": "confirmed prior interaction exists",
                "suggested_action": (
                    "verify that the person and address are still current, review the "
                    "message, and obtain explicit human approval before outreach"
                ),
                "execution_allowed": False,
                "requires_human_review": True,
            }
        )

    return sorted(
        queue,
        key=lambda item: (-item["priority_score"], item["company"].lower()),
    )


def build_portfolio_cases(events: Iterable[CareerEvent]) -> list[dict[str, Any]]:
    """Create public-safe case summaries without contacts or raw locators."""

    grouped: dict[tuple[str, str], list[CareerEvent]] = defaultdict(list)
    for event in events:
        grouped[_group_key(event)].append(event)

    cases = []
    for (company, role), group in sorted(grouped.items()):
        confirmed = [event for event in group if classify_evidence(event) == "confirmed"]
        if not confirmed:
            continue
        skills = sorted({skill for event in group for skill in event.get("skills", [])})
        summaries = [redact_sensitive_text(event.get("summary", "")) for event in confirmed]
        summaries = [summary for summary in summaries if summary]
        cases.append(
            {
                "case_id": _stable_id("case", [event["id"] for event in group]),
                "company": company,
                "role": role,
                "skills": skills,
                "verified_events": sorted({event["event_type"] for event in confirmed}),
                "evidence_count": len(confirmed),
                "summary": " ".join(summaries),
                "public_safe": True,
            }
        )
    return cases


def run_career_rinse(traces: list[CareerTrace]) -> dict[str, Any]:
    """Run the deterministic Career RINSE transformation.

    The input list and its dictionaries remain unchanged. The returned contact
    queue is redacted and cannot authorize execution.
    """

    snapshot = copy.deepcopy(traces)
    events = [normalize_career_event(trace) for trace in traces]
    result = {
        "events": events,
        "interpretations": derive_career_interpretations(events),
        "contact_queue": build_contact_queue(events),
        "portfolio_cases": build_portfolio_cases(events),
        "policy": {
            "source_mutation_allowed": False,
            "automatic_outreach_allowed": False,
            "human_review_required": True,
        },
    }
    if traces != snapshot:
        raise RuntimeError("Career RINSE mutated source traces")
    return result
