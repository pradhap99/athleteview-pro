"""Task 5.3 — cost report: the fixed EFC/variance formula + rollup + reconciliation."""

from __future__ import annotations

from throughline_api.budget import BudgetLine, build_cost_report


def _lines() -> list[BudgetLine]:
    return [
        BudgetLine(
            id="bl-1",
            code="1100",
            category="atl",
            description="Director",
            qty=1.0,
            unit="flat",
            rate=50_000.0,
        ),
        BudgetLine(
            id="bl-2",
            code="2100",
            category="btl",
            description="Key Grip",
            qty=10.0,
            unit="day",
            rate=500.0,
        ),
        BudgetLine(
            id="bl-3",
            code="2100",
            category="btl",
            description="Key Grip OT allow",
            qty=1.0,
            unit="allow",
            rate=1_000.0,
        ),
        BudgetLine(
            id="bl-4",
            code="5100",
            category="post",
            description="Editor",
            qty=4.0,
            unit="week",
            rate=3_000.0,
        ),
    ]


def test_efc_and_variance_formula():
    report = build_cost_report(
        _lines(),
        actuals=[{"code": "2100", "amount": 2_400.0}],
        commitments=[{"code": "2100", "amount": 1_500.0}],
        etc_overrides={"2100": 3_000.0},
    )
    row = report.row("2100")
    assert row.budget == 6_000.0  # 5000 + 1000 (two lines share the account)
    # EFC = Actuals + Committed + ETC = 2400 + 1500 + 3000
    assert row.efc == 6_900.0
    # Variance = Budget − EFC = 6000 − 6900 → over by 900
    assert row.variance == -900.0
    assert "EFC = actuals 2,400.00 + committed 1,500.00 + ETC 3,000.00" in row.derivation


def test_default_etc_is_remaining_budget():
    report = build_cost_report(_lines(), actuals=[{"code": "5100", "amount": 4_000.0}])
    row = report.row("5100")
    # ETC defaults to budget − actuals − committed = 12000 − 4000 → EFC = budget.
    assert row.etc == 8_000.0
    assert row.efc == 12_000.0
    assert row.variance == 0.0


def test_category_rollup_and_totals():
    report = build_cost_report(_lines())
    assert report.by_category["atl"]["budget"] == 50_000.0
    assert report.by_category["btl"]["budget"] == 6_000.0
    assert report.by_category["post"]["budget"] == 12_000.0
    assert report.totals["budget"] == 68_000.0
    # With no actuals/commitments, EFC reconciles to budget and variance is zero.
    assert report.totals["efc"] == 68_000.0
    assert report.totals["variance"] == 0.0


def test_actuals_on_unbudgeted_code_surface():
    """An actual hitting an account with no budget line must still appear (over budget)."""
    report = build_cost_report(_lines(), actuals=[{"code": "9999", "amount": 750.0}])
    row = report.row("9999")
    assert row.budget == 0.0
    assert row.efc == 750.0
    assert row.variance == -750.0
