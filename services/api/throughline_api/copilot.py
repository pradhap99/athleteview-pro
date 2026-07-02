"""Per-role copilot nudges (task 4.1) — deterministic core.

Each copilot watches the graph and surfaces the right nudge in the right person's
language, always citing the graph fact it derives from (explainability). This module is
the deterministic rules layer; the ml/ seam can later rephrase nudges via LLM without
changing what fires (utility AI only — analysis, never generative content).
"""

from __future__ import annotations

from typing import Any

from .budget import build_cost_report, line_from_payload
from .graph import GraphState
from .locations import company_moves
from .sides import tracking_summary


def _nudge(role: str, kind: str, message: str, ref: dict[str, Any]) -> dict[str, Any]:
    return {"role": role, "kind": kind, "message": message, "ref": ref}


def coordinator_nudges(state: GraphState) -> list[dict[str, Any]]:
    """Chase-before-call: unacknowledged call sheets and sides."""
    nudges: list[dict[str, Any]] = []
    latest_by_day: dict[int, dict[str, Any]] = {}
    for cs in state.call_sheets.values():
        day = cs["dayIndex"]
        if day not in latest_by_day or cs["revision"] > latest_by_day[day]["revision"]:
            latest_by_day[day] = cs
    for cs in latest_by_day.values():
        pending = [r["name"] for r in cs.get("recipients", []) if not r.get("acknowledgedAt")]
        if pending:
            nudges.append(
                _nudge(
                    "coordinator",
                    "callsheet_unacked",
                    f"Day {cs['dayIndex']} call sheet (rev {cs['revision']}): "
                    f"{len(pending)} recipient(s) have not acknowledged — {', '.join(sorted(pending))}",
                    {"callSheetId": cs["id"], "pending": sorted(pending)},
                )
            )
    chase = [r for r in tracking_summary(state) if r["needsChase"]]
    if chase:
        names = sorted({r["recipientName"] for r in chase})
        nudges.append(
            _nudge(
                "coordinator",
                "sides_unacked",
                f"{len(chase)} sides link(s) not acknowledged — {', '.join(names)}",
                {"linkIds": [r["linkId"] for r in chase]},
            )
        )
    return nudges


def first_ad_nudges(state: GraphState) -> list[dict[str, Any]]:
    """Board logistics: company moves coming up."""
    return [
        _nudge(
            "first_ad",
            "company_move",
            f"Company move day {m['fromDay']} → {m['toDay']}: "
            f"{m['fromLocation']} → {m['toLocation']} — plan the move order and turnaround",
            m,
        )
        for m in company_moves(state)
    ]


def line_producer_nudges(state: GraphState) -> list[dict[str, Any]]:
    """Money: accounts trending over (negative variance), worst first."""
    if not state.budget_lines:
        return []
    report = build_cost_report(
        [line_from_payload(p) for p in state.budget_lines],
        actuals=state.actuals,
        commitments=state.commitments,
        etc_overrides=state.etc_overrides,
    )
    over = sorted((r for r in report.rows if r.variance < 0), key=lambda r: r.variance)
    return [
        _nudge(
            "line_producer",
            "over_budget",
            f"Account {row.code} ({row.description or 'unnamed'}) trending over: "
            f"variance {row.variance:,.2f} (EFC {row.efc:,.2f} vs budget {row.budget:,.2f})",
            {"code": row.code, "variance": row.variance, "derivation": row.derivation},
        )
        for row in over
    ]


ROLES = {
    "coordinator": coordinator_nudges,
    "first_ad": first_ad_nudges,
    "line_producer": line_producer_nudges,
}


def nudges_for(state: GraphState, role: str) -> list[dict[str, Any]]:
    if role not in ROLES:
        raise ValueError(f"unknown copilot role {role!r} (want one of {sorted(ROLES)})")
    return ROLES[role](state)
