"""Compatibility wrapper for the importable RINSE core package."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rinse.core import (  # noqa: E402,F401
    detect_signals,
    extract_causal_links,
    filter_noise,
    interpret,
    main,
    run,
    score_clarity,
    suggest_next_step,
    synthesize_insight,
    tag_emotions,
)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
