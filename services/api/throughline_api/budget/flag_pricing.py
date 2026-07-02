"""Pricing rules-engine flags into dollars — shared by hot costs and timecards.

Every parameter comes from the flag itself (hours, table threshold, table multiplier) or
from data (hourly rate) — never from this module. The hourly-OT model covers
SAG/IATSE/Teamsters; the DGA day-count model adds day-fraction pay from the rate card and
returns 0.0 here (wired when day-rate data lands with task 5.5's DGA memos).
"""

from __future__ import annotations

from ..rules.engine import DayWork, Flag


def ot_premium(flag: Flag, hourly_rate: float) -> float:
    """Extra dollars beyond straight time: (hours − threshold) × rate × (multiplier − 1)."""
    if "multiplier" not in flag.computed:  # day-count model (DGA)
        return 0.0
    hours = float(flag.computed["hours"])
    threshold = float(flag.rule_ref.threshold)
    multiplier = float(flag.computed["multiplier"])
    return round(max(0.0, hours - threshold) * hourly_rate * (multiplier - 1.0), 2)


def meal_penalty_amount(flag: Flag) -> float:
    """The escalating-ladder dollars the engine already computed from the table."""
    return round(float(flag.computed["penalty_usd"]), 2)


def rest_invasion_premium(flag: Flag, hourly_rate: float) -> float:
    """Invaded rest hours paid at the table's rest-invasion multiplier."""
    invaded = float(flag.computed["required_hours"]) - float(flag.computed["rest_hours"])
    multiplier = float(flag.computed["penalty_multiplier"])
    return round(max(0.0, invaded) * hourly_rate * (multiplier - 1.0), 2)


def day_premium(flag: Flag, work: DayWork, hourly_rate: float) -> float:
    """6th/7th-day premium: the whole day's worked hours step up to the table multiplier."""
    multiplier = float(flag.computed["multiplier"])
    return round(work.worked_hours() * hourly_rate * (multiplier - 1.0), 2)
