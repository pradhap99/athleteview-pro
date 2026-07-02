"""Daily hot costs — next-morning actual vs. budgeted labor for the prior shoot day.

Line producers read this first every morning. Actual labor cost is computed from the
rules engine's flags (OT tiers, meal penalties, rest invasion, premium days), so every
premium traces to a table entry — the multipliers/thresholds come from the flags
themselves (table-derived), never from this module. Hourly rates and budgeted amounts
arrive as data (deal memos / budget lines).

Currently computes the hourly-OT model (SAG/IATSE/Teamsters). The DGA day-count model
adds day-fraction pay from the rate card and is wired when task 5.5 (timecards) lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..rules.engine import DayWork, Flag, RateCard, RulesEngine


@dataclass
class HotCostLine:
    person: str
    budgeted: float
    base: float
    ot_premium: float
    meal_penalties: float
    rest_invasion: float
    day_premium: float
    total: float
    variance: float  # budgeted − total (negative = over)
    explanations: list[str] = field(default_factory=list)


@dataclass
class HotCostReport:
    lines: list[HotCostLine] = field(default_factory=list)

    @property
    def total_budgeted(self) -> float:
        return round(sum(line.budgeted for line in self.lines), 2)

    @property
    def total_actual(self) -> float:
        return round(sum(line.total for line in self.lines), 2)

    @property
    def total_variance(self) -> float:
        return round(self.total_budgeted - self.total_actual, 2)


def _ot_premium(flag: Flag, hourly_rate: float) -> float:
    """Extra dollars beyond straight time for an hourly-model OT flag.

    All parameters come from the flag: hours worked, the table threshold it crossed, and
    the multiplier — extra = (hours − threshold) × rate × (multiplier − 1).
    """
    if "multiplier" not in flag.computed:  # day-count model (DGA) — handled in task 5.5
        return 0.0
    hours = float(flag.computed["hours"])
    threshold = float(flag.rule_ref.threshold)
    multiplier = float(flag.computed["multiplier"])
    return round(max(0.0, hours - threshold) * hourly_rate * (multiplier - 1.0), 2)


def _rest_invasion(flag: Flag, hourly_rate: float) -> float:
    """Invaded rest hours are paid at the table's rest-invasion multiplier."""
    invaded = float(flag.computed["required_hours"]) - float(flag.computed["rest_hours"])
    multiplier = float(flag.computed["penalty_multiplier"])
    return round(max(0.0, invaded) * hourly_rate * (multiplier - 1.0), 2)


def _day_premium(flag: Flag, work: DayWork, hourly_rate: float) -> float:
    """6th/7th-day premium: the whole day's worked hours step up to the table multiplier."""
    multiplier = float(flag.computed["multiplier"])
    return round(work.worked_hours() * hourly_rate * (multiplier - 1.0), 2)


def compute_hot_costs(
    day_works: list[DayWork],
    *,
    engine: RulesEngine,
    card: RateCard,
    hourly_rates: dict[str, float],
    budgeted: dict[str, float],
) -> HotCostReport:
    """Compute prior-day actual labor vs. budget, per person, from rules-engine flags."""
    report = HotCostReport()
    for work in day_works:
        rate = float(hourly_rates[work.person])
        flags = engine.evaluate_day(work, card)
        base = round(work.worked_hours() * rate, 2)
        ot = meals = rest = premium = 0.0
        explanations: list[str] = []
        for flag in flags:
            if flag.kind == "overtime":
                ot += _ot_premium(flag, rate)
            elif flag.kind == "meal_penalty":
                meals += float(flag.computed["penalty_usd"])
            elif flag.kind == "turnaround":
                rest += _rest_invasion(flag, rate)
            elif flag.kind in ("sixth_day", "seventh_day"):
                premium += _day_premium(flag, work, rate)
            explanations.append(flag.explain())
        total = round(base + ot + meals + rest + premium, 2)
        budget_amount = float(budgeted.get(work.person, 0.0))
        report.lines.append(
            HotCostLine(
                person=work.person,
                budgeted=round(budget_amount, 2),
                base=base,
                ot_premium=round(ot, 2),
                meal_penalties=round(meals, 2),
                rest_invasion=round(rest, 2),
                day_premium=round(premium, 2),
                total=total,
                variance=round(budget_amount - total, 2),
                explanations=explanations,
            )
        )
    return report
