"""The production graph as a projection of the event log.

``fold`` replays events into a :class:`GraphState`; ``reconstruct`` folds up to a given
event id, which is exactly the Time Machine capability (``GET .../graph?at=eventId``).

"AI drafts, humans confirm" is enforced HERE, structurally: an element's ``status`` is a
pure function of the events applied to it. Only an ``element.confirmed`` event (which the
API accepts solely from a human actor via an explicit endpoint) sets ``confirmed``. No
projector, propagation step, or AI path can produce that event — so nothing is ever
auto-marked final.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .db import Event
from .events import EventKind


@dataclass
class SceneState:
    id: str
    number: str
    int_ext: str
    location: str
    time_of_day: str
    heading: str
    page_eighths: int = 1
    characters: list[str] = field(default_factory=list)


@dataclass
class ElementState:
    id: str
    etype: str
    name: str
    confidence: float
    source: str  # rule | ner | llm | human
    scene_ids: list[str] = field(default_factory=list)
    status: str = "draft"  # draft | confirmed | rejected  (only a human flips off 'draft')
    needs_review: bool = True


@dataclass
class ProposedDiffState:
    id: str
    summary: str
    changes: list[dict[str, Any]]
    status: str = "pending"  # pending | confirmed | rejected
    dollar_delta: float = 0.0
    hold_days_delta: int = 0
    location_days_delta: int = 0


@dataclass
class GraphState:
    project_id: str
    org_id: str = ""
    title: str = ""
    project_type: str = ""
    at_event_id: int | None = None
    scenes: dict[str, SceneState] = field(default_factory=dict)
    elements: dict[str, ElementState] = field(default_factory=dict)
    assignments: dict[str, int] = field(default_factory=dict)  # scene_id -> day index
    dood: dict[str, list[str]] = field(default_factory=dict)
    num_days: int = 0
    budget_lines: list[dict[str, Any]] = field(default_factory=list)
    actuals: list[dict[str, Any]] = field(default_factory=list)
    commitments: list[dict[str, Any]] = field(default_factory=list)
    etc_overrides: dict[str, float] = field(default_factory=dict)  # account code -> ETC
    proposed_diffs: dict[str, ProposedDiffState] = field(default_factory=dict)

    def confirmed_elements(self) -> list[ElementState]:
        return [e for e in self.elements.values() if e.status == "confirmed"]

    def pending_review(self) -> list[ElementState]:
        return [e for e in self.elements.values() if e.status == "draft"]


def _apply(state: GraphState, ev: Event) -> None:
    p = ev.payload
    kind = ev.kind

    if kind == EventKind.PROJECT_CREATED:
        state.org_id = ev.org_id
        state.title = p.get("title", "")
        state.project_type = p.get("type", "")

    elif kind == EventKind.SCENE_ADDED:
        state.scenes[p["id"]] = SceneState(
            id=p["id"],
            number=p.get("number", ""),
            int_ext=p.get("intExt", "INT"),
            location=p.get("location", ""),
            time_of_day=p.get("timeOfDay", ""),
            heading=p.get("heading", ""),
            page_eighths=p.get("pageEighths", 1),
            characters=list(p.get("characters", [])),
        )

    elif kind == EventKind.ELEMENT_DRAFTED:
        conf = float(p.get("confidence", 1.0))
        state.elements[p["id"]] = ElementState(
            id=p["id"],
            etype=p["etype"],
            name=p["name"],
            confidence=conf,
            source=p.get("source", "llm"),
            scene_ids=list(p.get("sceneIds", [])),
            status="draft",
            needs_review=bool(p.get("needsReview", True)),
        )

    elif kind == EventKind.ELEMENT_CONFIRMED:
        el = state.elements.get(p["id"])
        if el is not None:
            el.status = "confirmed"
            el.needs_review = False

    elif kind == EventKind.ELEMENT_REJECTED:
        el = state.elements.get(p["id"])
        if el is not None:
            el.status = "rejected"
            el.needs_review = False

    elif kind == EventKind.SCHEDULE_SET:
        state.assignments = {k: int(v) for k, v in p.get("assignments", {}).items()}
        state.dood = {k: list(v) for k, v in p.get("dood", {}).items()}
        state.num_days = int(p.get("numDays", 0))

    elif kind == EventKind.SCENE_RESCHEDULED:
        state.assignments[p["sceneId"]] = int(p["toDay"])

    elif kind == EventKind.SCENE_REMOVED:
        state.scenes.pop(p["id"], None)
        state.assignments.pop(p["id"], None)

    elif kind == EventKind.SCENE_UPDATED:
        scene = state.scenes.get(p["id"])
        if scene is not None:
            for payload_key, attr in (
                ("heading", "heading"),
                ("location", "location"),
                ("timeOfDay", "time_of_day"),
                ("intExt", "int_ext"),
                ("pageEighths", "page_eighths"),
            ):
                value = p.get(payload_key)
                if value is not None:
                    setattr(scene, attr, value)
            if p.get("characters") is not None:
                scene.characters = list(p["characters"])

    elif kind == EventKind.BUDGET_LINE_ADDED:
        state.budget_lines.append(dict(p))

    elif kind == EventKind.ACTUAL_RECORDED:
        state.actuals.append(dict(p))

    elif kind == EventKind.COMMITMENT_RECORDED:
        state.commitments.append(dict(p))

    elif kind == EventKind.ETC_SET:
        state.etc_overrides[p["code"]] = float(p["amount"])  # type: ignore[attr-defined]

    elif kind == EventKind.CHANGE_PROPOSED:
        diff_id = p.get("diffId") or p["id"]
        state.proposed_diffs[diff_id] = ProposedDiffState(
            id=diff_id,
            summary=p.get("summary", ""),
            changes=list(p.get("changes", [])),
            dollar_delta=float(p.get("dollarDelta", 0.0)),
            hold_days_delta=int(p.get("holdDaysDelta", 0)),
            location_days_delta=int(p.get("locationDaysDelta", 0)),
        )

    elif kind == EventKind.CHANGE_CONFIRMED:
        diff = state.proposed_diffs.get(p["diffId"])
        if diff is not None:
            diff.status = "confirmed"

    elif kind == EventKind.CHANGE_REJECTED:
        diff = state.proposed_diffs.get(p["diffId"])
        if diff is not None:
            diff.status = "rejected"


def fold(project_id: str, events: Iterable[Event]) -> GraphState:
    state = GraphState(project_id=project_id)
    last_id: int | None = None
    for ev in events:
        _apply(state, ev)
        last_id = ev.id
    state.at_event_id = last_id
    return state


def reconstruct(session, project_id: str, at_event_id: int | None = None) -> GraphState:
    """Materialize the graph at HEAD, or exactly as it was at ``at_event_id`` (Time Machine)."""
    from .events import list_events

    events = list_events(session, project_id, upto_id=at_event_id)
    return fold(project_id, events)
