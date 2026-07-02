"""Script ingest → graph events (bridges the deterministic parser into the event log).

Scenes are structural facts written directly (the deterministic parser owns format
fidelity). Cast elements are written as *drafts* (``element.drafted``) — they still pass
through the human-confirms gate even though they are rule-sourced.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from throughline_ml.parser import parse_script

from .events import EventKind, append_event


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def ingest_script(
    session: Session,
    *,
    org_id: str,
    project_id: str,
    actor: str,
    text: str,
    fmt: str | None = None,
) -> dict[str, object]:
    parsed = parse_script(text, fmt)

    append_event(
        session,
        org_id=org_id,
        project_id=project_id,
        actor=actor,
        kind=EventKind.SCRIPT_IMPORTED,
        payload={
            "title": parsed.title,
            "sourceFormat": parsed.source_format,
            "sceneCount": len(parsed.scenes),
        },
    )

    character_scenes: dict[str, list[str]] = {}
    for i, scene in enumerate(parsed.scenes, start=1):
        scene_id = f"sc-{i}"
        append_event(
            session,
            org_id=org_id,
            project_id=project_id,
            actor=actor,
            kind=EventKind.SCENE_ADDED,
            payload={
                "id": scene_id,
                "number": scene.number,
                "intExt": scene.int_ext.value,
                "location": scene.location,
                "timeOfDay": scene.time_of_day,
                "heading": scene.heading,
                "pageEighths": scene.page_eighths,
                "characters": list(scene.characters),
            },
        )
        for character in scene.characters:
            character_scenes.setdefault(character, []).append(scene_id)

    for name, scene_ids in character_scenes.items():
        append_event(
            session,
            org_id=org_id,
            project_id=project_id,
            actor=actor,
            kind=EventKind.ELEMENT_DRAFTED,
            payload={
                "id": f"el-cast-{_slug(name)}",
                "etype": "cast",
                "name": name,
                "confidence": 1.0,
                "source": "rule",
                "sceneIds": scene_ids,
                "needsReview": False,
            },
        )

    return {
        "sceneCount": len(parsed.scenes),
        "elementCount": len(character_scenes),
        "characters": list(character_scenes),
    }
