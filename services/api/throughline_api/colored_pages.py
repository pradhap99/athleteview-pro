"""Colored-page script revisions (task 6.1).

Industry conventions enforced here:

* **Revision color order** — White → Blue → Pink → Yellow → Green → Goldenrod → Buff →
  Salmon → Cherry → Tan, then the cycle repeats as "Double White", "Triple White", …
* **Locked pages** — once the first revision is released, scene numbering is frozen: a
  scene inserted after scene 10 becomes **10A** (then 10B…), and a scene inserted before
  the first scene becomes **A1** — existing numbers never shift.
* **Revision marks** — changed/added lines carry an asterisk in the right margin.
* **Revision slug** — each release records ``color + date`` and accumulates into the
  title-page revision history.

Revision clouds / as-broadcast export are P2 (out of scope here, per spec §7A.4).
"""

from __future__ import annotations

import difflib
import string

REVISION_COLORS = (
    "White",
    "Blue",
    "Pink",
    "Yellow",
    "Green",
    "Goldenrod",
    "Buff",
    "Salmon",
    "Cherry",
    "Tan",
)

_MARK_COLUMN = 60  # right-margin column where the asterisk lands


def color_for_index(index: int) -> str:
    """0 → White, 1 → Blue, … 9 → Tan, 10 → Double White, 20 → Triple White, …"""
    if index < 0:
        raise ValueError("revision index must be >= 0")
    cycle, position = divmod(index, len(REVISION_COLORS))
    base = REVISION_COLORS[position]
    if cycle == 0:
        return base
    if cycle == 1:
        return f"Double {base}"
    if cycle == 2:
        return f"Triple {base}"
    return f"{cycle + 1}x {base}"


def next_color(history: list[dict]) -> tuple[int, str]:
    """The (index, color) for the next release given the existing history."""
    index = len(history)
    return index, color_for_index(index)


# ---- locked pages / A-scenes --------------------------------------------------


def a_scene_number(after_number: str, existing: set[str]) -> str:
    """First free A-number for a scene inserted AFTER ``after_number`` (10 → 10A, 10B…)."""
    for letter in string.ascii_uppercase:
        candidate = f"{after_number}{letter}"
        if candidate not in existing:
            return candidate
    raise ValueError(f"exhausted A–Z suffixes after scene {after_number}")


def before_scene_number(before_number: str, existing: set[str]) -> str:
    """First free number for a scene inserted BEFORE ``before_number`` (1 → A1, B1…)."""
    for letter in string.ascii_uppercase:
        candidate = f"{letter}{before_number}"
        if candidate not in existing:
            return candidate
    raise ValueError(f"exhausted A–Z prefixes before scene {before_number}")


# ---- revision marks -----------------------------------------------------------


def revision_marks(old_lines: list[str], new_lines: list[str]) -> list[tuple[str, bool]]:
    """Pair each new line with whether it changed (gets an asterisk in the margin).

    Deterministic line diff (difflib): replaced and inserted lines are marked; unchanged
    lines are not. Deletions leave no line to mark (they surface in the scene diff).
    """
    marked: list[tuple[str, bool]] = []
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for op, _i1, _i2, j1, j2 in matcher.get_opcodes():
        for j in range(j1, j2):
            marked.append((new_lines[j], op != "equal"))
    return marked


def render_marked_page(marked: list[tuple[str, bool]]) -> str:
    """Render lines with the conventional right-margin asterisk on changed lines."""
    out = []
    for line, changed in marked:
        out.append(f"{line:<{_MARK_COLUMN}}*" if changed else line)
    return "\n".join(out)


def revision_slug(color: str, date_iso: str) -> str:
    return f"{color} Revision — {date_iso}"
