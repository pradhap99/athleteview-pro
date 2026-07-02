"""Reactive propagation — the "change once, review the ripple" engine (task 2.2).

A change never writes silently. It produces a **proposed diff**: the downstream
consequences (cast hold-day delta, company-move delta, $ delta) computed against the
current graph, for a human to accept or reject. Accepting appends the effect events;
rejecting records the rejection. Ripple math reuses the ML scheduler's DOOD derivation so
the schedule board and the propagation preview never disagree.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from throughline_ml.scheduler.dood import derive_dood, hold_days

from .events import EventKind, append_event
from .graph import GraphState, ProposedDiffState


def _cast_workdays(state: GraphState, assignments: dict[str, int]) -> dict[str, set[int]]:
    workdays: dict[str, set[int]] = {}
    for scene_id, day in assignments.items():
        scene = state.scenes.get(scene_id)
        if scene is None:
            continue
        for character in scene.characters:
            workdays.setdefault(character, set()).add(day)
    return workdays


def _metrics(state: GraphState, assignments: dict[str, int]) -> tuple[int, int]:
    """(total hold days, distinct location-days) for an assignment map."""
    if not assignments:
        return 0, 0
    num_days = max(assignments.values()) + 1
    dood = derive_dood(_cast_workdays(state, assignments), num_days)
    holds = hold_days(dood)
    location_days = len(
        {(state.scenes[s].location, d) for s, d in assignments.items() if s in state.scenes}
    )
    return holds, location_days


def propose_reschedule(
    state: GraphState, *, diff_id: str, scene_id: str, to_day: int
) -> ProposedDiffState:
    """Preview moving a scene to a new day — the deltas shown before drop (ripple preview)."""
    if scene_id not in state.scenes:
        raise KeyError(f"unknown scene {scene_id}")
    before = dict(state.assignments)
    after = dict(before)
    from_day = before.get(scene_id)
    after[scene_id] = to_day

    holds_before, loc_before = _metrics(state, before)
    holds_after, loc_after = _metrics(state, after)
    scene = state.scenes[scene_id]

    return ProposedDiffState(
        id=diff_id,
        summary=(
            f"Move scene {scene.number} ({scene.location}) "
            f"from day {from_day} to day {to_day}: "
            f"{holds_after - holds_before:+d} hold days, "
            f"{loc_after - loc_before:+d} location-days"
        ),
        changes=[{"op": "reschedule_scene", "sceneId": scene_id, "toDay": to_day}],
        hold_days_delta=holds_after - holds_before,
        location_days_delta=loc_after - loc_before,
        dollar_delta=0.0,  # populated from budget-line drivers once task 2.3 lands
    )


def propose_schedule(
    state: GraphState,
    *,
    diff_id: str,
    assignments: dict[str, int],
    dood: dict[str, list[str]],
    num_days: int,
) -> ProposedDiffState:
    """Wrap a solver result as a proposed re-board (never applied without confirmation)."""
    holds, location_days = _metrics(state, assignments)
    return ProposedDiffState(
        id=diff_id,
        summary=f"Optimized board: {num_days} days, {holds} hold days, {location_days} location-days",
        changes=[
            {
                "op": "set_schedule",
                "assignments": assignments,
                "dood": dood,
                "numDays": num_days,
            }
        ],
        hold_days_delta=holds,
        location_days_delta=location_days,
    )


def apply_change(
    session: Session,
    *,
    org_id: str,
    project_id: str,
    actor: str,
    diff: ProposedDiffState,
) -> list[int]:
    """Append the effect events for a confirmed diff, then the confirmation marker.

    ``actor`` must be a human user id — confirmation is a human action (guardrail). Returns
    the ids of the appended events.
    """
    ids: list[int] = []
    for change in diff.changes:
        op = change["op"]
        if op == "reschedule_scene":
            ev = append_event(
                session,
                org_id=org_id,
                project_id=project_id,
                actor=actor,
                kind=EventKind.SCENE_RESCHEDULED,
                payload={"sceneId": change["sceneId"], "toDay": change["toDay"]},
            )
        elif op == "set_schedule":
            ev = append_event(
                session,
                org_id=org_id,
                project_id=project_id,
                actor=actor,
                kind=EventKind.SCHEDULE_SET,
                payload={
                    "assignments": change["assignments"],
                    "dood": change["dood"],
                    "numDays": change["numDays"],
                },
            )
        else:  # pragma: no cover - guarded by proposer
            raise ValueError(f"unknown change op {op!r}")
        ids.append(ev.id)

    marker = append_event(
        session,
        org_id=org_id,
        project_id=project_id,
        actor=actor,
        kind=EventKind.CHANGE_CONFIRMED,
        payload={"diffId": diff.id},
    )
    ids.append(marker.id)
    return ids


def reject_change(
    session: Session, *, org_id: str, project_id: str, actor: str, diff_id: str
) -> int:
    ev = append_event(
        session,
        org_id=org_id,
        project_id=project_id,
        actor=actor,
        kind=EventKind.CHANGE_REJECTED,
        payload={"diffId": diff_id},
    )
    return ev.id


def diff_to_dict(diff: ProposedDiffState) -> dict[str, Any]:
    return {
        "id": diff.id,
        "summary": diff.summary,
        "status": diff.status,
        "changes": diff.changes,
        "dollarDelta": diff.dollar_delta,
        "holdDaysDelta": diff.hold_days_delta,
        "locationDaysDelta": diff.location_days_delta,
    }
