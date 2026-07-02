"""Grounded Q&A orchestration + the faithfulness/abstain gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

FAITHFULNESS_GATE = 0.90
ABSTAIN = "Insufficient sources."
PROMPTS_DIR = Path(__file__).parents[2] / "prompts"


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    source_node: str  # graph node this came from (for click-to-source provenance)
    score: float = 0.0


@dataclass
class GroundedAnswer:
    text: str
    citations: list[str] = field(default_factory=list)
    faithfulness: float = 0.0
    abstained: bool = False


class Retriever(Protocol):
    def search(self, query: str, *, k: int) -> list[Passage]: ...


class LLM(Protocol):
    def answer(self, *, prompt: str) -> str: ...


class FaithfulnessGrader(Protocol):
    def score(self, *, answer: str, passages: list[Passage]) -> float: ...


def format_context(passages: list[Passage]) -> str:
    return "\n".join(f"[{i}] {p.text}" for i, p in enumerate(passages, start=1))


def load_prompt(name: str = "rag_answer_v1.md") -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def enforce_grounding(answer: str, faithfulness: float) -> GroundedAnswer:
    """Apply the faithfulness gate: below threshold (or already abstaining) → abstain."""
    if answer.strip() == ABSTAIN or faithfulness < FAITHFULNESS_GATE:
        return GroundedAnswer(text=ABSTAIN, citations=[], faithfulness=faithfulness, abstained=True)
    citations = _extract_citations(answer)
    return GroundedAnswer(text=answer, citations=citations, faithfulness=faithfulness)


def _extract_citations(answer: str) -> list[str]:
    import re

    return sorted(set(re.findall(r"\[(\d+)\]", answer)))


def grounded_answer(
    question: str,
    *,
    retriever: Retriever | None = None,
    llm: LLM | None = None,
    grader: FaithfulnessGrader | None = None,
    k: int = 6,
) -> GroundedAnswer:
    """Retrieve, answer only from context, and gate on faithfulness (else abstain)."""
    if retriever is None or llm is None or grader is None:
        raise RuntimeError(
            "grounded_answer needs a retriever, LLM, and faithfulness grader. Wire a "
            "pgvector index + vLLM/SGLang + Granite Guardian (see PRODUCT_SPEC §12), or "
            "inject test doubles."
        )
    passages = retriever.search(question, k=k)
    if not passages:
        return GroundedAnswer(text=ABSTAIN, abstained=True)
    prompt = (
        load_prompt()
        .replace("{{question}}", question)
        .replace("{{numbered_context}}", format_context(passages))
    )
    raw = llm.answer(prompt=prompt)
    faithfulness = grader.score(answer=raw, passages=passages)
    return enforce_grounding(raw, faithfulness)
