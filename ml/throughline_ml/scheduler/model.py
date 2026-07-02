"""OR-Tools CP-SAT shooting-schedule model.

Assign each scene to a shooting day so that hard constraints (one day per scene, daily
page capacity, cast + location availability) are never violated, minimizing a weighted
sum of company moves (proxied by distinct location-days) and cast hold-days. The solver
proposes; a human confirms the resulting stripboard.
"""
# ortools ships incomplete type stubs; CpModel builder methods are added dynamically.
# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from ortools.sat.python import cp_model

from .dood import derive_dood, hold_days
from .types import SchedulingProblem, Solution, SolveStatus

_STATUS = {
    cp_model.OPTIMAL: SolveStatus.OPTIMAL,
    cp_model.FEASIBLE: SolveStatus.FEASIBLE,
    cp_model.INFEASIBLE: SolveStatus.INFEASIBLE,
    cp_model.UNKNOWN: SolveStatus.UNKNOWN,
    cp_model.MODEL_INVALID: SolveStatus.UNKNOWN,
}


def solve_schedule(problem: SchedulingProblem) -> Solution:
    if problem.num_days < 1:
        raise ValueError("num_days must be >= 1")
    model = cp_model.CpModel()
    days = range(problem.num_days)
    scenes = problem.scenes

    # x[s][d] == 1  iff scene s is shot on day d.
    x = {(s.id, d): model.NewBoolVar(f"x_{s.id}_{d}") for s in scenes for d in days}

    # Each scene is scheduled exactly once.
    for s in scenes:
        model.AddExactlyOne(x[s.id, d] for d in days)

    # Hard: cast availability — a scene cannot fall on a day any of its cast is unavailable.
    for s in scenes:
        for d in days:
            unavailable = any(
                c in problem.cast_availability and d not in problem.cast_availability[c]
                for c in s.cast
            )
            loc_avail = problem.location_availability.get(s.location)
            loc_bad = loc_avail is not None and d not in loc_avail
            if unavailable or loc_bad:
                model.Add(x[s.id, d] == 0)

    # Hard: daily page-eighths capacity.
    if problem.capacity_eighths is not None:
        for d in days:
            model.Add(sum(s.page_eighths * x[s.id, d] for s in scenes) <= problem.capacity_eighths)

    # Company-move proxy: used[l][d] = OR of scenes at location l on day d.
    locations = problem.locations()
    used = {}
    for loc in locations:
        loc_scenes = [s for s in scenes if s.location == loc]
        for d in days:
            u = model.NewBoolVar(f"used_{loc}_{d}")
            model.AddMaxEquality(u, [x[s.id, d] for s in loc_scenes])
            used[loc, d] = u
    location_days = sum(used.values())

    # Cast hold days: hold_c = (last - first + 1) - workdays, minimized.
    hold_terms = []
    for c in problem.cast():
        c_scenes = [s for s in scenes if c in s.cast]
        works = []
        for d in days:
            w = model.NewBoolVar(f"works_{c}_{d}")
            model.AddMaxEquality(w, [x[s.id, d] for s in c_scenes])
            works.append(w)
        first = model.NewIntVar(0, problem.num_days - 1, f"first_{c}")
        last = model.NewIntVar(0, problem.num_days - 1, f"last_{c}")
        for d in days:
            model.Add(first <= d).OnlyEnforceIf(works[d])
            model.Add(last >= d).OnlyEnforceIf(works[d])
        model.Add(first <= last)
        num_work = model.NewIntVar(0, problem.num_days, f"nwork_{c}")
        model.Add(num_work == sum(works))
        hold_c = model.NewIntVar(0, problem.num_days, f"hold_{c}")
        model.Add(hold_c == last - first + 1 - num_work)
        hold_terms.append(hold_c)
    total_hold = sum(hold_terms) if hold_terms else 0

    model.Minimize(
        problem.company_move_weight * location_days + problem.hold_day_weight * total_hold
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = problem.time_budget_s
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    mapped = _STATUS.get(status, SolveStatus.UNKNOWN)

    if mapped in (SolveStatus.INFEASIBLE, SolveStatus.UNKNOWN):
        return Solution(status=mapped, solve_time_s=solver.WallTime())

    assignments = {s.id: next(d for d in days if solver.Value(x[s.id, d]) == 1) for s in scenes}
    cast_workdays: dict[str, set[int]] = {}
    for s in scenes:
        for c in s.cast:
            cast_workdays.setdefault(c, set()).add(assignments[s.id])
    dood = derive_dood(cast_workdays, problem.num_days)

    return Solution(
        status=mapped,
        assignments=assignments,
        dood=dood,
        location_days=int(solver.Value(location_days)),
        total_hold_days=hold_days(dood),
        objective=solver.ObjectiveValue(),
        best_bound=solver.BestObjectiveBound(),
        solve_time_s=solver.WallTime(),
    )
