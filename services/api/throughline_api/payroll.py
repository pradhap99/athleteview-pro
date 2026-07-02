"""Payroll handoff (task 5.5) — approved timecards → a payroll-ready schema.

Exports to the employer-of-record services (Entertainment Partners / Cast & Crew /
Wrapbook) in one neutral schema: per-employee earnings lines with wage type, hours,
rate, amount, and cost code; the box/kit rental as a **separate, taxability-flagged**
line (accountable plan → non-taxable reimbursement, else taxable wages); and a union
P&H wage-base summary (the input to SAG Contributions Manager / MPIPHP reporting —
the fund rates themselves stay in the providers' tables, not our code).

Only APPROVED timecards export — the human sign-off chain is the gate (guardrail).
"""

from __future__ import annotations

from typing import Any

from .graph import GraphState
from .rules.engine import RulesEngine
from .timecard_service import compute_for_state

PROVIDERS = ("ep", "castandcrew", "wrapbook")
SCHEMA_VERSION = "1.0"


def _earnings_lines(calc_dict_pairs: list[tuple[dict[str, Any], Any]]) -> list[dict[str, Any]]:
    """Flatten (timecard, calc) pairs into typed earnings lines per cost code."""
    lines: list[dict[str, Any]] = []
    for tc, calc in calc_dict_pairs:
        premium_total = round(
            calc.ot_premium + calc.meal_penalties + calc.rest_invasion + calc.day_premium, 2
        )
        for split in calc.split_amounts:
            # Straight time and premiums allocate by the same split proportions.
            share = split["amount"] / calc.total if calc.total else 0.0
            lines.append(
                {
                    "date": tc["date"],
                    "wageType": "straight",
                    "hours": calc.worked_hours,
                    "amount": round(calc.base * share, 2),
                    "costCode": split["code"],
                }
            )
            if premium_total:
                lines.append(
                    {
                        "date": tc["date"],
                        "wageType": "premiums",  # OT + MPV + rest invasion + 6th/7th day
                        "hours": None,
                        "amount": round(premium_total * share, 2),
                        "costCode": split["code"],
                        "breakdown": {
                            "otPremium": calc.ot_premium,
                            "mealPenalties": calc.meal_penalties,
                            "restInvasion": calc.rest_invasion,
                            "dayPremium": calc.day_premium,
                        },
                    }
                )
        for adj in tc.get("adjustments", []):
            lines.append(
                {
                    "date": tc["date"],
                    "wageType": f"adjustment:{adj.get('type', 'other')}",
                    "hours": None,
                    "amount": round(float(adj.get("amount", 0.0)), 2),
                    "costCode": adj.get("code")
                    or (calc.split_amounts[0]["code"] if calc.split_amounts else ""),
                }
            )
    return lines


def build_payroll_export(
    state: GraphState,
    engine: RulesEngine,
    *,
    provider: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError(f"unknown payroll provider {provider!r} (want one of {PROVIDERS})")

    approved = [
        tc
        for tc in state.timecards.values()
        if tc.get("status") == "approved" and start_date <= tc["date"] <= end_date
    ]

    by_person: dict[str, list[dict[str, Any]]] = {}
    for tc in approved:
        by_person.setdefault(tc["person"], []).append(tc)

    employees: list[dict[str, Any]] = []
    ph_base: dict[tuple[str, str], float] = {}
    for person in sorted(by_person):
        memo = state.deal_memos.get(person, {})
        pairs = [(tc, compute_for_state(state, engine, tc)) for tc in by_person[person]]
        earnings = _earnings_lines(pairs)
        wage_total = round(sum(line["amount"] for line in earnings), 2)

        # Box/kit rental: separate, taxability-flagged line (accountable plan → non-taxable).
        box_kit = None
        if memo.get("boxKitRate"):
            days = len(pairs) if memo.get("boxKitCadence", "daily") == "daily" else 1
            box_kit = {
                "amount": round(float(memo["boxKitRate"]) * days, 2),
                "cadence": memo.get("boxKitCadence", "daily"),
                "taxable": not bool(memo.get("boxKitAccountablePlan", False)),
                "costCode": memo.get("boxKitAccountCode") or memo.get("accountCode", ""),
            }

        key = (memo.get("union", ""), memo.get("contract", ""))
        ph_base[key] = round(ph_base.get(key, 0.0) + wage_total, 2)

        employees.append(
            {
                "person": person,
                "legalName": memo.get("legalName", person),
                "union": memo.get("union", ""),
                "contract": memo.get("contract", ""),
                "startPacketComplete": _packet_complete(state, person),
                "earnings": earnings,
                "wageTotal": wage_total,
                "boxKit": box_kit,
            }
        )

    return {
        "schema": f"throughline-payroll/{SCHEMA_VERSION}",
        "provider": provider,
        "periodStart": start_date,
        "periodEnd": end_date,
        "employees": employees,
        "phWageBaseSummary": [
            {"union": union, "contract": contract, "wageBase": base}
            for (union, contract), base in sorted(ph_base.items())
        ],
        "timecardCount": len(approved),
    }


_REQUIRED_FORMS = ("w4", "i9", "directDeposit")


def _packet_complete(state: GraphState, person: str) -> bool:
    forms = state.start_packets.get(person, {}).get("forms", {})
    return all(forms.get(name) for name in _REQUIRED_FORMS)
