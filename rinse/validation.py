"""Dependency-free structural validation helpers for RINSE records.

These helpers intentionally do not implement full JSON Schema validation. They
check the project-critical fields used by the reference pipeline and contracts.
"""

from __future__ import annotations

from typing import Any


class ValidationError(ValueError):
    """Raised when a RINSE record fails structural validation."""


INTERPRETATION_REQUIRED_FIELDS = (
    "id",
    "source_trace_ids",
    "emotions",
    "signals",
    "causal_links",
    "insight",
    "clarity",
    "next_step",
    "produced_at",
)


def _require_mapping(record: Any, name: str) -> dict:
    if not isinstance(record, dict):
        raise ValidationError(f"{name} must be an object")
    return record


def _require_non_empty_string(record: dict, field: str, name: str) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name}.{field} must be a non-empty string")


def validate_trace_event(record: Any) -> None:
    """Validate the minimal RINSE trace input shape.

    The trace is treated as source evidence. This function only validates
    structure and never mutates the record.
    """

    trace = _require_mapping(record, "trace")
    _require_non_empty_string(trace, "id", "trace")
    _require_non_empty_string(trace, "text", "trace")

    context = trace.get("context")
    if context is not None and not isinstance(context, dict):
        raise ValidationError("trace.context must be an object when present")


def validate_interpretation_record(record: Any) -> None:
    """Validate the minimal RINSE derived interpretation shape."""

    interpretation = _require_mapping(record, "interpretation")

    for field in INTERPRETATION_REQUIRED_FIELDS:
        if field not in interpretation:
            raise ValidationError(f"interpretation.{field} is required")

    _require_non_empty_string(interpretation, "id", "interpretation")
    _require_non_empty_string(interpretation, "insight", "interpretation")
    _require_non_empty_string(interpretation, "next_step", "interpretation")
    _require_non_empty_string(interpretation, "produced_at", "interpretation")

    source_trace_ids = interpretation["source_trace_ids"]
    if not isinstance(source_trace_ids, list) or not source_trace_ids:
        raise ValidationError("interpretation.source_trace_ids must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in source_trace_ids):
        raise ValidationError("interpretation.source_trace_ids must contain non-empty strings")

    for field in ("emotions", "signals"):
        value = interpretation[field]
        if not isinstance(value, list):
            raise ValidationError(f"interpretation.{field} must be a list")
        if not all(isinstance(item, str) for item in value):
            raise ValidationError(f"interpretation.{field} must contain strings")

    clarity = interpretation["clarity"]
    if not isinstance(clarity, (int, float)) or isinstance(clarity, bool):
        raise ValidationError("interpretation.clarity must be a number")
    if clarity < 0 or clarity > 1:
        raise ValidationError("interpretation.clarity must be between 0 and 1")

    causal_links = interpretation["causal_links"]
    if not isinstance(causal_links, list):
        raise ValidationError("interpretation.causal_links must be a list")
    for index, link in enumerate(causal_links):
        if not isinstance(link, dict):
            raise ValidationError(f"interpretation.causal_links[{index}] must be an object")
        _require_non_empty_string(link, "cause", f"interpretation.causal_links[{index}]")
        _require_non_empty_string(link, "effect", f"interpretation.causal_links[{index}]")


def validate_trace_events(records: list[Any]) -> None:
    """Validate a list of RINSE trace input records."""

    if not isinstance(records, list):
        raise ValidationError("trace events must be a list")
    for record in records:
        validate_trace_event(record)


def validate_interpretation_records(records: list[Any]) -> None:
    """Validate a list of RINSE derived interpretation records."""

    if not isinstance(records, list):
        raise ValidationError("interpretation records must be a list")
    for record in records:
        validate_interpretation_record(record)
