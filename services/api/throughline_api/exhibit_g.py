"""Exhibit G — the SAG-AFTRA performer time report (task 5.5).

Built as a projection over the day's timecards for performers whose deal memo is
SAG-AFTRA: report/dismiss times, meals, work-status code (W/SW/SWF/WF/H/T/TR/R/F), hours
in **tenths**, MPV count and forced-call flag (straight from the rules-engine flags),
minor flag (from the memo), wardrobe/stunt adjustments, and the performer's e-signature.
It renders to the guild-form layout and is the feed for daily hot costs — the same
DayWork records price both, so they can never disagree.
"""

from __future__ import annotations

from typing import Any

from .graph import GraphState
from .rules.engine import RulesEngine
from .timecard_service import calc_to_dict, compute_for_state

WORK_STATUS_CODES = frozenset({"W", "SW", "SWF", "WF", "H", "T", "TR", "R", "F"})
_EXHIBIT_G_UNION = "SAG-AFTRA"


def tenths(hours: float) -> float:
    """Guild convention: hours reported in tenths of an hour."""
    return round(round(hours * 10) / 10, 1)


def timecards_for_date(state: GraphState, date_iso: str) -> list[dict[str, Any]]:
    return [tc for tc in state.timecards.values() if tc.get("date") == date_iso]


def build_exhibit_g(state: GraphState, engine: RulesEngine, date_iso: str) -> list[dict[str, Any]]:
    """One row per SAG-AFTRA performer who has a timecard on the date."""
    rows: list[dict[str, Any]] = []
    for tc in sorted(timecards_for_date(state, date_iso), key=lambda t: t["person"]):
        memo = state.deal_memos.get(tc["person"])
        if memo is None or memo.get("union") != _EXHIBIT_G_UNION:
            continue
        calc = compute_for_state(state, engine, tc)
        status = tc.get("workStatusCode", "W")
        signature = state.exhibit_g_signatures.get(f"{tc['person']}:{date_iso}")
        rows.append(
            {
                "person": tc["person"],
                "legalName": memo.get("legalName", tc["person"]),
                "date": date_iso,
                "workStatusCode": status if status in WORK_STATUS_CODES else "W",
                "reportTime": tc["call"],
                "dismissTime": tc["wrap"],
                "meals": tc.get("meals", []),
                "workedTenths": tenths(calc.worked_hours),
                "elapsedTenths": tenths(calc.elapsed_hours),
                "mpvCount": calc.mpv_count,
                "forcedCall": calc.forced_call,
                "isMinor": bool(memo.get("isMinor", False)),
                "adjustments": tc.get("adjustments", []),
                "signature": signature,  # None until the performer e-signs
                "computed": calc_to_dict(calc),
            }
        )
    return rows


def render_exhibit_g_text(rows: list[dict[str, Any]], *, production: str) -> str:
    """Plain-text rendering in the guild-form column layout."""
    header = (
        f"EXHIBIT G — PERFORMER TIME REPORT · {production}\n"
        f"Date: {rows[0]['date'] if rows else '—'}\n"
        f"{'PERFORMER':<22}{'STATUS':<8}{'REPORT':<18}{'DISMISS':<18}"
        f"{'WORK(0.1h)':<12}{'MPV':<5}{'FC':<4}{'MINOR':<7}SIGNED"
    )
    lines = [header, "-" * len(header.splitlines()[-1])]
    for row in rows:
        lines.append(
            f"{row['legalName']:<22}{row['workStatusCode']:<8}{row['reportTime']:<18}"
            f"{row['dismissTime']:<18}{row['workedTenths']:<12}{row['mpvCount']:<5}"
            f"{'Y' if row['forcedCall'] else 'N':<4}{'Y' if row['isMinor'] else 'N':<7}"
            f"{'✓ ' + row['signature']['signedBy'] if row['signature'] else '—'}"
        )
    return "\n".join(lines)
