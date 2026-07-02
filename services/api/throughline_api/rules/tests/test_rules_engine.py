"""Task 5.1 — rules engine: effective-dated resolution + predictive, explainable flags."""

from __future__ import annotations

import datetime as dt

import pytest

from throughline_api.rules import DayWork, FlagSeverity, RulesEngine
from throughline_api.rules.ratecards import RateCardLibrary


def dtime(hour: int, minute: int = 0, day: int = 10) -> dt.datetime:
    return dt.datetime(2025, 3, day, hour, minute)


@pytest.fixture
def engine() -> RulesEngine:
    return RulesEngine(RateCardLibrary.from_dir())


# ---- effective-dated resolution --------------------------------------------


def test_effective_date_selects_correct_card(engine):
    early = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2023, 1, 1))
    late = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    assert early.effective_date == dt.date(2020, 7, 1)
    assert late.effective_date == dt.date(2024, 7, 1)
    # The 2024 MOA changed the meal-penalty ladder — proving date-driven thresholds.
    assert early.params["meal"]["penalty_ladder_usd"][0] == 25.0
    assert late.params["meal"]["penalty_ladder_usd"][0] == 30.0


def test_resolution_fails_before_first_effective_date(engine):
    with pytest.raises(LookupError):
        engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2019, 1, 1))


def test_changing_signatory_reloads_rule_set(engine):
    sag = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    iatse = engine.card_for("IATSE", "basic_agreement", "crew", dt.date(2025, 1, 1))
    # Different signatory → different turnaround requirement (12h studio vs 10h).
    assert sag.params["turnaround"]["by_context"]["studio"] == 12.0
    assert iatse.params["turnaround"]["by_context"]["studio"] == 10.0


# ---- worked vs elapsed ------------------------------------------------------


def test_worked_vs_elapsed_hours_are_distinct():
    work = DayWork(
        person="Alice",
        date=dt.date(2025, 3, 10),
        call=dtime(7),
        wrap=dtime(20),  # 13h elapsed
        meal_breaks=[(dtime(12), dtime(13))],  # 1h unpaid meal
    )
    assert work.elapsed_hours() == pytest.approx(13.0)
    assert work.meal_hours() == pytest.approx(1.0)
    assert work.worked_hours() == pytest.approx(12.0)


# ---- overtime (hourly, worked basis) ---------------------------------------


def test_overtime_hourly_tier(engine):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork("Alice", dt.date(2025, 3, 10), dtime(7), dtime(20), [(dtime(12), dtime(13))])
    ot = [f for f in engine.evaluate_day(work, card) if f.kind == "overtime"]
    assert len(ot) == 1
    # 12 worked hours → highest applicable tier is ×2.0 after 10h.
    assert ot[0].computed["multiplier"] == 2.0
    assert ot[0].computed["basis"] == "worked"
    assert ot[0].rule_ref.threshold == 10


def test_no_overtime_under_threshold(engine):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork("Bob", dt.date(2025, 3, 10), dtime(9), dtime(16))  # 7h, no meal
    assert not [f for f in engine.evaluate_day(work, card) if f.kind == "overtime"]


# ---- meal penalty (escalating ladder) --------------------------------------


def test_meal_penalty_escalates_from_table(engine):
    # 2020 card ladder = [25, 35, 50]; first meal 7h in → 1h over 6h limit = 2 intervals.
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2023, 1, 1))
    work = DayWork("Alice", dt.date(2025, 3, 10), dtime(7), dtime(20), [(dtime(14), dtime(14, 30))])
    meal = [f for f in engine.evaluate_day(work, card) if f.kind == "meal_penalty"]
    assert len(meal) == 1
    assert meal[0].severity == FlagSeverity.VIOLATION
    assert meal[0].computed["intervals"] == 2
    assert meal[0].computed["penalty_usd"] == pytest.approx(60.0)  # 25 + 35


# ---- turnaround / forced call ----------------------------------------------


def test_turnaround_violation_studio(engine):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork(
        "Alice",
        dt.date(2025, 3, 10),
        call=dtime(7, day=10),
        wrap=dtime(18, day=10),
        prior_wrap=dtime(22, day=9),  # only 9h rest before a 12h-required studio call
    )
    ta = [f for f in engine.evaluate_day(work, card) if f.kind == "turnaround"]
    assert len(ta) == 1
    assert ta[0].computed["rest_hours"] == pytest.approx(9.0)
    assert ta[0].computed["required_hours"] == 12.0
    assert ta[0].computed["penalty_multiplier"] == 2.0


def test_rest_invasion_multiplier_differs_by_union(engine):
    iatse = engine.card_for("IATSE", "basic_agreement", "crew", dt.date(2025, 1, 1))
    teamsters = engine.card_for("Teamsters", "local_399", "driver", dt.date(2025, 1, 1))
    assert iatse.params["turnaround"]["rest_invasion_multiplier"] == 2.0
    assert teamsters.params["turnaround"]["rest_invasion_multiplier"] == 3.0


# ---- premium days -----------------------------------------------------------


@pytest.mark.parametrize(
    "day_in_week,kind,mult",
    [(6, "sixth_day", 1.5), (7, "seventh_day", 2.0)],
)
def test_premium_days(engine, day_in_week, kind, mult):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork("Alice", dt.date(2025, 3, 10), dtime(8), dtime(16), day_in_week=day_in_week)
    flags = [f for f in engine.evaluate_day(work, card) if f.kind == kind]
    assert len(flags) == 1 and flags[0].computed["multiplier"] == mult


# ---- DGA day-count model (architecturally distinct) ------------------------


def test_dga_day_count_half_and_full(engine):
    card = engine.card_for("DGA", "basic_agreement", "director", dt.date(2025, 1, 1))
    half = DayWork("Dana", dt.date(2025, 3, 10), dtime(6), dtime(19))  # 13h elapsed > 12
    full = DayWork("Dana", dt.date(2025, 3, 10), dtime(6), dtime(22))  # 16h elapsed > 15
    half_ot = [f for f in engine.evaluate_day(half, card) if f.kind == "overtime"]
    full_ot = [f for f in engine.evaluate_day(full, card) if f.kind == "overtime"]
    assert half_ot[0].computed["extra"] == "half extra day"
    assert full_ot[0].computed["extra"] == "full extra day"


# ---- explainability ---------------------------------------------------------


def test_flags_cite_the_table_entry(engine):
    card = engine.card_for("SAG-AFTRA", "theatrical", "day_performer", dt.date(2025, 1, 1))
    work = DayWork("Alice", dt.date(2025, 3, 10), dtime(7), dtime(20), [(dtime(12), dtime(13))])
    flags = engine.evaluate_day(work, card)
    assert flags, "expected at least one flag"
    for f in flags:
        cite = f.rule_ref.cite()
        assert "SAG-AFTRA" in cite
        assert "2024-07-01" in cite  # effective date
        assert "sag_aftra.yaml" in cite  # source table
