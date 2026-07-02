"""Task 6.3 — solar math, doc vault expiry alerts, day-info, company moves."""

from __future__ import annotations

import datetime as dt

from throughline_api.locations import sun_times_utc

LA = (34.0522, -118.2437)


# ---- deterministic solar calculation (no network) ----------------------------


def _minutes_off(actual: dt.datetime, expected: dt.datetime) -> float:
    return abs((actual - expected).total_seconds()) / 60.0


def test_sun_times_la_summer_solstice():
    sun = sun_times_utc(*LA, dt.date(2025, 6, 21))
    assert sun is not None
    sunrise, sunset = sun
    # Known values for LA on 2025-06-21: sunrise ≈ 05:42 PDT (12:42 UTC),
    # sunset ≈ 20:08 PDT (03:08 UTC next day). Allow ±6 min (NOAA short form).
    assert _minutes_off(sunrise, dt.datetime(2025, 6, 21, 12, 42, tzinfo=dt.UTC)) <= 6
    assert _minutes_off(sunset, dt.datetime(2025, 6, 22, 3, 8, tzinfo=dt.UTC)) <= 6


def test_sun_times_la_winter_solstice():
    sun = sun_times_utc(*LA, dt.date(2025, 12, 21))
    assert sun is not None
    sunrise, sunset = sun
    # sunrise ≈ 06:55 PST (14:55 UTC), sunset ≈ 16:48 PST (00:48 UTC next day).
    assert _minutes_off(sunrise, dt.datetime(2025, 12, 21, 14, 55, tzinfo=dt.UTC)) <= 6
    assert _minutes_off(sunset, dt.datetime(2025, 12, 22, 0, 48, tzinfo=dt.UTC)) <= 6


def test_polar_night_returns_none():
    assert sun_times_utc(78.2, 15.6, dt.date(2025, 12, 21)) is None  # Svalbard, winter


# ---- API flows ----------------------------------------------------------------


def _project(client) -> str:
    return client.post("/v1/projects", json={"title": "Loc", "type": "scripted"}).json()["id"]


def _add_location(client, pid, **overrides) -> str:
    body = {
        "name": "Griffith Park",
        "address": "4730 Crystal Springs Dr, LA",
        "lat": LA[0],
        "lng": LA[1],
        "parking": "Lot B",
        "basecamp": "North lawn",
        "nearestHospital": "LAC+USC Medical Center (24h)",
        **overrides,
    }
    return client.post(f"/v1/projects/{pid}/locations", json=body).json()["id"]


def test_day_info_has_sun_magic_hour_and_logistics(client):
    pid = _project(client)
    loc = _add_location(client, pid)
    info = client.get(
        f"/v1/projects/{pid}/locations/{loc}/day-info", params={"date": "2025-06-21"}
    ).json()
    assert info["nearestHospital"].startswith("LAC+USC")
    assert info["parking"] == "Lot B" and info["basecamp"] == "North lawn"
    assert info["sunriseUtc"].startswith("2025-06-21T12:4")
    # magic hour derived from the sun times
    assert info["morningMagicHourEndUtc"] > info["sunriseUtc"]
    assert info["eveningMagicHourStartUtc"] < info["sunsetUtc"]
    assert info["weather"] is None  # external provider seam (call-sheet layer)


def test_coi_expiry_alerts(client):
    pid = _project(client)
    loc = _add_location(client, pid)
    today = dt.date.today()

    def add_doc(doc_type, days_from_now, **extra):
        client.post(
            f"/v1/projects/{pid}/locations/{loc}/documents",
            json={
                "type": doc_type,
                "expiryDate": (today + dt.timedelta(days=days_from_now)).isoformat(),
                **extra,
            },
        )

    add_doc("coi", -3, liabilityLimit=2_000_000, additionalInsured="Throughline Prods")
    add_doc("permit", 10)
    add_doc("release", 90)  # outside the 30-day window — no alert

    alerts = client.get(f"/v1/projects/{pid}/locations:alerts").json()["alerts"]
    assert [a["type"] for a in alerts] == ["coi", "permit"]  # most urgent first
    coi = alerts[0]
    assert coi["status"] == "expired" and coi["daysRemaining"] == -3
    assert coi["liabilityLimit"] == 2_000_000
    assert coi["additionalInsured"] == "Throughline Prods"
    assert alerts[1]["status"] == "expiring"


def test_unknown_doc_type_rejected(client):
    pid = _project(client)
    loc = _add_location(client, pid)
    r = client.post(
        f"/v1/projects/{pid}/locations/{loc}/documents",
        json={"type": "menu", "expiryDate": "2030-01-01"},
    )
    assert r.status_code == 422


def test_company_moves_from_schedule(client):
    pid = _project(client)
    script = (
        "INT. STAGE A - DAY #1#\n\nALICE\nHi.\n\n"
        "INT. STAGE A - DAY #2#\n\nALICE\nMore.\n\n"
        "EXT. PARK - DAY #3#\n\nBOB\nOut here.\n"
    )
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": script})
    # Capacity forces a 2-day split; the solver clusters STAGE A together, PARK alone.
    opt = client.post(
        f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 2, "capacityEighths": 2}
    ).json()
    client.post(f"/v1/projects/{pid}/changes/{opt['diff']['id']}:confirm")

    moves = client.get(f"/v1/projects/{pid}/company-moves").json()["moves"]
    assert len(moves) == 1
    move = moves[0]
    assert {move["fromLocation"], move["toLocation"]} == {"STAGE A", "PARK"}
    assert move["toDay"] == move["fromDay"] + 1
