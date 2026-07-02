"""Day-Out-of-Days derivation.

DOOD codes (PRODUCT_SPEC §9): SW=Start Work, W=Work, WF=Work Finish, H=Hold (idle day
between a performer's start and finish), SWF=Start-Work-Finish (single day). Empty string
= not yet started or already wrapped. Travel (T) is added by the on-set loop, not here.
"""

from __future__ import annotations


def derive_dood(cast_workdays: dict[str, set[int]], num_days: int) -> dict[str, list[str]]:
    """Given each performer's set of work-day indices, return their per-day DOOD codes."""
    result: dict[str, list[str]] = {}
    for cast, days in cast_workdays.items():
        codes = [""] * num_days
        if days:
            first, last = min(days), max(days)
            for d in range(num_days):
                if d < first or d > last:
                    codes[d] = ""
                elif d in days:
                    if first == last:
                        codes[d] = "SWF"
                    elif d == first:
                        codes[d] = "SW"
                    elif d == last:
                        codes[d] = "WF"
                    else:
                        codes[d] = "W"
                else:
                    codes[d] = "H"
        result[cast] = codes
    return result


def hold_days(dood: dict[str, list[str]]) -> int:
    """Total hold days across all performers (each 'H' is a paid idle day)."""
    return sum(codes.count("H") for codes in dood.values())
