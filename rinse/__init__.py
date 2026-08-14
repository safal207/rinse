"""RINSE public package API.

RINSE is a reflective interpretation layer over trace and memory substrates.
It reads source traces and writes only derived interpretation records.
"""

from .core import (
    detect_signals,
    extract_causal_links,
    filter_noise,
    interpret,
    run,
    score_clarity,
    suggest_next_step,
    synthesize_insight,
    tag_emotions,
)
from .bridge import (
    InterpretationSink,
    JsonFileTraceSource,
    JsonLinesInterpretationSink,
    TraceSource,
    bridge,
)
from .reflection_graph import (
    EFFECTIVE_STATUSES,
    EVIDENCE_RELATIONS,
    GRAPH_SCHEMA,
    INTERPRETATION_RELATIONS,
    RECORD_STATUSES,
    SCHEMA,
    ReflectionGraphError,
    build_reflection_graph,
    create_reflection_record,
    validate_reflection_graph,
    validate_reflection_record,
)
from .validation import (
    ValidationError,
    validate_interpretation_record,
    validate_interpretation_records,
    validate_trace_event,
    validate_trace_events,
)

__all__ = [
    "detect_signals",
    "extract_causal_links",
    "filter_noise",
    "interpret",
    "run",
    "score_clarity",
    "suggest_next_step",
    "synthesize_insight",
    "tag_emotions",
    "TraceSource",
    "InterpretationSink",
    "JsonFileTraceSource",
    "JsonLinesInterpretationSink",
    "bridge",
    "ValidationError",
    "validate_trace_event",
    "validate_trace_events",
    "validate_interpretation_record",
    "validate_interpretation_records",
    "SCHEMA",
    "GRAPH_SCHEMA",
    "RECORD_STATUSES",
    "EFFECTIVE_STATUSES",
    "EVIDENCE_RELATIONS",
    "INTERPRETATION_RELATIONS",
    "ReflectionGraphError",
    "create_reflection_record",
    "validate_reflection_record",
    "validate_reflection_graph",
    "build_reflection_graph",
]
