"""Deterministic page-eighths estimation.

Industry convention: a script page is divided into **eighths** (⅛-page units); a
breakdown reports each scene's length in eighths. Without true typeset pagination we
estimate from rendered line count: a standard page holds ~55 lines, so one eighth ≈
55 / 8 ≈ 6.875 lines. This is deterministic (same input → same output) and monotonic
(more content → more eighths); the eval gold set (evals/datasets/breakdown) calibrates
the constant against real paginated scripts.
"""

from __future__ import annotations

import math

LINES_PER_PAGE = 55
EIGHTHS_PER_PAGE = 8
LINES_PER_EIGHTH = LINES_PER_PAGE / EIGHTHS_PER_PAGE  # 6.875
_WRAP_COLS = 60  # approximate action-line width in a standard screenplay


def _rendered_line_count(text_lines: list[str]) -> int:
    """Count display lines, wrapping long lines at the standard column width."""
    total = 0
    for line in text_lines:
        stripped = line.rstrip()
        if not stripped:
            total += 1  # blank lines still consume vertical space
            continue
        total += max(1, math.ceil(len(stripped) / _WRAP_COLS))
    return total


def estimate_page_eighths(text_lines: list[str], *, include_heading: bool = True) -> int:
    """Estimate the number of ⅛-page units a scene occupies.

    ``text_lines`` are the scene's rendered content lines (heading excluded — it is added
    here when ``include_heading`` is true). Always ≥ 1 eighth for a non-empty scene.
    """
    lines = _rendered_line_count(text_lines)
    if include_heading:
        lines += 2  # slugline + trailing blank
    eighths = round(lines / LINES_PER_EIGHTH)
    return max(1, eighths)
