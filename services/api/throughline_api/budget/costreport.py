"""Weekly cost report — the artifact studios/financiers/bond companies read.

Per account: Approved Budget · Actuals (cost-to-date) · Committed (open POs) · ETC · EFC ·
Variance. **The math is fixed (guardrail): EFC = Actuals + Committed + ETC;
Variance = Budget − EFC.** ETC defaults to ``max(0, Budget − Actuals − Committed)``
(on-budget assumption) unless a human sets an override — an override is a judgment call,
so it arrives as data (an ``etc.set`` event), never a computation here. Rolls up
ATL → BTL → Post → Other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import BudgetLine

_CATEGORY_ORDER = ("atl", "btl", "post", "other")


@dataclass
class AccountRow:
    code: str
    category: str
    description: str
    budget: float
    actuals: float
    committed: float
    etc: float
    efc: float
    variance: float
    derivation: str


@dataclass
class CostReport:
    rows: list[AccountRow] = field(default_factory=list)
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    totals: dict[str, float] = field(default_factory=dict)

    def row(self, code: str) -> AccountRow:
        for r in self.rows:
            if r.code == code:
                return r
        raise KeyError(code)


def _sum_by_code(entries: list[dict[str, Any]], code_key: str = "code") -> dict[str, float]:
    out: dict[str, float] = {}
    for e in entries:
        out[e[code_key]] = out.get(e[code_key], 0.0) + float(e.get("amount", 0.0))
    return out


def build_cost_report(
    lines: list[BudgetLine],
    *,
    actuals: list[dict[str, Any]] | None = None,
    commitments: list[dict[str, Any]] | None = None,
    etc_overrides: dict[str, float] | None = None,
) -> CostReport:
    """Build the report from budget lines + actual/commitment entries (all data-driven).

    ``actuals`` / ``commitments`` entries are ``{"code": ..., "amount": ...}`` dicts (the
    shape of ``actual.recorded`` / ``commitment.recorded`` event payloads). Only APPROVED
    actuals should be passed in — drafts stay out of the report (human-confirms gate).
    """
    actual_by_code = _sum_by_code(actuals or [])
    committed_by_code = _sum_by_code(commitments or [])
    etc_overrides = etc_overrides or {}

    # Aggregate budget per account code (multiple lines can share a code).
    budget_by_code: dict[str, float] = {}
    meta_by_code: dict[str, tuple[str, str]] = {}
    for line in lines:
        budget_by_code[line.code] = round(budget_by_code.get(line.code, 0.0) + line.total, 2)
        meta_by_code.setdefault(line.code, (line.category, line.description))

    report = CostReport()
    all_codes = sorted(set(budget_by_code) | set(actual_by_code) | set(committed_by_code))
    for code in all_codes:
        category, description = meta_by_code.get(code, ("other", ""))
        budget = budget_by_code.get(code, 0.0)
        acts = round(actual_by_code.get(code, 0.0), 2)
        comm = round(committed_by_code.get(code, 0.0), 2)
        if code in etc_overrides:
            etc = round(float(etc_overrides[code]), 2)
            etc_src = "set by human"
        else:
            etc = round(max(0.0, budget - acts - comm), 2)
            etc_src = "default: max(0, budget − actuals − committed)"
        efc = round(acts + comm + etc, 2)
        variance = round(budget - efc, 2)
        report.rows.append(
            AccountRow(
                code=code,
                category=category,
                description=description,
                budget=budget,
                actuals=acts,
                committed=comm,
                etc=etc,
                efc=efc,
                variance=variance,
                derivation=(
                    f"EFC = actuals {acts:,.2f} + committed {comm:,.2f} + ETC {etc:,.2f} "
                    f"({etc_src}) = {efc:,.2f}; variance = budget {budget:,.2f} − EFC "
                    f"{efc:,.2f} = {variance:,.2f}"
                ),
            )
        )

    for cat in _CATEGORY_ORDER:
        cat_rows = [r for r in report.rows if r.category == cat]
        if not cat_rows:
            continue
        report.by_category[cat] = {
            "budget": round(sum(r.budget for r in cat_rows), 2),
            "actuals": round(sum(r.actuals for r in cat_rows), 2),
            "committed": round(sum(r.committed for r in cat_rows), 2),
            "etc": round(sum(r.etc for r in cat_rows), 2),
            "efc": round(sum(r.efc for r in cat_rows), 2),
            "variance": round(sum(r.variance for r in cat_rows), 2),
        }

    report.totals = {
        key: round(sum(r.__dict__[key] for r in report.rows), 2)
        for key in ("budget", "actuals", "committed", "etc", "efc", "variance")
    }
    return report
