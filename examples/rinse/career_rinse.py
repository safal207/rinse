"""Run Career RINSE against a JSON file containing a `traces` array."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rinse.career import run_career_rinse


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("usage: python examples/rinse/career_rinse.py <input.json>", file=sys.stderr)
        return 2

    payload = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    traces = payload.get("traces")
    if not isinstance(traces, list):
        print("input must contain a traces array", file=sys.stderr)
        return 2

    result = run_career_rinse(traces)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
