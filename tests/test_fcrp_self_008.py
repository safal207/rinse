from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "benchmarks" / "fcrp-self-008.json"
CAREER = ROOT / "rinse" / "career" / "pipeline.py"
CORE = ROOT / "rinse" / "reflection_graph.py"


def test_fcrp_self_008_identifies_repository_level_first_divergence() -> None:
    case = json.loads(CASE.read_text(encoding="utf-8"))

    assert case["caseId"] == "FCRP-SELF-008"
    assert case["divergence"]["firstMeaningfulDivergence"] == "N1"
    assert case["divergence"]["causePoint"] == "N1"
    assert case["divergence"]["selectedRefactorPoint"] == "N4"
    assert case["navigation"]["direction"] == "UP"
    assert case["expectedProtocolDecision"] == "PASS"


def test_career_depends_on_shared_reflection_contract() -> None:
    career = CAREER.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")

    assert "from rinse.reflection_graph import create_reflection_record" in career
    assert "build_career_reflection_records" in career
    assert '"reflection_records": reflection_records' in career
    assert '"interpretation_authority": "rinse.reflection-record.v0.2"' in career
    assert '"domain_projection_only": True' in career
    assert '"reflection_record_id": record["id"]' in career
    assert 'SCHEMA = "rinse.reflection-record.v0.2"' in core
    assert '"execution_allowed": False' in core
    assert '"classification": "REFLECTION_ONLY"' in core
