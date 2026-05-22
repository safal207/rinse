"""Read-only T-Trace JSONL source adapter.

The adapter reads append-only JSONL trace streams and normalizes each record into
the minimal RINSE trace shape. It never writes to the source file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


class TTraceJsonLinesSource:
    """Read T-Trace-style JSONL records as normalized RINSE traces."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read_traces(self) -> Iterator[dict]:
        with self._path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL record at line {line_number}: {exc.msg}"
                    ) from exc
                yield self._normalize_record(record, line_number)

    def _normalize_record(self, record: dict, line_number: int) -> dict:
        if not isinstance(record, dict):
            raise ValueError(f"expected object at line {line_number}")

        trace_id = record.get("id") or record.get("trace_id") or record.get("event_id")
        if not trace_id:
            raise ValueError(f"missing trace id at line {line_number}")

        text = record.get("text") or record.get("message") or record.get("content")
        if not text:
            raise ValueError(f"missing trace text at line {line_number}")

        context = record.get("context")
        if context is None:
            context = {}
        if not isinstance(context, dict):
            raise ValueError(f"context must be an object at line {line_number}")

        context = {
            **context,
            "ttrace_line": line_number,
        }

        return {
            "id": str(trace_id),
            "ts": record.get("ts") or record.get("timestamp"),
            "actor": record.get("actor"),
            "kind": record.get("kind") or record.get("type"),
            "text": str(text),
            "context": context,
        }
