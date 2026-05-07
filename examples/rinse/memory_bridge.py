"""Read-only adapter interface between RINSE and an underlying trace store.

The bridge never writes to or mutates the source substrate. Derived
interpretation records are persisted to a separate RINSE store passed in by
the caller.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Protocol


class TraceSource(Protocol):
    def read_traces(self) -> Iterable[dict]:
        ...


class InterpretationSink(Protocol):
    def write(self, record: dict) -> None:
        ...


class JsonFileTraceSource:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read_traces(self) -> Iterator[dict]:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        for trace in data.get("traces", []):
            yield trace


class JsonLinesInterpretationSink:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def bridge(source: TraceSource, sink: InterpretationSink, interpret_fn) -> int:
    count = 0
    for trace in source.read_traces():
        record = interpret_fn(trace)
        if record is None:
            continue
        sink.write(record)
        count += 1
    return count
