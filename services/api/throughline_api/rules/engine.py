"""The rules engine: worked-vs-elapsed hours + predictive, explainable compliance flags.

No rate/multiplier/hour-threshold literal appears here — every such value is read from a
resolved :class:`RateCard` (see ``tables/*.yaml``). The only numeric literals are
structural/unit constants (minutes per hour, calendar positions), whitelisted by
``scripts/check_no_hardcoded_rates.py``.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .ratecards import RateCard, RateCardLibrary, RuleRef, default_library

_MIN_PER_HOUR = 60
_SECS_PER_HOUR = 60 * 60
_SIXTH_DAY = 6
_SEVENTH_DAY = 7


class FlagSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"


@dataclass(frozen=True)
class Flag:
    kind: str  # overtime | meal_penalty | turnaround | sixth_day | seventh_day
    severity: FlagSeverity
    message: str
    rule_ref: RuleRef
    computed: dict[str, Any] = field(default_factory=dict)

    def explain(self) -> str:
        return f"[{self.severity.value}] {self.message} — {self.rule_ref.cite()}"


@dataclass
class DayWork:
    """One person's planned or actual work for one day.

    'worked' vs 'elapsed' hours are tracked distinctly (this reconciles most cross-union
    rules): elapsed is wall-clock (call → wrap); worked excludes unpaid meal periods.
    """

    person: str
    date: dt.date
    call: dt.datetime
    wrap: dt.datetime
    meal_breaks: list[tuple[dt.datetime, dt.datetime]] = field(default_factory=list)
    location_context: str = "studio"  # studio | studio_zone | nearby | distant_overnight
    day_in_week: int = 1  # 1..7 — which working day of the week this is
    prior_wrap: dt.datetime | None = None  # previous day's wrap, for turnaround

    def elapsed_hours(self) -> float:
        return (self.wrap - self.call).total_seconds() / _SECS_PER_HOUR

    def meal_hours(self) -> float:
        return sum((e - s).total_seconds() for s, e in self.meal_breaks) / _SECS_PER_HOUR

    def worked_hours(self) -> float:
        return self.elapsed_hours() - self.meal_hours()

    def hours_before_first_meal(self) -> float | None:
        if not self.meal_breaks:
            return None
        first = min(s for s, _ in self.meal_breaks)
        return (first - self.call).total_seconds() / _SECS_PER_HOUR


class RulesEngine:
    def __init__(self, library: RateCardLibrary | None = None) -> None:
        self.library = library or default_library()

    def card_for(self, union: str, contract: str, tier: str, pp_start_date: dt.date) -> RateCard:
        return self.library.resolve(union, contract, tier, pp_start_date)

    def evaluate_day(self, work: DayWork, card: RateCard) -> list[Flag]:
        """Predictive evaluation of a planned day against a resolved rate card."""
        flags: list[Flag] = []
        flags.extend(self._overtime(work, card))
        flags.extend(self._meal_penalty(work, card))
        flags.extend(self._turnaround(work, card))
        flags.extend(self._premium_day(work, card))
        return flags

    # -- individual rules -----------------------------------------------------

    def _overtime(self, work: DayWork, card: RateCard) -> list[Flag]:
        ot = card.params["overtime"]
        hours = work.worked_hours() if ot["basis"] == "worked" else work.elapsed_hours()

        if ot["model"] == "day_count":
            half = ot["extra_half_day_after_hours"]
            full = ot["extra_full_day_after_hours"]
            if hours > full:
                key, thr, extra = "overtime.extra_full_day_after_hours", full, "full extra day"
            elif hours > half:
                key, thr, extra = "overtime.extra_half_day_after_hours", half, "half extra day"
            else:
                return []
            return [
                Flag(
                    kind="overtime",
                    severity=FlagSeverity.WARNING,
                    message=(
                        f"{work.person} works {hours:.1f}h ({ot['basis']}) → {extra} "
                        f"(day-count model, threshold {thr}h)"
                    ),
                    rule_ref=card.ref(key, thr),
                    computed={"hours": round(hours, 2), "basis": ot["basis"], "extra": extra},
                )
            ]

        applicable = None
        for tier in ot["tiers"]:
            if hours > tier["after_hours"]:
                applicable = tier
        if applicable is None:
            return []
        return [
            Flag(
                kind="overtime",
                severity=FlagSeverity.WARNING,
                message=(
                    f"{work.person} works {hours:.1f}h ({ot['basis']}) → overtime "
                    f"×{applicable['multiplier']} after {applicable['after_hours']}h"
                ),
                rule_ref=card.ref("overtime.after_hours", applicable["after_hours"]),
                computed={
                    "hours": round(hours, 2),
                    "basis": ot["basis"],
                    "multiplier": applicable["multiplier"],
                },
            )
        ]

    def _meal_penalty(self, work: DayWork, card: RateCard) -> list[Flag]:
        meal = card.params["meal"]
        threshold = meal["first_meal_within_hours"]
        offset = work.hours_before_first_meal()
        if offset is None:
            offset = work.elapsed_hours()  # never broke for a meal
        if offset <= threshold:
            return []

        over_minutes = (offset - threshold) * _MIN_PER_HOUR
        intervals = math.ceil(over_minutes / meal["interval_minutes"])
        ladder = meal["penalty_ladder_usd"]
        penalty = sum(ladder[min(i, len(ladder) - 1)] for i in range(intervals))
        return [
            Flag(
                kind="meal_penalty",
                severity=FlagSeverity.VIOLATION,
                message=(
                    f"{work.person}: first meal at {offset:.1f}h exceeds the "
                    f"{threshold:.1f}h limit → {intervals} penalty interval(s), ${penalty:.2f}"
                ),
                rule_ref=card.ref("meal.first_meal_within_hours", threshold),
                computed={
                    "first_meal_hours": round(offset, 2),
                    "intervals": intervals,
                    "penalty_usd": round(penalty, 2),
                },
            )
        ]

    def _turnaround(self, work: DayWork, card: RateCard) -> list[Flag]:
        if work.prior_wrap is None:
            return []
        ta = card.params["turnaround"]
        required = ta["by_context"][work.location_context]
        rest = (work.call - work.prior_wrap).total_seconds() / _SECS_PER_HOUR
        if rest >= required:
            return []
        mult = ta["rest_invasion_multiplier"]
        return [
            Flag(
                kind="turnaround",
                severity=FlagSeverity.VIOLATION,
                message=(
                    f"{work.person}: only {rest:.1f}h turnaround (< {required:.1f}h required "
                    f"for {work.location_context}) → forced call, rest-invasion ×{mult}"
                ),
                rule_ref=card.ref(f"turnaround.by_context.{work.location_context}", required),
                computed={
                    "rest_hours": round(rest, 2),
                    "required_hours": required,
                    "penalty_multiplier": mult,
                },
            )
        ]

    def _premium_day(self, work: DayWork, card: RateCard) -> list[Flag]:
        pd = card.params["premium_days"]
        if work.day_in_week >= _SEVENTH_DAY:
            key, kind, mult = (
                "premium_days.seventh_day_multiplier",
                "seventh_day",
                pd["seventh_day_multiplier"],
            )
        elif work.day_in_week >= _SIXTH_DAY:
            key, kind, mult = (
                "premium_days.sixth_day_multiplier",
                "sixth_day",
                pd["sixth_day_multiplier"],
            )
        else:
            return []
        return [
            Flag(
                kind=kind,
                severity=FlagSeverity.WARNING,
                message=(
                    f"{work.person}: day {work.day_in_week} of the work week → premium ×{mult}"
                ),
                rule_ref=card.ref(key, mult),
                computed={"day_in_week": work.day_in_week, "multiplier": mult},
            )
        ]
