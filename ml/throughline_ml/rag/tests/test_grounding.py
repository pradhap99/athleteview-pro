"""Grounding gate tests — abstain when unfaithful; keep citations when grounded."""

from __future__ import annotations

import pytest

from throughline_ml.rag import ABSTAIN, enforce_grounding, format_context, grounded_answer
from throughline_ml.rag.pipeline import Passage


def test_format_context_is_numbered():
    passages = [Passage("a", "First fact.", "node-1"), Passage("b", "Second fact.", "node-2")]
    assert format_context(passages) == "[1] First fact.\n[2] Second fact."


def test_abstains_below_faithfulness_gate():
    result = enforce_grounding("The budget is $1.2M [1].", faithfulness=0.80)
    assert result.abstained is True
    assert result.text == ABSTAIN


def test_grounded_answer_keeps_citations():
    result = enforce_grounding("The budget is $1.2M [1], per the top sheet [3].", faithfulness=0.95)
    assert result.abstained is False
    assert result.citations == ["1", "3"]


def test_explicit_abstention_is_respected():
    result = enforce_grounding(ABSTAIN, faithfulness=0.99)
    assert result.abstained is True


def test_grounded_answer_requires_components():
    with pytest.raises(RuntimeError, match="retriever, LLM, and faithfulness grader"):
        grounded_answer("What is the budget?")
