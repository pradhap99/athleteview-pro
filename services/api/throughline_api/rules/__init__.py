"""Union & labor-compliance rules engine (tasks 5.1 / 5.2).

The single highest-value feature and a moat. Everything rate-like is **table-driven** and
**effective-dated** — keyed on union × contract × tier × location-context ×
principal-photography-start-date. NO rate, multiplier, or hour threshold is hard-coded in
this package; ``scripts/check_no_hardcoded_rates.py`` (`make check-rates`) fails the build
if one appears. Flags are PREDICTIVE (fire at schedule time) and EXPLAINABLE (cite the
rule + the exact table entry). See PRODUCT_SPEC §7A.1.
"""

from .engine import DayWork, Flag, FlagSeverity, RulesEngine
from .ratecards import RateCard, RateCardLibrary, RuleRef, default_library

__all__ = [
    "RulesEngine",
    "DayWork",
    "Flag",
    "FlagSeverity",
    "RateCard",
    "RateCardLibrary",
    "RuleRef",
    "default_library",
]
