"""Task 0.2 — Time Machine: reconstruct the graph exactly as of any past event id."""

from __future__ import annotations

from throughline_api.events import EventKind, append_event
from throughline_api.graph import reconstruct


def test_reconstruct_at_past_event(session):
    org, pid = "org-a", "proj-tm"
    append_event(
        session,
        org_id=org,
        project_id=pid,
        actor="u1",
        kind=EventKind.PROJECT_CREATED,
        payload={"title": "TM", "type": "scripted"},
    )
    append_event(
        session,
        org_id=org,
        project_id=pid,
        actor="u1",
        kind=EventKind.ELEMENT_DRAFTED,
        payload={
            "id": "el-1",
            "etype": "cast",
            "name": "JANE",
            "confidence": 1.0,
            "source": "rule",
            "sceneIds": [],
            "needsReview": False,
        },
    )
    session.commit()

    # Capture the event id at the moment the element is still a draft.
    before_confirm = reconstruct(session, pid)
    draft_head = before_confirm.at_event_id
    assert before_confirm.elements["el-1"].status == "draft"

    # Later, a human confirms it.
    append_event(
        session,
        org_id=org,
        project_id=pid,
        actor="human",
        kind=EventKind.ELEMENT_CONFIRMED,
        payload={"id": "el-1"},
    )
    session.commit()

    # HEAD shows confirmed; rewinding to draft_head shows the historical draft state.
    assert reconstruct(session, pid).elements["el-1"].status == "confirmed"
    assert reconstruct(session, pid, at_event_id=draft_head).elements["el-1"].status == "draft"


def test_reconstruct_ignores_future_events(session):
    org, pid = "org-a", "proj-tm2"
    e1 = append_event(
        session,
        org_id=org,
        project_id=pid,
        actor="u1",
        kind=EventKind.PROJECT_CREATED,
        payload={"title": "A", "type": "scripted"},
    )
    session.commit()
    early_id = e1.id
    append_event(
        session,
        org_id=org,
        project_id=pid,
        actor="u1",
        kind=EventKind.SCENE_ADDED,
        payload={
            "id": "sc-1",
            "number": "1",
            "intExt": "INT",
            "location": "X",
            "timeOfDay": "DAY",
            "heading": "INT. X - DAY",
            "characters": [],
        },
    )
    session.commit()

    # As of the project-created event, the later scene must not exist.
    past = reconstruct(session, pid, at_event_id=early_id)
    assert past.scenes == {}
    assert reconstruct(session, pid).scenes  # but it exists at HEAD
