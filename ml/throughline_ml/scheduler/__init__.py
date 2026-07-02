"""CP-SAT shooting-schedule optimizer + DOOD derivation (task 2.1).

The solver *proposes*; humans confirm (guardrail). Hard constraints are never violated
in a proposed schedule (eval gate: violations == 0). Objective minimizes company moves +
cast hold-days. See PRODUCT_SPEC §7.3 / §15.2.
"""

from .dood import derive_dood, hold_days
from .model import solve_schedule
from .types import Scene, SchedulingProblem, Solution, SolveStatus

__all__ = [
    "solve_schedule",
    "derive_dood",
    "hold_days",
    "Scene",
    "SchedulingProblem",
    "Solution",
    "SolveStatus",
]
