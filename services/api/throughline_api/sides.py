"""Sides + secure watermarked distribution (task 6.2).

Scripts/sides are confidential IP (guardrail): distribution is **permissioned,
watermarked per-recipient, and revocable**, and every delivery + acknowledgment is
logged. Sides generate from a shooting day's scenes in shooting order (call-sheet order
takes over when task 4.1 lands; until then, scene-number order within the day), with a
one-click character filter. The recipient's name/email is burned into **every page**.

Links are capability URLs: the token is the credential, so viewers need no paid seat —
but the link can expire, is revocable at any moment, and each open is an event.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from .graph import GraphState, SceneState


class SidesError(Exception):
    """Link invalid/expired/revoked (→ 410 at the API layer)."""


def _scene_sort_key(scene: SceneState) -> tuple:
    """Natural order for scene numbers incl. A-scenes: 1 < 1A < 2 < 10 < 10A."""
    match = re.match(r"^([A-Z]*)(\d+)([A-Z]*)$", scene.number or "")
    if not match:
        return (1, scene.number)
    prefix, digits, suffix = match.groups()
    # A-prefixed scenes (A1) sort just before their base number.
    return (0, int(digits), 0 if prefix else 1, prefix, suffix)


def scenes_for_day(state: GraphState, day_index: int) -> list[SceneState]:
    ids = [sid for sid, day in state.assignments.items() if day == day_index]
    return sorted((state.scenes[i] for i in ids if i in state.scenes), key=_scene_sort_key)


def generate_sides(
    state: GraphState, *, day_index: int, character: str | None = None
) -> list[dict[str, Any]]:
    """One half-letter page per scene, in shooting order; optionally character-filtered."""
    pages: list[dict[str, Any]] = []
    for scene in scenes_for_day(state, day_index):
        if character is not None and character not in scene.characters:
            continue
        pages.append(
            {
                "sceneId": scene.id,
                "number": scene.number,
                "heading": scene.heading,
                "body": scene.body,
                "characters": scene.characters,
                "pageEighths": scene.page_eighths,
            }
        )
    return pages


def watermark(link: dict[str, Any]) -> str:
    return (
        f"CONFIDENTIAL — {link['recipientName']} <{link['recipientEmail']}> — "
        f"link {link['id']} — do not forward"
    )


def render_sides_text(pages: list[dict[str, Any]], link: dict[str, Any]) -> str:
    """Half-letter text rendering with the personalized watermark on EVERY page."""
    mark = watermark(link)
    out: list[str] = []
    for page in pages:
        out.append(mark)
        out.append(f"SCENE {page['number']} · {page['heading']}")
        out.append("")
        if page["body"]:
            out.append(page["body"])
        out.append("")
        out.append(mark)
        out.append("=" * 48)  # page break
    return "\n".join(out)


def check_link_access(link: dict[str, Any] | None, *, now: dt.datetime) -> dict[str, Any]:
    """Validate a capability link: must exist, not be revoked, not be expired."""
    if link is None:
        raise SidesError("sides link not found")
    if link.get("revoked"):
        raise SidesError("this sides link has been revoked")
    expires = link.get("expiresAt")
    if expires:
        if dt.datetime.fromisoformat(expires) < now:
            raise SidesError("this sides link has expired")
    return link


def tracking_summary(state: GraphState) -> list[dict[str, Any]]:
    """Delivery/acknowledgment per recipient — the coordinator's chase-before-call list."""
    rows = []
    for link in state.sides_links.values():
        rows.append(
            {
                "linkId": link["id"],
                "recipientName": link["recipientName"],
                "recipientEmail": link["recipientEmail"],
                "dayIndex": link["dayIndex"],
                "character": link.get("character"),
                "revoked": bool(link.get("revoked")),
                "opened": bool(link.get("openedAt")),
                "openedAt": link.get("openedAt"),
                "acknowledged": bool(link.get("acknowledgedAt")),
                "acknowledgedAt": link.get("acknowledgedAt"),
                "needsChase": not link.get("acknowledgedAt") and not link.get("revoked"),
            }
        )
    return sorted(rows, key=lambda r: (not r["needsChase"], r["recipientName"]))
