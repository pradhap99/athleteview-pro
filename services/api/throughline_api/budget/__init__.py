"""Budget engine (tasks 2.3 / 5.3): lines, fringes, cost report, hot costs.

Everything here is **data-driven** — no rate, multiplier, or threshold literal appears in
this package (enforced by ``make check-rates``, which scans this directory). Every figure
is **explainable**: it expands to its derivation string (rate × qty × unit + fringes).
Cost-report math is fixed (guardrail): ``EFC = Actuals + Committed + ETC``;
``Variance = Budget − EFC``. Fringes flow proportionally when wages change because they
are always *derived* from the current wage total, never stored.
"""

from .costreport import AccountRow, CostReport, build_cost_report
from .hotcosts import HotCostLine, HotCostReport, compute_hot_costs
from .model import BudgetLine, Fringe, line_from_payload

__all__ = [
    "BudgetLine",
    "Fringe",
    "line_from_payload",
    "CostReport",
    "AccountRow",
    "build_cost_report",
    "HotCostReport",
    "HotCostLine",
    "compute_hot_costs",
]
