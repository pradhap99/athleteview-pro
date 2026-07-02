"""Location management (task 6.3).

Per-location **document vault** (signed release, permits, COI with additional-insured
endorsement + liability limit + expiry) with expiry alerts; **sunrise/sunset/magic hour**
computed deterministically (NOAA solar equations — no network, unit-testable) for the
call sheet; maps/parking/basecamp and the **nearest 24-hr hospital**; **company-move
logistics** derived from the confirmed schedule.

Weather is an external integration (network) and is wired at the call-sheet layer
(task 4.1) behind a provider seam — never in unit-tested core logic.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

from .graph import GraphState

DOC_TYPES = ("release", "permit", "coi")
_ZENITH_OFFICIAL_DEG = 90.833  # official sunrise/sunset zenith (refraction-corrected)
_GOLDEN_HOUR = dt.timedelta(hours=1)


# ---- NOAA solar position (deterministic; accurate to ~1–2 minutes) ------------


def _solar_params(day_of_year: int) -> tuple[float, float]:
    """(equation-of-time minutes, solar declination radians) for a day of year (noon)."""
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    return eqtime, decl


def sun_times_utc(lat: float, lng: float, date: dt.date) -> tuple[dt.datetime, dt.datetime] | None:
    """(sunrise, sunset) as UTC datetimes, or None in polar day/night conditions.

    ``lng`` is east-positive (Los Angeles ≈ -118.24).
    """
    eqtime, decl = _solar_params(date.timetuple().tm_yday)
    lat_rad = math.radians(lat)
    cos_ha = math.cos(math.radians(_ZENITH_OFFICIAL_DEG)) / (
        math.cos(lat_rad) * math.cos(decl)
    ) - math.tan(lat_rad) * math.tan(decl)
    if cos_ha < -1.0 or cos_ha > 1.0:
        return None  # sun never rises/sets at this latitude on this date
    ha_deg = math.degrees(math.acos(cos_ha))
    base = dt.datetime(date.year, date.month, date.day, tzinfo=dt.UTC)
    sunrise_min = 720.0 - 4.0 * (lng + ha_deg) - eqtime
    sunset_min = 720.0 - 4.0 * (lng - ha_deg) - eqtime
    return (
        base + dt.timedelta(minutes=sunrise_min),
        base + dt.timedelta(minutes=sunset_min),
    )


def day_info(location: dict[str, Any], date: dt.date) -> dict[str, Any]:
    """The call-sheet block for a location/date: sun, magic hour, logistics, hospital."""
    info: dict[str, Any] = {
        "locationId": location["id"],
        "name": location["name"],
        "date": date.isoformat(),
        "address": location.get("address", ""),
        "parking": location.get("parking", ""),
        "basecamp": location.get("basecamp", ""),
        "nearestHospital": location.get("nearestHospital", ""),
        "weather": None,  # external provider seam — wired at the call-sheet layer (4.1)
    }
    lat, lng = location.get("lat"), location.get("lng")
    if lat is not None and lng is not None:
        sun = sun_times_utc(float(lat), float(lng), date)
        if sun is not None:
            sunrise, sunset = sun
            info["sunriseUtc"] = sunrise.isoformat()
            info["sunsetUtc"] = sunset.isoformat()
            info["morningMagicHourEndUtc"] = (sunrise + _GOLDEN_HOUR).isoformat()
            info["eveningMagicHourStartUtc"] = (sunset - _GOLDEN_HOUR).isoformat()
    return info


# ---- document vault + expiry alerts --------------------------------------------


def expiry_alerts(state: GraphState, *, today: dt.date, within_days: int) -> list[dict[str, Any]]:
    """Expired or expiring-soon location documents (COI/permit/release), most urgent first."""
    horizon = today + dt.timedelta(days=within_days)
    alerts: list[dict[str, Any]] = []
    for location in state.locations.values():
        for doc in location.get("documents", []):
            expiry_iso = doc.get("expiryDate")
            if not expiry_iso:
                continue
            expiry = dt.date.fromisoformat(expiry_iso)
            if expiry <= horizon:
                alerts.append(
                    {
                        "locationId": location["id"],
                        "locationName": location["name"],
                        "docId": doc["docId"],
                        "type": doc["type"],
                        "expiryDate": expiry_iso,
                        "status": "expired" if expiry < today else "expiring",
                        "daysRemaining": (expiry - today).days,
                        "liabilityLimit": doc.get("liabilityLimit"),
                        "additionalInsured": doc.get("additionalInsured"),
                    }
                )
    return sorted(alerts, key=lambda a: a["daysRemaining"])


# ---- company moves from the schedule --------------------------------------------


def _primary_location(state: GraphState, day: int) -> str | None:
    counts: dict[str, int] = {}
    for scene_id, assigned in state.assignments.items():
        if assigned == day and scene_id in state.scenes:
            loc = state.scenes[scene_id].location
            counts[loc] = counts.get(loc, 0) + 1
    if not counts:
        return None
    return max(counts, key=lambda k: (counts[k], k))


def company_moves(state: GraphState) -> list[dict[str, Any]]:
    """Moves between consecutive shooting days whose primary location differs."""
    if not state.assignments:
        return []
    days = sorted(set(state.assignments.values()))
    moves: list[dict[str, Any]] = []
    for prev_day, next_day in zip(days, days[1:], strict=False):
        prev_loc = _primary_location(state, prev_day)
        next_loc = _primary_location(state, next_day)
        if prev_loc and next_loc and prev_loc != next_loc:
            moves.append(
                {
                    "fromDay": prev_day,
                    "toDay": next_day,
                    "fromLocation": prev_loc,
                    "toLocation": next_loc,
                }
            )
    return moves
