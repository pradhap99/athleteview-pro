"""Effective-dated rate-card library.

A rate card bundles the rule parameters (OT tiers, meal thresholds, turnaround, premium
days) for one (union, contract, tier) as of an ``effective_date``. Resolution picks the
latest card whose ``effective_date`` is on or before the production's principal-photography
start date — this is how the 2024 MOA threshold changes phase in by shoot start.

All numeric parameters live in the YAML files under ``tables/``; this module only loads
and selects them.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

TABLES_DIR = Path(__file__).parent / "tables"


@dataclass(frozen=True)
class RuleRef:
    """A citation back to the exact table entry a flag was derived from (explainability)."""

    union: str
    contract: str
    tier: str
    effective_date: dt.date
    rule_key: str
    threshold: Any
    source_file: str

    def cite(self) -> str:
        return (
            f"{self.union} / {self.contract} / {self.tier} "
            f"(eff. {self.effective_date.isoformat()}) · {self.rule_key}={self.threshold} "
            f"[{self.source_file}]"
        )


@dataclass(frozen=True)
class RateCard:
    union: str
    contract: str
    tier: str
    effective_date: dt.date
    params: dict[str, Any]
    source_file: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.union, self.contract, self.tier)

    def ref(self, rule_key: str, threshold: Any) -> RuleRef:
        return RuleRef(
            union=self.union,
            contract=self.contract,
            tier=self.tier,
            effective_date=self.effective_date,
            rule_key=rule_key,
            threshold=threshold,
            source_file=self.source_file,
        )


class RateCardLibrary:
    """Loads rate cards from YAML and resolves them by effective date."""

    def __init__(self) -> None:
        self._cards: list[RateCard] = []

    @classmethod
    def from_dir(cls, path: str | Path = TABLES_DIR) -> RateCardLibrary:
        lib = cls()
        for yml in sorted(Path(path).glob("*.yaml")):
            doc = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            for entry in doc.get("cards", []):
                lib._add(entry, yml.name)
        return lib

    def _add(self, entry: dict[str, Any], source_file: str) -> None:
        eff = entry["effective_date"]
        if isinstance(eff, str):
            eff = dt.date.fromisoformat(eff)
        self._cards.append(
            RateCard(
                union=entry["union"],
                contract=entry["contract"],
                tier=entry["tier"],
                effective_date=eff,
                params=entry["params"],
                source_file=source_file,
            )
        )

    def resolve(
        self,
        union: str,
        contract: str,
        tier: str,
        pp_start_date: dt.date,
    ) -> RateCard:
        """Return the latest card for the key effective on or before ``pp_start_date``."""
        candidates = [
            c
            for c in self._cards
            if c.key == (union, contract, tier) and c.effective_date <= pp_start_date
        ]
        if not candidates:
            raise LookupError(
                f"no rate card for {union}/{contract}/{tier} effective by "
                f"{pp_start_date.isoformat()}"
            )
        return max(candidates, key=lambda c: c.effective_date)

    def keys(self) -> list[tuple[str, str, str]]:
        return sorted({c.key for c in self._cards})


_DEFAULT: RateCardLibrary | None = None


def default_library() -> RateCardLibrary:
    """Process-wide library loaded from the bundled ``tables/`` directory (cached)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = RateCardLibrary.from_dir()
    return _DEFAULT
