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
]
