"""Task 5.2 (partial) — minors / child-labor hard-gate checks, per-jurisdiction."""

from __future__ import annotations

from throughline_api.rules.engine import FlagSeverity
from throughline_api.rules.minors import check_minor_day, coogan_required


def test_minor_over_work_cap_is_a_violation():
    # CA band 6_to_8: max_work_hours 4.0 → 5h scheduled is a hard violation.
    flags = check_minor_day("CA", 8, work_hours=5.0, at_place_hours=8.0)
    kinds = {f.kind for f in flags}
    assert "minor_hours" in kinds
    assert all(f.severity == FlagSeverity.VIOLATION for f in flags)


def test_jurisdiction_swap_changes_limits():
    # 8-year-old, 4.4h work: over CA cap (4.0) but within NY cap (4.5).
    ca = check_minor_day("CA", 8, work_hours=4.4, at_place_hours=6.0)
    ny = check_minor_day("NY", 8, work_hours=4.4, at_place_hours=6.0)
    assert any(f.kind == "minor_hours" for f in ca)
    assert not any(f.kind == "minor_hours" for f in ny)


def test_minor_turnaround_hard_gate():
    flags = check_minor_day("CA", 15, work_hours=4.0, at_place_hours=6.0, turnaround_hours=10.0)
    assert any(f.kind == "minor_turnaround" for f in flags)


def test_coogan_required_states():
    assert coogan_required("CA")
    assert coogan_required("NY")
    assert coogan_required("NM")
    assert not coogan_required("TX")


def test_flags_cite_jurisdiction_and_table():
    flags = check_minor_day("CA", 8, work_hours=6.0, at_place_hours=10.0)
    assert flags
    for f in flags:
        assert "CA" in f.rule_ref.cite()
        assert "minors.yaml" in f.rule_ref.cite()
