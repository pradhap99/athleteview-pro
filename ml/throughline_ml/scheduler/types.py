"""Scheduling problem + solution types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class Scene:
    id: str
    location: str
    cast: frozenset[str] = frozenset()
    page_eighths: int = 8
    int_ext: str = "INT"
    time_of_day: str = "DAY"


@dataclass
class SchedulingProblem:
    scenes: list[Scene]
    num_days: int
    # Optional hard constraints (None = unconstrained).
    capacity_eighths: int | None = None  # max shootable eighths per day
    cast_availability: dict[str, set[int]] = field(default_factory=dict)  # cast -> allowed days
    location_availability: dict[str, set[int]] = field(default_factory=dict)  # loc -> allowed days
    # Objective weights.
    company_move_weight: int = 10
    hold_day_weight: int = 1
    # Solver budget (seconds) — feeds the PAR-2 eval metric.
    time_budget_s: float = 10.0

    def cast(self) -> list[str]:
        seen: dict[str, None] = {}
        for scene in self.scenes:
            for c in scene.cast:
                seen.setdefault(c, None)
        return list(seen)

    def locations(self) -> list[str]:
        seen: dict[str, None] = {}
        for scene in self.scenes:
            seen.setdefault(scene.location, None)
        return list(seen)


class SolveStatus(str, Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


@dataclass
class Solution:
    status: SolveStatus
    assignments: dict[str, int] = field(default_factory=dict)  # scene_id -> day index
    dood: dict[str, list[str]] = field(default_factory=dict)  # cast -> per-day code
    location_days: int = 0  # count of (day, location) activations — company-move proxy
    total_hold_days: int = 0
    objective: float = 0.0
    best_bound: float = 0.0
    solve_time_s: float = 0.0

    @property
    def optimality_gap(self) -> float:
        """Relative gap vs the solver's best bound (0 == proven optimal)."""
        if self.objective == 0:
            return 0.0
        return abs(self.objective - self.best_bound) / max(1e-9, abs(self.objective))

    def day_plan(self) -> dict[int, list[str]]:
        plan: dict[int, list[str]] = {}
        for scene_id, day in sorted(self.assignments.items(), key=lambda kv: (kv[1], kv[0])):
            plan.setdefault(day, []).append(scene_id)
        return plan

    @property
    def feasible(self) -> bool:
        return self.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
