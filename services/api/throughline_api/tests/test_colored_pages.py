"""Task 6.1 — color order, A-scene numbering, revision marks."""

from __future__ import annotations

import pytest

from throughline_api.colored_pages import (
    a_scene_number,
    before_scene_number,
    color_for_index,
    render_marked_page,
    revision_marks,
    revision_slug,
)


def test_standard_color_order():
    assert [color_for_index(i) for i in range(4)] == ["White", "Blue", "Pink", "Yellow"]
    assert color_for_index(9) == "Tan"


def test_color_order_wraps_to_double_and_triple():
    assert color_for_index(10) == "Double White"
    assert color_for_index(11) == "Double Blue"
    assert color_for_index(20) == "Triple White"
    assert color_for_index(30) == "4x White"


def test_negative_index_rejected():
    with pytest.raises(ValueError):
        color_for_index(-1)


def test_a_scene_numbering_and_collisions():
    assert a_scene_number("10", {"10", "11"}) == "10A"
    assert a_scene_number("10", {"10", "10A", "11"}) == "10B"
    assert before_scene_number("1", {"1", "2"}) == "A1"
    assert before_scene_number("1", {"1", "A1"}) == "B1"


def test_revision_marks_only_changed_lines():
    old = ["JANE pours coffee.", "She sits.", "The phone rings."]
    new = ["JANE pours coffee.", "She stands, restless.", "The phone rings.", "She ignores it."]
    marked = revision_marks(old, new)
    assert marked == [
        ("JANE pours coffee.", False),
        ("She stands, restless.", True),
        ("The phone rings.", False),
        ("She ignores it.", True),
    ]
    rendered = render_marked_page(marked)
    lines = rendered.split("\n")
    assert lines[0] == "JANE pours coffee."  # unchanged: no asterisk
    assert lines[1].endswith("*") and lines[3].endswith("*")


def test_revision_slug():
    assert revision_slug("Blue", "2026-07-02") == "Blue Revision — 2026-07-02"
