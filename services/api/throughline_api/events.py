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
    BUDGET_LINE_ADDED = "budget_line.added"
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
