"""Breakdown orchestration + model protocols.

The orchestration (candidate → reconcile → provenance → dedupe → draft) is real and
testable with injected doubles. Concrete GLiNER/Qwen3 adapters require a model endpoint
and the ``[ai]`` extra; ``run_breakdown`` raises a clear error if none is wired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..parser import parse_script
from ..parser.types import SAFETY_CRITICAL

LOW_CONFIDENCE = 0.6
NER_LABELS = (
    "character",
    "prop",
    "wardrobe",
    "location",
    "vehicle",
    "special effect",
    "visual effect",
    "stunt",
    "animal",
    "sound",
    "set dressing",
)
PROMPTS_DIR = Path(__file__).parents[2] / "prompts"


@dataclass(frozen=True)
class Candidate:
    etype: str
    name: str
    start: int
    end: int
    score: float


@dataclass
class DraftElement:
    etype: str
    name: str
    confidence: float
    source: str  # ner | llm
    scene_id: str
    source_span: tuple[int, int]
    needs_review: bool = True
    status: str = "draft"  # never anything else out of the agent — humans confirm


@dataclass
class BreakdownResult:
    elements: list[DraftElement] = field(default_factory=list)

    def by_type(self, etype: str) -> list[DraftElement]:
        return [e for e in self.elements if e.etype == etype]


class NerModel(Protocol):
    def tag(self, text: str, labels: tuple[str, ...]) -> list[Candidate]: ...


class LLMReconciler(Protocol):
    def reconcile(
        self, *, heading: str, scene_text: str, candidates: list[Candidate], prompt: str
    ) -> list[DraftElement]: ...


def load_prompt(name: str = "breakdown_v1.md") -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _finalize(elements: list[DraftElement]) -> list[DraftElement]:
    """Apply the human-confirms + safety-recall policy, then dedupe by (etype, name)."""
    seen: dict[tuple[str, str], DraftElement] = {}
    for el in elements:
        # Policy fully determines review: safety-critical is always recall-first (review),
        # everything else needs review iff below the confidence threshold.
        el.needs_review = el.etype in SAFETY_CRITICAL or el.confidence < LOW_CONFIDENCE
        el.status = "draft"  # structural guarantee: the agent never emits 'confirmed'
        key = (el.etype, el.name.lower())
        if key not in seen or el.confidence > seen[key].confidence:
            seen[key] = el
    return list(seen.values())


def run_breakdown(
    script_text: str,
    fmt: str | None = None,
    *,
    ner: NerModel | None = None,
    llm: LLMReconciler | None = None,
) -> BreakdownResult:
    """Draft a breakdown for a script. Requires injected NER + LLM (or a wired endpoint)."""
    if ner is None or llm is None:
        raise RuntimeError(
            "run_breakdown needs a NER model and an LLM reconciler. Install the '[ai]' "
            "extra and wire a vLLM/SGLang endpoint, or inject test doubles. See "
            "ml/throughline_ml/breakdown/agent.py and PRODUCT_SPEC §12."
        )
    parsed = parse_script(script_text, fmt)
    prompt = load_prompt()
    drafts: list[DraftElement] = []
    for i, scene in enumerate(parsed.scenes, start=1):
        scene_id = f"sc-{i}"
        candidates = ner.tag(scene.body or scene.heading, NER_LABELS)
        for el in llm.reconcile(
            heading=scene.heading, scene_text=scene.body, candidates=candidates, prompt=prompt
        ):
            el.scene_id = scene_id
            drafts.append(el)
    return BreakdownResult(elements=_finalize(drafts))
