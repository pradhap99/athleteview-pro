"""DOOD derivation unit tests."""

from __future__ import annotations

from throughline_ml.scheduler.dood import derive_dood, hold_days


def test_start_hold_finish():
    dood = derive_dood({"A": {0, 2}}, num_days=4)
    assert dood["A"] == ["SW", "H", "WF", ""]
    assert hold_days(dood) == 1


def test_single_day_is_swf():
    dood = derive_dood({"B": {1}}, num_days=3)
    assert dood["B"] == ["", "SWF", ""]
    assert hold_days(dood) == 0


def test_no_workdays_is_all_blank():
    dood = derive_dood({"C": set()}, num_days=2)
    assert dood["C"] == ["", ""]


def test_contiguous_run_has_no_holds():
    dood = derive_dood({"D": {0, 1, 2}}, num_days=3)
    assert dood["D"] == ["SW", "W", "WF"]
    assert hold_days(dood) == 0
