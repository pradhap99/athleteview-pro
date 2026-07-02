"""Script revision → proposed graph diff (task 1.3, server side).

Re-importing a revised draft never blind-appends. The current graph scenes are compared
against the new draft (scene-number keyed, deterministic); the result becomes a
``change.proposed`` diff whose ops (add/remove/update scene) apply only on human confirm —
so a revision ripples through the graph exactly like any other change.
"""

from __future__ import annotations

import uuid

from throughline_ml.parser import ParsedScript, diff_scripts, parse_script
from throughline_ml.parser.types import IntExt, ParsedScene

from .graph import GraphState, ProposedDiffState


def state_to_parsed(state: GraphState) -> ParsedScript:
    """Rebuild a comparable ParsedScript from the graph's current scene projections."""
    script = ParsedScript(title=state.title, source_format="graph")
    for scene in state.scenes.values():
        script.scenes.append(
            ParsedScene(
                number=scene.number,
                int_ext=IntExt(scene.int_ext),
                location=scene.location,
                time_of_day=scene.time_of_day,
                heading=scene.heading,
                page_eighths=scene.page_eighths,
                characters=list(scene.characters),
            )
        )
    return script


def propose_revision(
    state: GraphState, *, diff_id: str, new_text: str, fmt: str | None = None
) -> tuple[ProposedDiffState, dict]:
    """Diff the current graph against a revised draft → a reviewable proposed change."""
    old = state_to_parsed(state)
    new = parse_script(new_text, fmt)
    script_diff = diff_scripts(old, new)

    id_by_number = {s.number: s.id for s in state.scenes.values()}
    changes: list[dict] = []

    for scene in script_diff.added:
        changes.append(
            {
                "op": "add_scene",
                "scene": {
                    "id": f"sc-{uuid.uuid4().hex[:8]}",
                    "number": scene.number,
                    "intExt": scene.int_ext.value,
                    "location": scene.location,
                    "timeOfDay": scene.time_of_day,
                    "heading": scene.heading,
                    "pageEighths": scene.page_eighths,
                    "characters": list(scene.characters),
                },
            }
        )
    for scene in script_diff.removed:
        changes.append({"op": "remove_scene", "sceneId": id_by_number[scene.number]})
    for change in script_diff.changed:
        after = change.after
        assert after is not None
        changes.append(
            {
                "op": "update_scene",
                "sceneId": id_by_number[change.number],
                "heading": after.heading,
                "intExt": after.int_ext.value,
                "location": after.location,
                "timeOfDay": after.time_of_day,
                "pageEighths": after.page_eighths,
                "characters": list(after.characters),
                "fieldsChanged": change.fields_changed,
                "charactersAdded": change.characters_added,
                "charactersRemoved": change.characters_removed,
            }
        )

    diff = ProposedDiffState(
        id=diff_id,
        summary=f"Script revision: {script_diff.summary()}",
        changes=changes,
    )
    detail = {
        "added": [s.number for s in script_diff.added],
        "removed": [s.number for s in script_diff.removed],
        "changed": [
            {
                "number": c.number,
                "fieldsChanged": c.fields_changed,
                "charactersAdded": c.characters_added,
                "charactersRemoved": c.characters_removed,
            }
            for c in script_diff.changed
        ],
    }
    return diff, detail
