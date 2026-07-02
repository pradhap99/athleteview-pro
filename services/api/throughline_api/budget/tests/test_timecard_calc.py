"""Task 5.5 — timecard computation + exact account-code allocation."""

from __future__ import annotations

import datetime as dt

import pytest

from throughline_api.budget.timecards import allocate_across_codes, compute_timecard
from throughline_api.rules import DayWork, RulesEngine
from throughline_api.rules.ratecards import RateCardLibrary


def dtime(hour: int, minute: int = 0) -> dt.datetime:
    return dt.datetime(2025, 3, 10, hour, minute)


@pytest.fixture
def engine() -> RulesEngine:
    return RulesEngine(RateCardLibrary.from_dir())


def test_allocation_sums_exactly_no_cent_drift():
    # 100.00 split three equal ways: 33.33 + 33.33 + 33.34 — never 99.99.
    parts = allocate_across_codes(100.0, [{"code": "A"}, {"code": "B"}, {"code": "C"}])
    assert [p["amount"] for p in parts] == [33.33, 33.33, 33.34]
    assert round(sum(p["amount"] for p in parts), 2) == 100.0


def test_allocation_respects_weights():
    parts = allocate_across_codes(1000.0, [{"code": "A", "weight": 3}, {"code": "B", "weight": 1}])
    assert parts == [{"code": "A", "amount": 750.0}, {"code": "B", "amount": 250.0}]


def test_allocation_rejects_nonpositive_weights():
    with pytest.raises(ValueError):
        allocate_across_codes(10.0, [{"code": "A", "weight": 0}])


def test_compute_timecard_prices_from_rules_engine(engine):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork(
        "Alice",
        dt.date(2025, 3, 10),
        call=dtime(7),
        wrap=dtime(17, 30),
        meal_breaks=[(dtime(14), dtime(14, 30))],  # first meal 7h in → 2 MPV intervals
    )
    calc = compute_timecard(
        work,
        engine=engine,
        card=card,
        hourly_rate=100.0,
        splits=[{"code": "2100", "weight": 3}, {"code": "2200", "weight": 1}],
        adjustments=[{"type": "wardrobe", "amount": 15.0}],
    )
    assert calc.base == 1000.0  # 10h worked × 100
    assert calc.ot_premium == 100.0  # (10 − 8) × 100 × (1.5 − 1)
    assert calc.meal_penalties == 70.0  # 2024 ladder: 30 + 40
    assert calc.adjustments == 15.0
    assert calc.total == 1185.0
    assert calc.mpv_count == 2
    assert calc.forced_call is False
    # Splits carve the total exactly.
    assert calc.split_amounts == [
        {"code": "2100", "amount": 888.75},
        {"code": "2200", "amount": 296.25},
    ]
    assert any("meal" in e for e in calc.explanations)
