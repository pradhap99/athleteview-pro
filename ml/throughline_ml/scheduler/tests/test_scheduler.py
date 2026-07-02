"""Task 2.1 — CP-SAT scheduler tests (eval-gate style: feasibility + optimality gap)."""

from __future__ import annotations

import pytest

from throughline_ml.scheduler import Scene, SchedulingProblem, SolveStatus, solve_schedule


def _assert_hard_constraints(problem: SchedulingProblem, sol) -> None:
    # every scene assigned exactly once, to a valid day
    assert set(sol.assignments) == {s.id for s in problem.scenes}
    for day in sol.assignments.values():
        assert 0 <= day < problem.num_days
    # cast availability respected
    by_id = {s.id: s for s in problem.scenes}
    for sid, day in sol.assignments.items():
        for c in by_id[sid].cast:
            if c in problem.cast_availability:
                assert day in problem.cast_availability[c]
    # capacity respected
    if problem.capacity_eighths is not None:
        for _day, sids in sol.day_plan().items():
            assert sum(by_id[s].page_eighths for s in sids) <= problem.capacity_eighths


def test_groups_locations_and_finds_optimum():
    scenes = [
        Scene("s1", "STAGE_A", frozenset({"ALICE"})),
        Scene("s2", "STAGE_A", frozenset({"ALICE"})),
        Scene("s3", "PARK", frozenset({"BOB"})),
        Scene("s4", "PARK", frozenset({"BOB"})),
    ]
    problem = SchedulingProblem(scenes=scenes, num_days=2)
    sol = solve_schedule(problem)

    assert sol.status == SolveStatus.OPTIMAL
    _assert_hard_constraints(problem, sol)
    # Each location is clustered onto a single day (2 location-setups total), 0 holds.
    # (Whether the two locations share a day or not is objective-equivalent here.)
    assert sol.assignments["s1"] == sol.assignments["s2"]
    assert sol.assignments["s3"] == sol.assignments["s4"]
    assert sol.location_days == 2
    assert sol.total_hold_days == 0
    assert sol.optimality_gap == pytest.approx(0.0, abs=1e-9)


def test_cast_availability_is_a_hard_constraint():
    scenes = [
        Scene("s1", "LOFT", frozenset({"ALICE"})),
        Scene("s2", "LOFT", frozenset({"ALICE"})),
    ]
    # ALICE can only work on day index 1.
    problem = SchedulingProblem(scenes=scenes, num_days=2, cast_availability={"ALICE": {1}})
    sol = solve_schedule(problem)
    assert sol.feasible
    _assert_hard_constraints(problem, sol)
    assert sol.assignments["s1"] == 1 and sol.assignments["s2"] == 1


def test_minimizes_cast_hold_days():
    # ALICE is in scenes at both locations; a naive split would strand her on a hold day.
    scenes = [
        Scene("s1", "STAGE_A", frozenset({"ALICE"})),
        Scene("s2", "PARK", frozenset({"ALICE"})),
    ]
    problem = SchedulingProblem(scenes=scenes, num_days=3)
    sol = solve_schedule(problem)
    assert sol.status == SolveStatus.OPTIMAL
    # Best is both her scenes adjacent → zero holds.
    assert sol.total_hold_days == 0


def test_capacity_infeasibility_is_detected():
    scenes = [Scene(f"s{i}", "STAGE", page_eighths=8) for i in range(3)]
    # 24 eighths of work, 8/day cap, only 2 days = 16 capacity → infeasible.
    problem = SchedulingProblem(scenes=scenes, num_days=2, capacity_eighths=8)
    sol = solve_schedule(problem)
    assert sol.status == SolveStatus.INFEASIBLE
    assert not sol.feasible


def test_solves_within_budget():
    scenes = [
        Scene(f"s{i}", ["STAGE_A", "PARK", "OFFICE"][i % 3], frozenset({f"C{i % 4}"}))
        for i in range(12)
    ]
    problem = SchedulingProblem(scenes=scenes, num_days=5, time_budget_s=10.0)
    sol = solve_schedule(problem)
    assert sol.feasible
    _assert_hard_constraints(problem, sol)
    assert sol.solve_time_s <= problem.time_budget_s + 2.0
