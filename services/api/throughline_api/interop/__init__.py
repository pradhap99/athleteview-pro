"""Interop — deterministic import/export for industry formats (task 2.3 / §7.10).

Deterministic parsers own format fidelity — never AI (guardrail). AICP bid-form here;
Movie Magic (.mmb/.mmsp) round-trip is DEFERRED pending the legal review of the
proprietary format that PRODUCT_SPEC flags as a gating dependency.
"""

from .aicp import from_aicp, to_aicp, to_aicp_csv

__all__ = ["to_aicp", "from_aicp", "to_aicp_csv"]
