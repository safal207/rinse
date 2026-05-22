"""Compatibility wrapper for the importable RINSE bridge package."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rinse.bridge import (  # noqa: E402,F401
    InterpretationSink,
    JsonFileTraceSource,
    JsonLinesInterpretationSink,
    TraceSource,
    bridge,
    main,
)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
