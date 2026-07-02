"""Task 5.3 — budget lines + fringes: caps, proportional flow, derivations."""

from __future__ import annotations

import pytest

from throughline_api.budget import BudgetLine, Fringe, line_from_payload


def _wage_line(rate: float = 500.0, qty: float = 5.0) -> BudgetLine:
    return BudgetLine(
        id="bl-1",
        code="2100",
        category="btl",
        description="Key Grip",
        qty=qty,
        unit="day",
        rate=rate,
        fringes=[Fringe("P&H", 22.0), Fringe("FICA", 7.65, cap=120.0)],
    )


def test_base_and_fringe_totals():
    line = _wage_line()
    assert line.base_total == 2500.0
    # P&H 22% of 2500 = 550; FICA 7.65% = 191.25 → capped at 120.
    assert line.fringe_total == 670.0
    assert line.total == 3170.0


def test_fringe_cap_applies():
    fringe = Fringe("FICA", 7.65, cap=120.0)
    assert fringe.amount(2500.0) == 120.0
    assert "capped" in fringe.derivation(2500.0)


def test_fringes_flow_proportionally_on_wage_change():
    line = _wage_line(rate=500.0)
    repriced = line.reprice(600.0)
    # Base scales 2500 → 3000; uncapped P&H scales 550 → 660 automatically.
    assert repriced.base_total == 3000.0
    assert Fringe("P&H", 22.0).amount(repriced.base_total) == 660.0
    assert repriced.fringe_total == 780.0  # 660 + capped 120
    assert repriced.total == 3780.0


def test_derivation_expands_every_figure():
    d = _wage_line().derivation()
    assert "5.0 day × 500.00 = 2,500.00" in d
    assert "P&H: 2,500.00 × 22.0% = 550.00" in d
    assert "total = 3,170.00" in d


def test_payload_round_trip():
    line = _wage_line()
    rebuilt = line_from_payload(line.to_payload())
    assert rebuilt.total == line.total
    assert rebuilt.derivation() == line.derivation()


def test_invalid_category_rejected():
    with pytest.raises(ValueError, match="category"):
        BudgetLine(
            id="x", code="1", category="catering", description="", qty=1.0, unit="flat", rate=1.0
        )
