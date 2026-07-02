"""Production-wide hybrid search + grounded Q&A (task 3.3) — seam.

Retrieval (pgvector dense + keyword hybrid) and generation are separated (Ragas-style).
The grounded answer is emitted ONLY if the faithfulness grader clears the gate (≥0.90);
otherwise it abstains ("Insufficient sources.") and routes to a human — an ungrounded
answer about a contract clause is a liability. Concrete embedder/index/LLM/grader adapters
live behind a model endpoint; the grounding + abstain policy here is real and testable.
"""

from .pipeline import (
    ABSTAIN,
    FAITHFULNESS_GATE,
    GroundedAnswer,
    Passage,
    enforce_grounding,
    format_context,
    grounded_answer,
)

__all__ = [
    "grounded_answer",
    "enforce_grounding",
    "format_context",
    "GroundedAnswer",
    "Passage",
    "ABSTAIN",
    "FAITHFULNESS_GATE",
]
