"""Budget lines + fringes with full derivations.

A :class:`BudgetLine` is qty × rate (in ``unit``) plus derived fringes. ``driver`` links a
line to the graph fact that drives it (e.g. ``{"kind": "hold_day"}`` — the line's rate is
applied per cast hold day), which is what powers "cost of this decision" ripple deltas.

Fringes are never stored as amounts: they are recomputed from the current wage total every
time, so they flow proportionally when wages change (guardrail).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CATEGORIES = ("atl", "btl", "post", "other")


@dataclass(frozen=True)
class Fringe:
    """A named fringe: ``rate_pct`` of the wage base, optionally capped per line."""

    name: str
    rate_pct: float  # percentage, e.g. 22.5 — data, never hard-coded
    cap: float | None = None  # max fringe dollars per line (None = uncapped)

    def amount(self, base: float) -> float:
        raw = base * self.rate_pct / 100
        if self.cap is not None:
            raw = min(raw, self.cap)
        return round(raw, 2)

    def derivation(self, base: float) -> str:
        capped = self.cap is not None and base * self.rate_pct / 100 > self.cap
        text = f"{self.name}: {base:,.2f} × {self.rate_pct}%"
        if capped:
            text += f" (capped at {self.cap:,.2f})"
        return f"{text} = {self.amount(base):,.2f}"


@dataclass
class BudgetLine:
    id: str
    code: str  # account code, e.g. "2100" or AICP "B-12"
    category: str  # atl | btl | post | other
    description: str
    qty: float
    unit: str  # day | week | flat | allow | eighth
    rate: float
    fringes: list[Fringe] = field(default_factory=list)
    driver: dict[str, Any] | None = None  # e.g. {"kind": "hold_day", "cast": "ALICE"}
    aicp_section: str | None = None  # AICP bid-form section letter (A–W)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}, got {self.category!r}")

    @property
    def base_total(self) -> float:
        return round(self.qty * self.rate, 2)

    @property
    def fringe_total(self) -> float:
        return round(sum(f.amount(self.base_total) for f in self.fringes), 2)

    @property
    def total(self) -> float:
        return round(self.base_total + self.fringe_total, 2)

    def derivation(self) -> str:
        """Every figure expands to its derivation (explainability principle)."""
        parts = [f"{self.qty} {self.unit} × {self.rate:,.2f} = {self.base_total:,.2f}"]
        parts.extend(f.derivation(self.base_total) for f in self.fringes)
        if self.fringes:
            parts.append(f"total = {self.total:,.2f}")
        return " · ".join(parts)

    def reprice(self, new_rate: float) -> BudgetLine:
        """Return a copy at a new rate — fringes recompute automatically (proportional flow)."""
        return BudgetLine(
            id=self.id,
            code=self.code,
            category=self.category,
            description=self.description,
            qty=self.qty,
            unit=self.unit,
            rate=new_rate,
            fringes=list(self.fringes),
            driver=dict(self.driver) if self.driver else None,
            aicp_section=self.aicp_section,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "category": self.category,
            "description": self.description,
            "qty": self.qty,
            "unit": self.unit,
            "rate": self.rate,
            "fringes": [
                {"name": f.name, "ratePct": f.rate_pct, "cap": f.cap} for f in self.fringes
            ],
            "driver": self.driver,
            "aicpSection": self.aicp_section,
            "total": self.total,
            "derivation": self.derivation(),
        }


def line_from_payload(p: dict[str, Any]) -> BudgetLine:
    """Rebuild a BudgetLine from an event payload (inverse of ``to_payload``)."""
    return BudgetLine(
        id=p["id"],
        code=p.get("code", ""),
        category=p.get("category", "other"),
        description=p.get("description", ""),
        qty=float(p.get("qty", 1.0)),
        unit=p.get("unit", "flat"),
        rate=float(p.get("rate", 0.0)),
        fringes=[
            Fringe(name=f["name"], rate_pct=float(f["ratePct"]), cap=f.get("cap"))
            for f in p.get("fringes", [])
        ],
        driver=p.get("driver"),
        aicp_section=p.get("aicpSection"),
    )
