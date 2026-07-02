"""Call sheets (task 4.1) — auto-populated from the graph, revision-native.

A call sheet for day N assembles: the day's scenes in shooting order, the cast working
that day (with DOOD status codes), the location's day-info block (sunrise/sunset/magic
hour, parking, basecamp, nearest 24-hr hospital — weather via the provider seam), and any
company move into the day. Publishing snapshots the content as an event; a re-publish for
the same day SUPERSEDES the prior revision and re-notifies ONLY the recipients whose own
day actually changed (their scenes or the general call). Recipients acknowledge via
capability tokens — viewers need no paid seat.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from .graph import GraphState
from .locations import company_moves, day_info
from .sides import scenes_for_day


def _location_record(state: GraphState, location_name: str) -> dict[str, Any] | None:
    wanted = location_name.strip().upper()
    for location in state.locations.values():
        if location.get("name", "").strip().upper() == wanted:
            return location
    return None


def build_call_sheet(
    state: GraphState,
    *,
    day_index: int,
    date_iso: str,
    general_call: str,
) -> dict[str, Any]:
    """Assemble the call-sheet content for a day purely from graph projections."""
    scenes = scenes_for_day(state, day_index)
    if not scenes:
        raise ValueError(f"no scenes scheduled on day {day_index}")

    cast: list[dict[str, Any]] = []
    seen: set[str] = set()
    for scene in scenes:
        for character in scene.characters:
            if character in seen:
                continue
            seen.add(character)
            codes = state.dood.get(character, [])
            cast.append(
                {
                    "character": character,
                    "doodCode": codes[day_index] if day_index < len(codes) else "W",
                    "scenes": [s.number for s in scenes if character in s.characters],
                }
            )

    primary = scenes[0].location if scenes else ""
    location = _location_record(state, primary)
    location_block = (
        day_info(location, dt.date.fromisoformat(date_iso)) if location is not None else None
    )
    move_in = next(
        (m for m in company_moves(state) if m["toDay"] == day_index),
        None,
    )

    return {
        "dayIndex": day_index,
        "date": date_iso,
        "generalCall": general_call,
        "scenes": [
            {
                "number": s.number,
                "heading": s.heading,
                "intExt": s.int_ext,
                "location": s.location,
                "timeOfDay": s.time_of_day,
                "pageEighths": s.page_eighths,
                "characters": s.characters,
            }
            for s in scenes
        ],
        "cast": cast,
        "primaryLocation": primary,
        "locationInfo": location_block,  # sun/magic hour/hospital/parking (None if unmatched)
        "companyMoveIn": move_in,
        "weather": None,  # external provider seam
    }


def personal_view(content: dict[str, Any], character: str) -> dict[str, Any]:
    """The slice of a call sheet that matters to one cast recipient (for re-notify diffs)."""
    return {
        "generalCall": content["generalCall"],
        "date": content["date"],
        "scenes": [s["number"] for s in content["scenes"] if character in s["characters"]],
    }


def affected_recipients(
    old_content: dict[str, Any], new_content: dict[str, Any], recipients: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Recipients whose personal day changed between two revisions (re-notify ONLY these).

    Crew (non-cast) recipients are affected by general-call/date changes; cast recipients
    also by changes to their own scene list.
    """
    general_changed = old_content.get("generalCall") != new_content.get(
        "generalCall"
    ) or old_content.get("date") != new_content.get("date")
    affected = []
    for recipient in recipients:
        character = recipient.get("character")
        if character:
            if general_changed or personal_view(old_content, character) != personal_view(
                new_content, character
            ):
                affected.append(recipient)
        elif general_changed:
            affected.append(recipient)
    return affected
