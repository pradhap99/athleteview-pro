"""Task 5.3 — hot costs: prior-day actuals from rules-engine flags (table-driven)."""

from __future__ import annotations

import datetime as dt

import pytest

from throughline_api.budget import compute_hot_costs
from throughline_api.rules import DayWork, RulesEngine
from throughline_api.rules.ratecards import RateCardLibrary


def dtime(hour: int, minute: int = 0, day: int = 10) -> dt.datetime:
    return dt.datetime(2025, 3, day, hour, minute)


@pytest.fixture
def engine() -> RulesEngine:
    return RulesEngine(RateCardLibrary.from_dir())


def test_clean_day_matches_budget(engine):
    card = engine.card_for("IATSE", "basic_agreement", "crew", dt.date(2025, 1, 1))
    # 8.5h elapsed with a half-hour meal 5h in → 8h worked, no OT, no penalties.
    work = DayWork(
        "Grip",
        dt.date(2025, 3, 10),
        dtime(8),
        dtime(16, 30),
        meal_breaks=[(dtime(13), dtime(13, 30))],
    )
    report = compute_hot_costs(
        [work],
        engine=engine,
        card=card,
        hourly_rates={"Grip": 50.0},
        budgeted={"Grip": 400.0},
    )
    line = report.lines[0]
    assert line.base == 400.0
    assert line.total == 400.0
    assert line.variance == 0.0


def test_ot_and_meal_penalty_flow_into_hot_costs(engine):
    # SAG 2024 card: OT ×1.5 after 8h worked; meal ladder [30, 40, 50].
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork(
        "Alice",
        dt.date(2025, 3, 10),
        call=dtime(7),
        wrap=dtime(17, 30),  # 10.5h elapsed
        meal_breaks=[(dtime(14), dtime(14, 30))],  # first meal 7h in → 2 penalty intervals
    )
    report = compute_hot_costs(
        [work],
        engine=engine,
        card=card,
        hourly_rates={"Alice": 100.0},
        budgeted={"Alice": 800.0},
    )
    line = report.lines[0]
    # worked = 10h → base 1000; OT: (10 − 8) × 100 × 0.5 = 100
    assert line.base == 1000.0
    assert line.ot_premium == 100.0
    # meal penalties from the 2024 table ladder: 30 + 40
    assert line.meal_penalties == 70.0
    assert line.total == 1170.0
    assert line.variance == -370.0  # over budget
    assert any("meal" in e for e in line.explanations)


def test_rest_invasion_priced_from_table(engine):
    # Teamsters rest invasion is 3× (vs IATSE 2×) — the table drives the dollars.
    card = engine.card_for("Teamsters", "local_399", "driver", dt.date(2025, 1, 1))
    work = DayWork(
        "Driver",
        dt.date(2025, 3, 10),
        call=dtime(6),
        wrap=dtime(14),
        prior_wrap=dtime(22, day=9),  # 8h rest < 10h required → 2 invaded hours
    )
    report = compute_hot_costs(
        [work],
        engine=engine,
        card=card,
        hourly_rates={"Driver": 60.0},
        budgeted={"Driver": 480.0},
    )
    line = report.lines[0]
    # invaded 2h × 60 × (3 − 1) = 240
    assert line.rest_invasion == 240.0


def test_report_totals(engine):
    card = engine.card_for("IATSE", "basic_agreement", "crew", dt.date(2025, 1, 1))
    meal = [(dtime(13), dtime(13, 30))]
    works = [
        DayWork("A", dt.date(2025, 3, 10), dtime(8), dtime(16, 30), meal_breaks=meal),
        DayWork("B", dt.date(2025, 3, 10), dtime(8), dtime(16, 30), meal_breaks=meal),
    ]
    report = compute_hot_costs(
        works,
        engine=engine,
        card=card,
        hourly_rates={"A": 50.0, "B": 40.0},
        budgeted={"A": 400.0, "B": 400.0},
    )
    assert report.total_budgeted == 800.0
    assert report.total_actual == 720.0
    assert report.total_variance == 80.0  # under budget
