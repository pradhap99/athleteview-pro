"""Minors / child-labor checks (task 5.2, partial) — per-jurisdiction, table-driven.

Non-compliance here is legal/criminal exposure, so it is a hard gate: a minor scheduled
past a jurisdictional cap yields a VIOLATION flag, not a warning. Age-band hours, hard
caps, and Coogan/blocked-trust requirements are read from ``tables/minors.yaml`` — nothing
is hard-coded. CA and NY diverge materially, which the table encodes.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import yaml

from .engine import Flag, FlagSeverity
from .ratecards import RuleRef

_MINORS_FILE = Path(__file__).parent / "tables" / "minors.yaml"


def load_minor_rules(path: str | Path = _MINORS_FILE) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def coogan_required(jurisdiction: str, rules: dict[str, Any] | None = None) -> bool:
    rules = rules or load_minor_rules()
    return jurisdiction in rules.get("coogan_states", [])


def _find_age_band(bands: list[dict[str, Any]], age_years: float) -> dict[str, Any] | None:
    for band in bands:
        if "min_years" in band and "max_years" in band:
            if band["min_years"] <= age_years < band["max_years"]:
                return band
    return None


def _ref(jurisdiction: str, band_label: str, rule_key: str, threshold: Any) -> RuleRef:
    return RuleRef(
        union="CHILD-LABOR",
        contract=jurisdiction,
        tier=band_label,
        effective_date=dt.date.min,
        rule_key=rule_key,
        threshold=threshold,
        source_file="minors.yaml",
    )


def check_minor_day(
    jurisdiction: str,
    age_years: float,
    *,
    work_hours: float,
    at_place_hours: float,
    turnaround_hours: float | None = None,
    rules: dict[str, Any] | None = None,
) -> list[Flag]:
    """Flag any breach of a minor's jurisdictional caps for a planned day."""
    rules = rules or load_minor_rules()
    juris = rules.get("jurisdictions", {}).get(jurisdiction)
    if juris is None:
        raise LookupError(f"no minor rules for jurisdiction {jurisdiction!r}")

    band = _find_age_band(juris["age_bands"], age_years)
    flags: list[Flag] = []
    if band is None:
        return flags

    if work_hours > band["max_work_hours"]:
        flags.append(
            Flag(
                kind="minor_hours",
                severity=FlagSeverity.VIOLATION,
                message=(
                    f"Minor ({age_years:.0f}y, {jurisdiction}) scheduled {work_hours:.1f}h "
                    f"work > cap {band['max_work_hours']}h (band {band['label']})"
                ),
                rule_ref=_ref(
                    jurisdiction, band["label"], "max_work_hours", band["max_work_hours"]
                ),
                computed={"work_hours": work_hours, "cap": band["max_work_hours"]},
            )
        )
    if at_place_hours > band["max_at_place_hours"]:
        flags.append(
            Flag(
                kind="minor_at_place",
                severity=FlagSeverity.VIOLATION,
                message=(
                    f"Minor ({age_years:.0f}y, {jurisdiction}) at place of work "
                    f"{at_place_hours:.1f}h > cap {band['max_at_place_hours']}h"
                ),
                rule_ref=_ref(
                    jurisdiction, band["label"], "max_at_place_hours", band["max_at_place_hours"]
                ),
                computed={"at_place_hours": at_place_hours, "cap": band["max_at_place_hours"]},
            )
        )
    required_turn = juris.get("max_turnaround_hours")
    if (
        turnaround_hours is not None
        and required_turn is not None
        and turnaround_hours < required_turn
    ):
        flags.append(
            Flag(
                kind="minor_turnaround",
                severity=FlagSeverity.VIOLATION,
                message=(
                    f"Minor ({jurisdiction}) turnaround {turnaround_hours:.1f}h < required "
                    f"{required_turn}h (no exceptions)"
                ),
                rule_ref=_ref(jurisdiction, "all", "max_turnaround_hours", required_turn),
                computed={"turnaround_hours": turnaround_hours, "required": required_turn},
            )
        )
    return flags
