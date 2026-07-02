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
    body: str = ""  # scene text — confidential IP; distributed only via watermarked sides


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
    purchase_orders: dict[str, dict[str, Any]] = field(default_factory=dict)
    check_requests: dict[str, dict[str, Any]] = field(default_factory=dict)
    petty_cash: dict[str, dict[str, Any]] = field(default_factory=dict)
    revision_history: list[dict[str, Any]] = field(default_factory=list)
    pp_start_date: str = ""  # principal-photography start — keys rate-card resolution
    deal_memos: dict[str, dict[str, Any]] = field(default_factory=dict)  # person -> memo
    start_packets: dict[str, dict[str, Any]] = field(default_factory=dict)  # person -> forms
    timecards: dict[str, dict[str, Any]] = field(default_factory=dict)
    exhibit_g_signatures: dict[str, dict[str, Any]] = field(default_factory=dict)  # person:date
    sides_links: dict[str, dict[str, Any]] = field(default_factory=dict)
    locations: dict[str, dict[str, Any]] = field(default_factory=dict)
    proposed_diffs: dict[str, ProposedDiffState] = field(default_factory=dict)

    @property
    def pages_locked(self) -> bool:
        """Scene numbering freezes once the first colored revision is released (§7A.4)."""
        return bool(self.revision_history)

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
        state.pp_start_date = p.get("ppStartDate") or ""

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
            body=p.get("body", ""),
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
                ("body", "body"),
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
        state.etc_overrides[p["code"]] = float(p["amount"])

    # -- purchase orders: approved-uninvoiced = committed; invoiced = actual --

    elif kind == EventKind.PO_CREATED:
        state.purchase_orders[p["id"]] = {**p, "status": "draft", "receivedAmount": None}

    elif kind == EventKind.PO_APPROVED:
        po = state.purchase_orders.get(p["id"])
        if po is not None:
            po["status"] = "approved"
            state.commitments.append(
                {"code": po["code"], "amount": float(po["amount"]), "poId": po["id"]}
            )

    elif kind == EventKind.PO_RECEIVED:
        po = state.purchase_orders.get(p["id"])
        if po is not None:
            po["receivedAmount"] = float(p["amount"])

    elif kind == EventKind.PO_INVOICED:
        po = state.purchase_orders.get(p["id"])
        if po is not None:
            po["status"] = "invoiced"
            po["invoiceRef"] = p.get("invoiceRef", "")
            state.commitments = [c for c in state.commitments if c.get("poId") != po["id"]]
            state.actuals.append(
                {"code": po["code"], "amount": float(p["amount"]), "poId": po["id"]}
            )

    elif kind == EventKind.PO_CANCELLED:
        po = state.purchase_orders.get(p["id"])
        if po is not None:
            po["status"] = "cancelled"
            state.commitments = [c for c in state.commitments if c.get("poId") != po["id"]]

    # -- check requests: ordered sign-off chain; actual books on completion ----

    elif kind == EventKind.CHECK_REQUEST_CREATED:
        state.check_requests[p["id"]] = {**p, "status": "pending", "approvals": []}

    elif kind == EventKind.CHECK_REQUEST_APPROVED:
        req = state.check_requests.get(p["id"])
        if req is not None:
            req["approvals"].append({"approver": p["approver"], "role": p["role"]})
            if len(req["approvals"]) >= len(req.get("chain", [])):
                req["status"] = "approved"
                state.actuals.append(
                    {
                        "code": req["code"],
                        "amount": float(req["amount"]),
                        "checkRequestId": req["id"],
                    }
                )

    # -- petty cash: envelope model ---------------------------------------------

    elif kind == EventKind.PETTY_CASH_ISSUED:
        state.petty_cash[p["id"]] = {**p, "status": "open", "receipts": []}

    elif kind == EventKind.PETTY_CASH_RECEIPT:
        envelope = state.petty_cash.get(p["envelopeId"])
        if envelope is not None:
            envelope["receipts"].append(dict(p))
            state.actuals.append(
                {
                    "code": p["code"],
                    "amount": float(p["amount"]),
                    "pettyCashId": p["envelopeId"],
                }
            )

    elif kind == EventKind.PETTY_CASH_RECONCILED:
        envelope = state.petty_cash.get(p["envelopeId"])
        if envelope is not None:
            envelope["status"] = "reconciled"
            envelope["returnedCash"] = float(p["returnedCash"])

    # -- colored-page revisions ---------------------------------------------------

    elif kind == EventKind.SCRIPT_REVISION_RELEASED:
        state.revision_history.append(dict(p))

    # -- timecards / start paperwork / Exhibit G (task 5.5) -----------------------

    elif kind == EventKind.DEAL_MEMO_CREATED:
        state.deal_memos[p["person"]] = dict(p)  # latest memo wins

    elif kind == EventKind.START_PACKET_UPDATED:
        packet = state.start_packets.setdefault(p["person"], {"person": p["person"], "forms": {}})
        packet["forms"].update(p.get("forms", {}))

    elif kind == EventKind.TIMECARD_SUBMITTED:
        state.timecards[p["id"]] = {**p, "status": "submitted", "approvals": []}

    elif kind == EventKind.TIMECARD_APPROVED:
        tc = state.timecards.get(p["id"])
        if tc is not None:
            tc["approvals"].append({"approver": p["approver"], "role": p["role"]})
            if len(tc["approvals"]) >= len(tc.get("chain", [])):
                tc["status"] = "approved"

    elif kind == EventKind.EXHIBIT_G_SIGNED:
        key = f"{p['person']}:{p['date']}"
        state.exhibit_g_signatures[key] = {
            "person": p["person"],
            "date": p["date"],
            "signedBy": p.get("signedBy", p["person"]),
            "signedAt": p.get("signedAt", ""),
        }

    # -- sides distribution (task 6.2) ---------------------------------------------

    elif kind == EventKind.SIDES_LINK_ISSUED:
        state.sides_links[p["id"]] = {
            **p,
            "revoked": False,
            "openedAt": None,
            "acknowledgedAt": None,
        }

    elif kind == EventKind.SIDES_LINK_REVOKED:
        link = state.sides_links.get(p["id"])
        if link is not None:
            link["revoked"] = True

    elif kind == EventKind.SIDES_OPENED:
        link = state.sides_links.get(p["id"])
        if link is not None and not link.get("openedAt"):
            link["openedAt"] = p.get("at", "")

    elif kind == EventKind.SIDES_ACKNOWLEDGED:
        link = state.sides_links.get(p["id"])
        if link is not None and not link.get("acknowledgedAt"):
            link["acknowledgedAt"] = p.get("at", "")

    # -- locations (task 6.3) --------------------------------------------------------

    elif kind == EventKind.LOCATION_ADDED:
        state.locations[p["id"]] = {**p, "documents": []}

    elif kind == EventKind.LOCATION_DOC_ADDED:
        location = state.locations.get(p["locationId"])
        if location is not None:
            location["documents"].append(dict(p))  # type: ignore[attr-defined]

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
