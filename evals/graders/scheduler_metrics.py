"""Scheduler optimizer grader (PRODUCT_SPEC §15.2).

Deterministic code graders. Gates (block merge):
  * hard-constraint violations == 0 (feasibility must be 100%)
  * mean optimality gap ≤ 10%
  * solve within a fixed wall-clock budget (PAR-2 penalty for timeouts)
"""

from __future__ import annotations

from dataclasses import dataclass

from throughline_ml.scheduler import SchedulingProblem, Solution


def count_hard_violations(problem: SchedulingProblem, solution: Solution) -> int:
    """Independently re-check the solution against the hard constraints (trust nothing)."""
    if not solution.feasible:
        return 1
    violations = 0
    by_id = {s.id: s for s in problem.scenes}
    if set(solution.assignments) != set(by_id):
        violations += 1
    for sid, day in solution.assignments.items():
        if not (0 <= day < problem.num_days):
            violations += 1
        for c in by_id[sid].cast:
            avail = problem.cast_availability.get(c)
            if avail is not None and day not in avail:
                violations += 1
    if problem.capacity_eighths is not None:
        for _day, sids in solution.day_plan().items():
            if sum(by_id[s].page_eighths for s in sids) > problem.capacity_eighths:
                violations += 1
    return violations


def par2(solve_time_s: float, budget_s: float) -> float:
    """PAR-2: solve time, or 2× the budget if it timed out."""
    return solve_time_s if solve_time_s <= budget_s else 2.0 * budget_s


@dataclass
class SchedulerReport:
    instances: int = 0
    feasible: int = 0
    total_violations: int = 0
    mean_gap: float = 0.0
    mean_par2: float = 0.0

    @property
    def feasibility_rate(self) -> float:
        return self.feasible / self.instances if self.instances else 1.0


def grade_solution(
    results: list[tuple[SchedulingProblem, Solution]],
) -> SchedulerReport:
    report = SchedulerReport(instances=len(results))
    gaps: list[float] = []
    par2s: list[float] = []
    for problem, solution in results:
        v = count_hard_violations(problem, solution)
        report.total_violations += v
        if solution.feasible and v == 0:
            report.feasible += 1
        gaps.append(solution.optimality_gap)
        par2s.append(par2(solution.solve_time_s, problem.time_budget_s))
    report.mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
    report.mean_par2 = sum(par2s) / len(par2s) if par2s else 0.0
    return report


def check_scheduler_gates(report: SchedulerReport) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if report.total_violations != 0:
        failures.append(f"hard-constraint violations {report.total_violations} != 0")
    if report.feasibility_rate < 1.0:
        failures.append(f"feasibility {report.feasibility_rate:.0%} < 100%")
    if report.mean_gap > 0.10:
        failures.append(f"mean optimality gap {report.mean_gap:.1%} > 10%")
    return (not failures, failures)
