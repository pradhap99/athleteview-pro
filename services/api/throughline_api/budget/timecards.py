"""Cost-coded timecard computation (task 5.5) — always against the rules engine.

A timecard is a person-day (``DayWork``) priced by the effective-dated rate card:
straight time + OT + meal penalties + rest invasion + premium days, then **split across
account codes without cent drift** (largest-remainder allocation). Recomputed from events
on every read, so a corrected call time or a changed rate card auto-recalculates — nothing
is cached stale.

Rates and split weights are data (deal memos / submissions). No rate, multiplier, or
threshold literal lives here (rate-card guard scans this package).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..rules.engine import DayWork, RateCard, RulesEngine
from .flag_pricing import day_premium, meal_penalty_amount, ot_premium, rest_invasion_premium


@dataclass
class TimecardCalc:
    person: str
    worked_hours: float
    elapsed_hours: float
    base: float
    ot_premium: float
    meal_penalties: float
    rest_invasion: float
    day_premium: float
    adjustments: float
    total: float
    split_amounts: list[dict] = field(default_factory=list)  # [{code, amount}]
    explanations: list[str] = field(default_factory=list)

    @property
    def mpv_count(self) -> int:
        """Meal-penalty-violation intervals (Exhibit G field), summed from the flags."""
        return self._mpv

    _mpv: int = 0
    forced_call: bool = False


def allocate_across_codes(total: float, splits: list[dict]) -> list[dict]:
    """Allocate ``total`` across account codes by weight, exactly (no cent drift).

    Every split gets ``round(total × share, 2)`` except the last, which takes the exact
    remainder — so the parts always sum to the whole.
    """
    if not splits:
        return []
    weight_sum = float(sum(float(s.get("weight", 1.0)) for s in splits))
    if weight_sum <= 0.0:
        raise ValueError("split weights must sum to a positive number")
    out: list[dict] = []
    allocated = 0.0
    for split in splits[:-1]:
        share = float(split.get("weight", 1.0)) / weight_sum
        amount = round(total * share, 2)
        allocated = round(allocated + amount, 2)
        out.append({"code": split["code"], "amount": amount})
    out.append({"code": splits[-1]["code"], "amount": round(total - allocated, 2)})
    return out


def compute_timecard(
    work: DayWork,
    *,
    engine: RulesEngine,
    card: RateCard,
    hourly_rate: float,
    splits: list[dict],
    adjustments: list[dict] | None = None,
) -> TimecardCalc:
    """Price one person-day against the rules engine and split it across account codes."""
    rate = float(hourly_rate)
    flags = engine.evaluate_day(work, card)
    base = round(work.worked_hours() * rate, 2)
    ot = meals = rest = premium = 0.0
    mpv = 0
    forced = False
    explanations: list[str] = []
    for flag in flags:
        if flag.kind == "overtime":
            ot += ot_premium(flag, rate)
        elif flag.kind == "meal_penalty":
            meals += meal_penalty_amount(flag)
            mpv += int(flag.computed.get("intervals", 0))
        elif flag.kind == "turnaround":
            rest += rest_invasion_premium(flag, rate)
            forced = True
        elif flag.kind in ("sixth_day", "seventh_day"):
            premium += day_premium(flag, work, rate)
        explanations.append(flag.explain())

    adj_total = round(sum(float(a.get("amount", 0.0)) for a in (adjustments or [])), 2)
    total = round(base + ot + meals + rest + premium + adj_total, 2)

    calc = TimecardCalc(
        person=work.person,
        worked_hours=round(work.worked_hours(), 2),
        elapsed_hours=round(work.elapsed_hours(), 2),
        base=base,
        ot_premium=round(ot, 2),
        meal_penalties=round(meals, 2),
        rest_invasion=round(rest, 2),
        day_premium=round(premium, 2),
        adjustments=adj_total,
        total=total,
        split_amounts=allocate_across_codes(total, splits),
        explanations=explanations,
    )
    calc._mpv = mpv
    calc.forced_call = forced
    return calc
