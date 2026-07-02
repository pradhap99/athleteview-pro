"""Task 0.2 — event log → projection, and the structural human-confirms gate."""

from __future__ import annotations

from throughline_api.events import EventKind, append_event, list_events
from throughline_api.graph import reconstruct


def _seed_project(session, project_id="proj-1", org="org-a"):
    append_event(
        session,
        org_id=org,
        project_id=project_id,
        actor="u1",
        kind=EventKind.PROJECT_CREATED,
        payload={"title": "Test", "type": "scripted"},
    )
    append_event(
        session,
        org_id=org,
        project_id=project_id,
        actor="u1",
        kind=EventKind.SCENE_ADDED,
        payload={
            "id": "sc-1",
            "number": "1",
            "intExt": "INT",
            "location": "KITCHEN",
            "timeOfDay": "DAY",
            "heading": "INT. KITCHEN - DAY",
            "characters": ["JANE"],
        },
    )
    append_event(
        session,
        org_id=org,
        project_id=project_id,
        actor="u1",
        kind=EventKind.ELEMENT_DRAFTED,
        payload={
            "id": "el-1",
            "etype": "prop",
            "name": "revolver",
            "confidence": 0.7,
            "source": "llm",
            "sceneIds": ["sc-1"],
            "needsReview": True,
        },
    )
    session.commit()


def test_event_seq_is_monotonic_per_project(session):
    _seed_project(session)
    events = list_events(session, "proj-1")
    assert [e.seq for e in events] == [1, 2, 3]
    assert all(e.id is not None for e in events)


def test_projection_materializes_scene_and_draft(session):
    _seed_project(session)
    state = reconstruct(session, "proj-1")
    assert state.title == "Test"
    assert "sc-1" in state.scenes and state.scenes["sc-1"].location == "KITCHEN"
    el = state.elements["el-1"]
    assert el.status == "draft" and el.needs_review is True


def test_draft_is_not_auto_confirmed(session):
    """No projector path flips a draft to confirmed — only an explicit human event does."""
    _seed_project(session)
    # Replay many times: status must never drift to confirmed on its own.
    for _ in range(3):
        assert reconstruct(session, "proj-1").elements["el-1"].status == "draft"


def test_human_confirm_event_flips_status(session):
    _seed_project(session)
    append_event(
        session,
        org_id="org-a",
        project_id="proj-1",
        actor="human-user",
        kind=EventKind.ELEMENT_CONFIRMED,
        payload={"id": "el-1"},
    )
    session.commit()
    el = reconstruct(session, "proj-1").elements["el-1"]
    assert el.status == "confirmed" and el.needs_review is False


def test_reject_event_flips_status(session):
    _seed_project(session)
    append_event(
        session,
        org_id="org-a",
        project_id="proj-1",
        actor="human-user",
        kind=EventKind.ELEMENT_REJECTED,
        payload={"id": "el-1"},
    )
    session.commit()
    assert reconstruct(session, "proj-1").elements["el-1"].status == "rejected"
