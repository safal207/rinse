"""Career RINSE domain-adapter API."""

from .pipeline import (
    build_career_reflection_records,
    build_contact_queue,
    build_portfolio_cases,
    classify_evidence,
    derive_career_interpretations,
    normalize_career_event,
    redact_sensitive_text,
    redact_url,
    run_career_rinse,
)

__all__ = [
    "normalize_career_event",
    "classify_evidence",
    "build_career_reflection_records",
    "derive_career_interpretations",
    "build_contact_queue",
    "build_portfolio_cases",
    "redact_sensitive_text",
    "redact_url",
    "run_career_rinse",
]
