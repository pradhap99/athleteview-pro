"""Script revision diff (task 1.3, server side) — deterministic, scene-number keyed.

Re-importing a revised draft must never blind-append: it produces an element-level diff
(added / removed / changed scenes, with per-scene character adds/drops) that the API wraps
as a proposed change for human confirmation, rippling downstream (schedule/budget) like
any other change.

Scenes are matched by scene number — the industry-stable key (locked pages / A-scenes keep
numbers sticky across colored revisions, §7A.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import ParsedScene, ParsedScript


@dataclass
class SceneChange:
    number: str
    fields_changed: list[str] = field(default_factory=list)
    characters_added: list[str] = field(default_factory=list)
    characters_removed: list[str] = field(default_factory=list)
    before: ParsedScene | None = None
    after: ParsedScene | None = None


@dataclass
class ScriptDiff:
    added: list[ParsedScene] = field(default_factory=list)
    removed: list[ParsedScene] = field(default_factory=list)
    changed: list[SceneChange] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary(self) -> str:
        if self.is_empty:
            return "No scene-level changes."
        parts = []
        if self.added:
            parts.append(
                f"{len(self.added)} scene(s) added ({', '.join(s.number for s in self.added)})"
            )
        if self.removed:
            parts.append(
                f"{len(self.removed)} removed ({', '.join(s.number for s in self.removed)})"
            )
        if self.changed:
            parts.append(
                f"{len(self.changed)} changed ({', '.join(c.number for c in self.changed)})"
            )
        return "; ".join(parts)


_COMPARED_FIELDS = ("int_ext", "location", "time_of_day", "heading", "page_eighths")


def diff_scripts(old: ParsedScript, new: ParsedScript) -> ScriptDiff:
    """Element-level diff of two parsed drafts, keyed by scene number."""
    old_by_num = {s.number: s for s in old.scenes}
    new_by_num = {s.number: s for s in new.scenes}
    result = ScriptDiff()

    for number, scene in new_by_num.items():
        if number not in old_by_num:
            result.added.append(scene)

    for number, scene in old_by_num.items():
        if number not in new_by_num:
            result.removed.append(scene)

    for number, before in old_by_num.items():
        after = new_by_num.get(number)
        if after is None:
            continue
        change = SceneChange(number=number, before=before, after=after)
        for field_name in _COMPARED_FIELDS:
            old_val = getattr(before, field_name)
            new_val = getattr(after, field_name)
            if field_name == "int_ext":
                old_val, new_val = old_val.value, new_val.value
            if old_val != new_val:
                change.fields_changed.append(field_name)
        change.characters_added = [c for c in after.characters if c not in before.characters]
        change.characters_removed = [c for c in before.characters if c not in after.characters]
        if change.fields_changed or change.characters_added or change.characters_removed:
            result.changed.append(change)

    return result
