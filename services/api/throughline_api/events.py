"""Event kinds + append-only log helpers.

Writes always go through :func:`append_event`; nothing mutates or deletes an event. The
per-project ``seq`` is monotonic; the global ``id`` gives a total order for Time Machine.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Event


class EventKind:
    PROJECT_CREATED = "project.created"
    SCRIPT_IMPORTED = "script.imported"
    SCENE_ADDED = "scene.added"
    ELEMENT_DRAFTED = "element.drafted"  # AI/parser draft — status starts 'draft'
    ELEMENT_CONFIRMED = "element.confirmed"  # HUMAN action only — flips to 'confirmed'
    ELEMENT_REJECTED = "element.rejected"  # HUMAN action only
    SCHEDULE_SET = "schedule.set"
    SCENE_RESCHEDULED = "scene.rescheduled"
    SCENE_REMOVED = "scene.removed"
    SCENE_UPDATED = "scene.updated"
    BUDGET_LINE_ADDED = "budget_line.added"
    ACTUAL_RECORDED = "actual.recorded"  # human-entered/approved only — drafts stay out
    COMMITMENT_RECORDED = "commitment.recorded"  # approved-uninvoiced PO = committed
    ETC_SET = "etc.set"  # human judgment call — overrides the default ETC
    # Purchase orders (task 5.4): approved-uninvoiced PO = committed; invoice → actual.
    PO_CREATED = "po.created"  # draft — does NOT commit until approved
    PO_APPROVED = "po.approved"  # HUMAN action — the PO becomes a commitment
    PO_RECEIVED = "po.received"  # goods-receipt leg of the 3-way match
    PO_INVOICED = "po.invoiced"  # 3-way matched at the endpoint → actual
    PO_CANCELLED = "po.cancelled"
    # Check requests route through an ordered sign-off chain (dept head → UPM → …).
    CHECK_REQUEST_CREATED = "check_request.created"
    CHECK_REQUEST_APPROVED = "check_request.approved"
    # Petty cash: envelope model — receipts + returned cash must reconcile to the float.
    PETTY_CASH_ISSUED = "petty_cash.issued"
    PETTY_CASH_RECEIPT = "petty_cash.receipt"
    PETTY_CASH_RECONCILED = "petty_cash.reconciled"
    # Colored-page script revisions (task 6.1).
    SCRIPT_REVISION_RELEASED = "script_revision.released"
    # Timecards / start paperwork / Exhibit G (task 5.5).
    DEAL_MEMO_CREATED = "deal_memo.created"  # structured start paperwork; latest wins
    START_PACKET_UPDATED = "start_packet.updated"  # W-4/W-9/I-9/direct-deposit checklist
    TIMECARD_SUBMITTED = "timecard.submitted"
    TIMECARD_APPROVED = "timecard.approved"  # ordered chain, like check requests
    EXHIBIT_G_SIGNED = "exhibit_g.signed"  # performer e-signature per (person, date)
    CHANGE_PROPOSED = "change.proposed"  # a reviewable diff — NOT applied
    CHANGE_CONFIRMED = "change.confirmed"  # HUMAN action — applies the diff
    CHANGE_REJECTED = "change.rejected"


def append_event(
    session: Session,
    *,
    org_id: str,
    project_id: str,
    actor: str,
    kind: str,
    payload: dict[str, Any] | None = None,
) -> Event:
    last_seq = session.execute(
        select(func.max(Event.seq)).where(Event.project_id == project_id)
    ).scalar()
    event = Event(
        org_id=org_id,
        project_id=project_id,
        seq=(last_seq or 0) + 1,
        ts=dt.datetime.now(dt.UTC).replace(tzinfo=None),
        actor=actor,
        kind=kind,
        payload=payload or {},
    )
    session.add(event)
    session.flush()  # assign event.id without committing
    return event


def list_events(session: Session, project_id: str, *, upto_id: int | None = None) -> list[Event]:
    stmt = select(Event).where(Event.project_id == project_id)
    if upto_id is not None:
        stmt = stmt.where(Event.id <= upto_id)
    return list(session.execute(stmt.order_by(Event.id)).scalars())


def org_of(session: Session, project_id: str) -> str | None:
    return session.execute(
        select(Event.org_id).where(Event.project_id == project_id).order_by(Event.id).limit(1)
    ).scalar()
