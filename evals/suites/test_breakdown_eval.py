"""Breakdown EVAL GATE (PRODUCT_SPEC §15.1).

The live gate needs a model-serving endpoint (GLiNER + Qwen3) to produce predictions, so
it is skipped unless ``THROUGHLINE_LLM_ENDPOINT`` is set. What always runs here is the
quality firewall itself: we prove the grader ACCEPTS a perfect breakdown and REJECTS one
that drops a safety-critical element (recall gate). A firewall that never fails is useless.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from evals.graders import check_breakdown_gates, grade_breakdown

GOLDEN = Path(__file__).parents[1] / "datasets" / "breakdown" / "golden_001.json"


def _gold() -> list[tuple[str, str]]:
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    return [(e["etype"], e["name"]) for e in data["gold_elements"]]


@pytest.mark.eval
def test_perfect_breakdown_passes_gates():
    gold = _gold()
    report = grade_breakdown(gold, gold)
    passed, failures = check_breakdown_gates(report)
    assert passed, failures
    assert report.safety_recall == 1.0
    assert report.micro_f1 == 1.0


@pytest.mark.eval
def test_missing_safety_critical_element_fails_gate():
    gold = _gold()
    # Model misses the stunt (car flip) — a safety-critical miss must fail the gate.
    predictions = [e for e in gold if e != ("stunt", "car flip")]
    report = grade_breakdown(predictions, gold)
    passed, failures = check_breakdown_gates(report)
    assert not passed
    assert any("safety-critical recall" in f for f in failures)
    assert report.safety_recall < 0.95


@pytest.mark.eval
@pytest.mark.skipif(
    not os.environ.get("THROUGHLINE_LLM_ENDPOINT"),
    reason="live breakdown gate requires a model-serving endpoint (GLiNER + Qwen3)",
)
def test_live_breakdown_meets_gates():  # pragma: no cover - runs only with a model endpoint
    from throughline_ml.breakdown import run_breakdown  # noqa: PLC0415

    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    result = run_breakdown(data["script"], fmt=data["source_format"])
    predictions = [(e.etype, e.name) for e in result.elements]
    report = grade_breakdown(predictions, _gold())
    passed, failures = check_breakdown_gates(report)
    assert passed, failures
