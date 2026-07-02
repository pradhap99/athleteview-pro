"""Scheduler EVAL GATE (PRODUCT_SPEC §15.2) — runs the golden instance bank.

Run with ``make evals`` (``pytest -m eval``). Asserts feasibility == 100%, zero
hard-constraint violations, and mean optimality gap ≤ 10% across the bank.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.graders import check_scheduler_gates, grade_solution
from throughline_ml.scheduler import Scene, SchedulingProblem, solve_schedule

INSTANCES = Path(__file__).parents[1] / "datasets" / "scheduler" / "instances.json"


def _load_problems() -> list[SchedulingProblem]:
    data = json.loads(INSTANCES.read_text(encoding="utf-8"))
    problems = []
    for inst in data["instances"]:
        problems.append(
            SchedulingProblem(
                scenes=[
                    Scene(
                        id=s["id"],
                        location=s["location"],
                        cast=frozenset(s["cast"]),
                        page_eighths=s["page_eighths"],
                    )
                    for s in inst["scenes"]
                ],
                num_days=inst["num_days"],
                capacity_eighths=inst.get("capacity_eighths"),
                time_budget_s=10.0,
            )
        )
    return problems


@pytest.mark.eval
def test_scheduler_gates_on_golden_bank():
    problems = _load_problems()
    results = [(p, solve_schedule(p)) for p in problems]
    report = grade_solution(results)

    assert report.instances == len(problems)
    passed, failures = check_scheduler_gates(report)
    assert passed, f"scheduler eval gate failed: {failures}"
    # Explicit invariants for the regression record.
    assert report.total_violations == 0
    assert report.feasibility_rate == 1.0
    assert report.mean_gap <= 0.10
