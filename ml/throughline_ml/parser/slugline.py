"""Slugline (scene heading) parsing — shared by the Fountain and FDX parsers."""

from __future__ import annotations

import re

from .types import IntExt

# Leading scene number, e.g. "1", "10A", "101" before the INT/EXT token.
_LEADING_NUMBER = re.compile(r"^\s*(?P<num>\d+[A-Z]?)[.)\s]+")

# INT / EXT / INT-EXT variants at the start of the heading.
_PREFIX = re.compile(
    r"^\s*(?P<pfx>INT\.?/EXT\.?|EXT\.?/INT\.?|I/E\.?|INT\.?|EXT\.?)\s+",
    re.IGNORECASE,
)

_TOD_SEP = re.compile(r"\s[-–—]\s")  # " - ", " – ", " — "


def _normalize_prefix(raw: str) -> IntExt:
    p = raw.upper().replace(".", "").replace(" ", "")
    if p in {"INT/EXT", "EXT/INT", "I/E"}:
        return IntExt.INT_EXT
    if p == "EXT":
        return IntExt.EXT
    return IntExt.INT


def is_slugline(line: str) -> bool:
    """True if a line reads as a scene heading (with or without a leading number)."""
    candidate = _LEADING_NUMBER.sub("", line)
    return bool(_PREFIX.match(candidate))


def parse_slugline(line: str) -> tuple[str | None, IntExt, str, str]:
    """Parse a heading into (scene_number | None, int_ext, location, time_of_day)."""
    num_match = _LEADING_NUMBER.match(line)
    number = num_match.group("num") if num_match else None
    rest = _LEADING_NUMBER.sub("", line, count=1) if num_match else line

    pfx_match = _PREFIX.match(rest)
    if not pfx_match:
        # Not a conventional slug; treat the whole thing as the location.
        return number, IntExt.INT, rest.strip().rstrip(".").upper(), ""

    int_ext = _normalize_prefix(pfx_match.group("pfx"))
    remainder = rest[pfx_match.end() :].strip()

    parts = _TOD_SEP.split(remainder)
    if len(parts) >= 2:
        time_of_day = parts[-1].strip().upper()
        location = " - ".join(p.strip() for p in parts[:-1]).upper()
    else:
        location = remainder.upper()
        time_of_day = ""
    return number, int_ext, location.strip(), time_of_day.strip()
