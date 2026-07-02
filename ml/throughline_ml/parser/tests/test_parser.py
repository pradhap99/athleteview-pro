"""Task 1.1 — deterministic parser tests (golden fixtures + FDX round-trip)."""

from __future__ import annotations

from pathlib import Path

import pytest

from throughline_ml.parser import parse_fdx, parse_fountain, parse_script, to_fdx
from throughline_ml.parser.pageeighths import estimate_page_eighths
from throughline_ml.parser.slugline import parse_slugline
from throughline_ml.parser.types import IntExt

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fountain_text() -> str:
    return (FIXTURES / "sample.fountain").read_text(encoding="utf-8")


@pytest.fixture
def fdx_text() -> str:
    return (FIXTURES / "sample.fdx").read_text(encoding="utf-8")


# ---- slugline parsing -------------------------------------------------------


@pytest.mark.parametrize(
    "line,expected",
    [
        ("INT. KITCHEN - DAY", (IntExt.INT, "KITCHEN", "DAY")),
        ("EXT. CITY STREET - DOWNTOWN - NIGHT", (IntExt.EXT, "CITY STREET - DOWNTOWN", "NIGHT")),
        ("INT./EXT. CAR - MOVING - NIGHT", (IntExt.INT_EXT, "CAR - MOVING", "NIGHT")),
        ("I/E. BOAT - DUSK", (IntExt.INT_EXT, "BOAT", "DUSK")),
        ("INT. WAREHOUSE", (IntExt.INT, "WAREHOUSE", "")),
    ],
)
def test_parse_slugline(line, expected):
    _num, int_ext, location, tod = parse_slugline(line)
    assert (int_ext, location, tod) == expected


def test_slugline_leading_number():
    number, int_ext, location, tod = parse_slugline("10A  INT. LOFT - DAY")
    assert number == "10A"
    assert (int_ext, location, tod) == (IntExt.INT, "LOFT", "DAY")


# ---- Fountain ---------------------------------------------------------------


def test_fountain_scenes_and_headings(fountain_text):
    script = parse_fountain(fountain_text)
    assert script.title == "The Long Way Home"
    assert len(script.scenes) == 3

    s1, s2, s3 = script.scenes
    assert (s1.int_ext, s1.location, s1.time_of_day) == (IntExt.INT, "KITCHEN", "DAY")
    assert (s2.int_ext, s2.location, s2.time_of_day) == (
        IntExt.EXT,
        "CITY STREET - DOWNTOWN",
        "NIGHT",
    )
    assert s3.int_ext == IntExt.INT_EXT and s3.location == "CAR - MOVING"


def test_fountain_characters_dedup_and_extensions(fountain_text):
    script = parse_fountain(fountain_text)
    s1, s2, _ = script.scenes
    # JANE and JOHN (from JOHN (V.O.)); extensions stripped; deduped.
    assert s1.characters == ["JANE", "JOHN"]
    # (CONT'D) collapses to the same character, not a new one.
    assert s2.characters == ["JANE"]
    assert script.characters() == ["JANE", "JOHN"]


def test_fountain_emits_cast_elements_only(fountain_text):
    script = parse_fountain(fountain_text)
    for scene in script.scenes:
        assert all(e.etype == "cast" and e.source == "rule" for e in scene.elements)


def test_action_line_is_not_a_character():
    # "JANE stands..." is mixed case → not a cue; only the JANE cue counts.
    script = parse_fountain("INT. ROOM - DAY\n\nJANE waves at BOB.\n\nJANE\nHi.\n")
    assert script.scenes[0].characters == ["JANE"]


# ---- FDX --------------------------------------------------------------------


def test_fdx_parse(fdx_text):
    script = parse_fdx(fdx_text)
    assert len(script.scenes) == 2
    s1, s2 = script.scenes
    assert s1.number == "1" and s1.int_ext == IntExt.INT and s1.location == "OFFICE"
    assert s2.number == "2" and s2.int_ext == IntExt.EXT and s2.location == "ROOFTOP"
    assert s1.characters == ["MARIA"]
    # (O.S.) extension stripped; MARIA appears once despite two cues in the scene.
    assert s2.characters == ["SAM", "MARIA"]


def test_fdx_round_trip_lossless_on_core_fields(fdx_text):
    original = parse_fdx(fdx_text)
    exported = to_fdx(original)
    reparsed = parse_fdx(exported)
    assert [s.core_key() for s in reparsed.scenes] == [s.core_key() for s in original.scenes]


def test_fountain_round_trips_through_fdx(fountain_text):
    script = parse_fountain(fountain_text)
    reparsed = parse_fdx(to_fdx(script))
    assert [s.core_key() for s in reparsed.scenes] == [s.core_key() for s in script.scenes]


# ---- dispatch + page eighths ------------------------------------------------


def test_parse_script_infers_format(fdx_text, fountain_text):
    assert parse_script(fdx_text).source_format == "fdx"
    assert parse_script(fountain_text).source_format == "fountain"


def test_parse_script_from_path(tmp_path, fountain_text):
    p = tmp_path / "s.fountain"
    p.write_text(fountain_text, encoding="utf-8")
    assert len(parse_script(str(p)).scenes) == 3


def test_page_eighths_monotonic_and_min_one():
    assert estimate_page_eighths([]) == 1
    short = estimate_page_eighths(["A short line."])
    long = estimate_page_eighths(["A much longer line of action. " * 8] * 20)
    assert short == 1
    assert long > short
