"""Breakdown information-extraction grader: per-type precision/recall/F1 (PRODUCT_SPEC §15.1).

An element is matched by ``(etype, normalized-name)``. Gates (block merge):
  * characters / locations F1 ≥ 0.90
  * props / wardrobe / vehicles F1 ≥ 0.80
  * safety-critical (stunt / sfx / animal / vehicle) *recall* ≥ 0.95
Net-time-saved is measured separately in a timed QA study; ship only if > 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SAFETY_CRITICAL = frozenset({"stunt", "sfx", "animal", "vehicle"})


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def _prf1(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


@dataclass
class BreakdownReport:
    per_type: dict[str, dict[str, float]] = field(default_factory=dict)  # etype -> {p,r,f1,n}
    micro_f1: float = 0.0
    macro_f1: float = 0.0
    safety_recall: float = 0.0

    def f1(self, etype: str) -> float:
        return self.per_type.get(etype, {}).get("f1", 0.0)


def _to_sets(items: list[tuple[str, str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for etype, name in items:
        out.setdefault(etype, set()).add(_norm(name))
    return out


def grade_breakdown(
    predictions: list[tuple[str, str]], gold: list[tuple[str, str]]
) -> BreakdownReport:
    """Grade predicted ``(etype, name)`` pairs against a gold set."""
    pred = _to_sets(predictions)
    gld = _to_sets(gold)
    report = BreakdownReport()

    all_types = sorted(set(pred) | set(gld))
    micro_tp = micro_fp = micro_fn = 0
    f1s: list[float] = []
    for etype in all_types:
        p_set, g_set = pred.get(etype, set()), gld.get(etype, set())
        precision, recall, f1 = _prf1(p_set, g_set)
        report.per_type[etype] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "n": float(len(g_set)),
        }
        micro_tp += len(p_set & g_set)
        micro_fp += len(p_set - g_set)
        micro_fn += len(g_set - p_set)
        f1s.append(f1)

    mp = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) else 1.0
    mr = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) else 1.0
    report.micro_f1 = 2 * mp * mr / (mp + mr) if (mp + mr) else 0.0
    report.macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    sc_pred = {n for t in SAFETY_CRITICAL for n in pred.get(t, set())}
    sc_gold = {n for t in SAFETY_CRITICAL for n in gld.get(t, set())}
    _, report.safety_recall, _ = _prf1(sc_pred, sc_gold)
    return report


def check_breakdown_gates(report: BreakdownReport) -> tuple[bool, list[str]]:
    """Return (passed, failure-reasons) for the merge-blocking breakdown gates."""
    failures: list[str] = []
    for etype in ("cast", "location"):
        # 'cast' F1 stands in for characters; only checked when present in gold.
        if etype in report.per_type and report.f1(etype) < 0.90:
            failures.append(f"{etype} F1 {report.f1(etype):.2f} < 0.90")
    for etype in ("prop", "wardrobe", "vehicle"):
        if etype in report.per_type and report.f1(etype) < 0.80:
            failures.append(f"{etype} F1 {report.f1(etype):.2f} < 0.80")
    if report.safety_recall < 0.95:
        failures.append(f"safety-critical recall {report.safety_recall:.2f} < 0.95")
    return (not failures, failures)
