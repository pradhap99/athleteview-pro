"""Task 2.3 (AICP half) — bid-form export/import round-trip fixtures."""

from __future__ import annotations

import pytest

from throughline_api.budget import BudgetLine, Fringe
from throughline_api.interop import from_aicp, to_aicp, to_aicp_csv


def _lines() -> list[BudgetLine]:
    return [
        BudgetLine(
            id="bl-1",
            code="A-01",
            category="btl",
            description="Line producer (prep/wrap)",
            qty=10.0,
            unit="day",
            rate=850.0,
            fringes=[Fringe("P&H", 22.0)],
            aicp_section="A",
        ),
        BudgetLine(
            id="bl-2",
            code="B-05",
            category="btl",
            description="Director of photography",
            qty=3.0,
            unit="day",
            rate=1_200.0,
            aicp_section="B",
        ),
        BudgetLine(
            id="bl-3",
            code="T-01",
            category="other",
            description="Production fee",
            qty=1.0,
            unit="flat",
            rate=15_000.0,
            aicp_section="T",
        ),
        BudgetLine(
            id="bl-4",
            code="9000",
            category="other",
            description="No section assigned",
            qty=1.0,
            unit="flat",
            rate=100.0,
        ),
    ]


def test_export_groups_by_section_with_subtotals():
    doc = to_aicp(_lines(), title="Spot: Q3 launch")
    by_letter = {s["section"]: s for s in doc["sections"]}
    assert by_letter["A"]["title"] == "Pre-production & wrap crew labor"
    # A: 10×850 = 8500 + 22% P&H (1870) = 10370
    assert by_letter["A"]["subtotal"] == 10_370.0
    assert by_letter["B"]["subtotal"] == 3_600.0
    assert by_letter["T"]["subtotal"] == 15_000.0
    assert doc["grandTotal"] == pytest.approx(10_370.0 + 3_600.0 + 15_000.0 + 100.0)


def test_round_trip_lossless_on_core_fields():
    original = _lines()
    reimported = from_aicp(to_aicp(original))
    assert len(reimported) == len(original)
    orig_by_id = {line.id: line for line in original}
    for line in reimported:
        src = orig_by_id[line.id]
        assert (line.code, line.description, line.qty, line.unit, line.rate) == (
            src.code,
            src.description,
            src.qty,
            src.unit,
            src.rate,
        )
        assert line.category == src.category
        assert line.total == src.total
        assert [(f.name, f.rate_pct, f.cap) for f in line.fringes] == [
            (f.name, f.rate_pct, f.cap) for f in src.fringes
        ]


def test_unsectioned_lines_are_never_dropped():
    reimported = from_aicp(to_aicp(_lines()))
    assert any(line.id == "bl-4" for line in reimported)


def test_rejects_non_aicp_document():
    with pytest.raises(ValueError, match="not an AICP bid"):
        from_aicp({"format": "mmb"})


def test_csv_contains_lines_and_totals():
    text = to_aicp_csv(_lines())
    assert "Director of photography" in text
    assert "GRAND TOTAL" in text
    assert "P&H 22.0%" in text
