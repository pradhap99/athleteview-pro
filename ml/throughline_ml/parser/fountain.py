"""Fountain (plain-text screenplay) parser → ParsedScript.

Implements the subset of the Fountain spec needed for a breakdown: title page keys,
scene headings (incl. forced ``.`` headings and ``#n#`` scene numbers), and character
cues (for cast elements). Deterministic; no AI.
"""

from __future__ import annotations

import re

from .pageeighths import estimate_page_eighths
from .slugline import is_slugline, parse_slugline
from .types import IntExt, ParsedElement, ParsedScene, ParsedScript

_SCENE_NUMBER = re.compile(r"\s*#([\w.\-]+)#\s*$")
_TITLE_KEY = re.compile(r"^(?P<key>[A-Za-z ]+):\s*(?P<val>.*)$")
_CHAR_EXTENSION = re.compile(r"\s*\(.*?\)\s*$")  # (V.O.), (CONT'D), (O.S.)
_TRANSITIONS = ("CUT TO:", "FADE OUT", "FADE IN", "DISSOLVE TO:", "SMASH CUT")


def _is_forced_heading(line: str) -> bool:
    return line.startswith(".") and not line.startswith("..")


def _is_character_cue(line: str, prev_blank: bool, next_nonblank: bool) -> bool:
    """A character cue is an uppercase line between a blank line and dialogue."""
    text = line.strip()
    if not text or not prev_blank or not next_nonblank:
        return False
    if text.startswith("@"):  # forced character
        return True
    if text.endswith(tuple(t[-1] for t in _TRANSITIONS)) and any(
        text.startswith(t.split()[0]) for t in _TRANSITIONS
    ):
        return False
    core = _CHAR_EXTENSION.sub("", text)
    if not core or not any(ch.isalpha() for ch in core):
        return False
    # Must be all-caps (letters), allowing digits/punct; exclude transitions.
    letters = [ch for ch in core if ch.isalpha()]
    return bool(letters) and all(ch.isupper() for ch in letters) and not core.endswith("TO:")


def _character_name(line: str) -> str:
    text = line.strip().lstrip("@")
    return _CHAR_EXTENSION.sub("", text).strip().rstrip(":").strip()


def parse_fountain(text: str) -> ParsedScript:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    script = ParsedScript(source_format="fountain")

    # --- title page: leading "Key: value" block terminated by a blank line ---
    idx = 0
    if lines and _TITLE_KEY.match(lines[0]) and ":" in lines[0]:
        while idx < len(lines) and lines[idx].strip():
            m = _TITLE_KEY.match(lines[idx])
            if m and m.group("key").strip().lower() == "title":
                script.title = m.group("val").strip()
            idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1

    body_lines: list[str] = []
    current: ParsedScene | None = None
    auto_number = 0

    def flush(scene: ParsedScene | None, body: list[str]) -> None:
        if scene is None:
            return
        scene.body = "\n".join(body).strip()
        scene.page_eighths = estimate_page_eighths(body)

    content = lines[idx:]
    for i, raw in enumerate(content):
        line = raw.rstrip()
        forced = _is_forced_heading(line)
        heading_text = line[1:].strip() if forced else line

        if forced or is_slugline(line):
            flush(current, body_lines)
            body_lines = []
            num_m = _SCENE_NUMBER.search(heading_text)
            explicit_number = num_m.group(1) if num_m else None
            clean_heading = _SCENE_NUMBER.sub("", heading_text).strip()
            number, int_ext, location, tod = parse_slugline(clean_heading)
            auto_number += 1
            current = ParsedScene(
                number=explicit_number or number or str(auto_number),
                int_ext=int_ext if isinstance(int_ext, IntExt) else IntExt.INT,
                location=location,
                time_of_day=tod,
                heading=clean_heading,
            )
            script.scenes.append(current)
            continue

        if current is not None:
            prev_blank = i == 0 or not content[i - 1].strip()
            next_nonblank = i + 1 < len(content) and bool(content[i + 1].strip())
            if line.strip() and _is_character_cue(line, prev_blank, next_nonblank):
                name = _character_name(line)
                if name and name not in current.characters:
                    current.characters.append(name)
                    current.elements.append(ParsedElement("cast", name, 1.0, "rule"))
            body_lines.append(raw)

    flush(current, body_lines)
    return script
