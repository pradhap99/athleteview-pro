"""AI Breakdown Agent (task 1.2) — seam.

Pipeline: deterministic parse → zero-shot NER candidates (GLiNER v2.1 + spaCy) → LLM
reconcile (Qwen3, XGrammar-constrained JSON) → typed elements, each a DRAFT with
confidence + source span. Safety-critical types are tuned for recall. The concrete NER /
LLM adapters live behind a model-serving endpoint (``[ai]`` extra + vLLM/SGLang); the
orchestration, provenance, and human-confirms wiring here are real and unit-testable with
injected components. Nothing is auto-confirmed — every element enters the graph as a draft.
"""

from .agent import (
    BreakdownResult,
    Candidate,
    DraftElement,
    LLMReconciler,
    NerModel,
    run_breakdown,
)

__all__ = [
    "run_breakdown",
    "BreakdownResult",
    "Candidate",
    "DraftElement",
    "NerModel",
    "LLMReconciler",
]
