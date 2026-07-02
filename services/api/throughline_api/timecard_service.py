"""Glue between timecard events, deal memos, and the rules engine (task 5.5).

Deal memos are the single source of rates and union affiliation; the rate card resolves
from union × contract × tier × the project's PP start date (falling back to the timecard
date if the project has none). Computation happens on read — auto-recalc by construction.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from .budget.timecards import TimecardCalc, compute_timecard
from .graph import GraphState
from .rules.engine import DayWork, RateCard, RulesEngine


class TimecardError(Exception):
    """Invalid timecard input (→ 409/422 at the API layer)."""


def _parse_dt(value: str, field_name: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise TimecardError(f"invalid {field_name}: {value!r} (want ISO datetime)") from exc


def daywork_from_timecard(tc: dict[str, Any]) -> DayWork:
    meals = [
        (_parse_dt(m["start"], "meal.start"), _parse_dt(m["end"], "meal.end"))
        for m in tc.get("meals", [])
    ]
    prior_wrap = tc.get("priorWrap")
    return DayWork(
        person=tc["person"],
        date=dt.date.fromisoformat(tc["date"]),
        call=_parse_dt(tc["call"], "call"),
        wrap=_parse_dt(tc["wrap"], "wrap"),
        meal_breaks=meals,
        location_context=tc.get("locationContext", "studio"),
        day_in_week=int(tc.get("dayInWeek", 1)),
        prior_wrap=_parse_dt(prior_wrap, "priorWrap") if prior_wrap else None,
    )


def memo_for(state: GraphState, person: str) -> dict[str, Any]:
    memo = state.deal_memos.get(person)
    if memo is None:
        raise TimecardError(f"no deal memo on file for {person!r} — create one first")
    return memo


def resolve_card(
    engine: RulesEngine, state: GraphState, memo: dict[str, Any], tc_date: str
) -> RateCard:
    effective = state.pp_start_date or tc_date
    return engine.card_for(
        memo["union"], memo["contract"], memo["tier"], dt.date.fromisoformat(effective)
    )


def compute_for_state(state: GraphState, engine: RulesEngine, tc: dict[str, Any]) -> TimecardCalc:
    """Price a stored timecard payload against the current memo + rate card."""
    memo = memo_for(state, tc["person"])
    card = resolve_card(engine, state, memo, tc["date"])
    splits = tc.get("splits") or [{"code": memo.get("accountCode", ""), "weight": 1.0}]
    return compute_timecard(
        daywork_from_timecard(tc),
        engine=engine,
        card=card,
        hourly_rate=float(memo["hourlyRate"]),
        splits=splits,
        adjustments=tc.get("adjustments"),
    )


def calc_to_dict(calc: TimecardCalc) -> dict[str, Any]:
    return {
        "person": calc.person,
        "workedHours": calc.worked_hours,
        "elapsedHours": calc.elapsed_hours,
        "base": calc.base,
        "otPremium": calc.ot_premium,
        "mealPenalties": calc.meal_penalties,
        "restInvasion": calc.rest_invasion,
        "dayPremium": calc.day_premium,
        "adjustments": calc.adjustments,
        "total": calc.total,
        "splits": calc.split_amounts,
        "mpvCount": calc.mpv_count,
        "forcedCall": calc.forced_call,
        "explanations": calc.explanations,
    }
