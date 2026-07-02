"""Breakdown orchestration tests — the human-confirms + safety-recall policy.

Uses injected NER/LLM doubles (no model endpoint) to test the real orchestration logic.
"""

from __future__ import annotations

import pytest

from throughline_ml.breakdown import Candidate, DraftElement, run_breakdown

SCRIPT = "INT. GUN SHOP - DAY\n\nMARIA examines a revolver. A stunt driver waits outside.\n"


class _StubNer:
    def tag(self, text, labels):
        return [Candidate("prop", "revolver", 0, 8, 0.4)]


class _StubLLM:
    """Returns a fixed draft set (one high-conf cast, one low-conf prop, one stunt, a dup)."""

    def reconcile(self, *, heading, scene_text, candidates, prompt):
        span = (0, 1)
        return [
            DraftElement("cast", "MARIA", 0.95, "llm", "", span),
            DraftElement("prop", "revolver", 0.40, "llm", "", span),
            DraftElement("stunt", "car flip", 0.99, "llm", "", span),
            DraftElement("cast", "maria", 0.90, "llm", "", span),  # duplicate of MARIA
        ]


def test_run_breakdown_applies_policy_and_dedupes():
    result = run_breakdown(SCRIPT, fmt="fountain", ner=_StubNer(), llm=_StubLLM())
    by_name = {(e.etype, e.name.lower()): e for e in result.elements}

    # dedupe: only one MARIA survives (the higher-confidence one)
    assert len([e for e in result.elements if e.etype == "cast"]) == 1
    assert by_name[("cast", "maria")].confidence == 0.95

    # low-confidence prop flagged for review; high-confidence cast not
    assert by_name[("prop", "revolver")].needs_review is True
    assert by_name[("cast", "maria")].needs_review is False

    # safety-critical stunt always needs review despite 0.99 confidence (recall-first)
    assert by_name[("stunt", "car flip")].needs_review is True

    # nothing is ever auto-confirmed
    assert all(e.status == "draft" for e in result.elements)


def test_run_breakdown_requires_models():
    with pytest.raises(RuntimeError, match="NER model and an LLM"):
        run_breakdown(SCRIPT, fmt="fountain")
