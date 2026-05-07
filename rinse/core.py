"""Reference RINSE pipeline.

Dependency-free, deterministic, and read-only on input traces.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

Trace = dict[str, Any]
Interpretation = dict[str, Any]

EMOTION_LEXICON = {
    "joy": ["happy", "glad", "excited", "joy", "delighted"],
    "sadness": ["sad", "tired", "drained", "down", "lonely"],
    "anger": ["angry", "furious", "irritated", "annoyed"],
    "fear": ["anxious", "afraid", "scared", "worried", "nervous"],
    "clarity": ["clear", "clearer", "focused", "finished", "done"],
    "avoidance": [
        "avoid",
        "avoids",
        "avoided",
        "drop",
        "drops",
        "dropped",
        "dropping",
        "procrastinate",
    ],
}

CAUSE_CUES = ("because", "so", "therefore", "since", "when")

SIGNAL_PATTERNS = {
    "deadline_pressure": ["deadline", "deadlines"],
    "planning": ["spec", "specs", "plan", "plans", "planning"],
    "incomplete_followthrough": ["drop", "drops", "dropped", "dropping"],
    "sleep_state": ["sleep", "sleeping", "slept"],
}

NOISE_TOKEN_RE = re.compile(r"^[a-z]{2,}$")


def _has_word(text: str, words: list[str]) -> bool:
    if not words:
        return False
    pattern = r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b"
    return re.search(pattern, text, re.IGNORECASE) is not None


def filter_noise(trace: Trace) -> bool:
    """Return True when a trace contains enough signal to interpret."""

    text = (trace.get("text") or "").strip()
    if len(text) < 8:
        return False
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    if not tokens:
        return False
    distinct = set(tokens)
    if len(distinct) == 1 and NOISE_TOKEN_RE.match(next(iter(distinct))):
        return False
    return True


def detect_signals(text: str) -> list[str]:
    return [name for name, words in SIGNAL_PATTERNS.items() if _has_word(text, words)]


def tag_emotions(text: str) -> list[str]:
    return [label for label, words in EMOTION_LEXICON.items() if _has_word(text, words)]


def extract_causal_links(text: str) -> list[dict[str, str]]:
    links = []
    lower = text.lower()
    for cue in CAUSE_CUES:
        idx = lower.find(f" {cue} ")
        if idx == -1:
            continue
        left = text[:idx].strip(" .,;:")
        right = text[idx + len(cue) + 2 :].strip(" .,;:")
        if left and right:
            if cue in ("because", "since"):
                links.append({"cause": right, "effect": left})
            else:
                links.append({"cause": left, "effect": right})
    return links


def synthesize_insight(
    emotions: list[str],
    signals: list[str],
    causal_links: list[dict[str, str]],
) -> str:
    parts = []
    if emotions:
        parts.append("emotional tone: " + ", ".join(emotions))
    if signals:
        parts.append("signals: " + ", ".join(signals))
    if causal_links:
        first = causal_links[0]
        parts.append(f"pattern: {first['cause']} -> {first['effect']}")
    if not parts:
        return "no salient interpretation"
    return "; ".join(parts)


def score_clarity(
    text: str,
    emotions: list[str],
    signals: list[str],
    causal_links: list[dict[str, str]],
) -> float:
    score = 0.0
    if emotions:
        score += 0.3
    if signals:
        score += 0.3
    if causal_links:
        score += 0.3
    if len(text.split()) >= 8:
        score += 0.1
    return round(min(score, 1.0), 2)


def suggest_next_step(emotions: list[str], signals: list[str]) -> str:
    if "deadline_pressure" in signals and "fear" in emotions:
        return "open the editor for ten minutes without a goal"
    if "incomplete_followthrough" in signals:
        return "write a one-line spec before starting the next project"
    if "sleep_state" in signals and "sadness" in emotions:
        return "treat today as a recovery day; defer judgment of progress"
    if "planning" in signals and "clarity" in emotions:
        return "reuse the spec-first pattern on the next task"
    return "note the trace and revisit tomorrow"


def interpret(trace: Trace) -> Interpretation:
    """Create a derived interpretation record without mutating the source trace."""

    text = trace["text"]
    emotions = tag_emotions(text)
    signals = detect_signals(text)
    causal_links = extract_causal_links(text)
    return {
        "id": f"rinse-{uuid.uuid4().hex[:12]}",
        "source_trace_ids": [trace["id"]],
        "emotions": emotions,
        "signals": signals,
        "causal_links": causal_links,
        "insight": synthesize_insight(emotions, signals, causal_links),
        "clarity": score_clarity(text, emotions, signals, causal_links),
        "next_step": suggest_next_step(emotions, signals),
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }


def run(traces: list[Trace]) -> list[Interpretation]:
    return [interpret(t) for t in traces if filter_noise(t)]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m rinse.core <input.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    traces = data.get("traces", [])
    records = run(traces)
    print(json.dumps({"interpretations": records}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
