"""Read-only adapter interface between RINSE and an underlying trace store.

The bridge never writes to or mutates the source substrate. Derived
interpretation records are persisted to a separate RINSE store passed in by
the caller.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .core import filter_noise, interpret


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


def _interpret_or_skip(trace: dict) -> dict | None:
    if not filter_noise(trace):
        return None
    return interpret(trace)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "usage: python -m rinse.bridge <input.json> <output.jsonl>",
            file=sys.stderr,
        )
        return 2
    source = JsonFileTraceSource(argv[1])
    sink = JsonLinesInterpretationSink(argv[2])
    written = bridge(source, sink, _interpret_or_skip)
    print(f"wrote {written} interpretation record(s) to {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
