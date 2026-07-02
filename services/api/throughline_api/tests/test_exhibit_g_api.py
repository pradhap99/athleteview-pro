"""Task 5.5 via the API — Exhibit G rows/render/sign + hot costs from the same feed."""

from __future__ import annotations

from throughline_api.tests.test_timecards_api import MEMO, TIMECARD

CREW_MEMO = {
    "person": "Grip",
    "union": "IATSE",
    "contract": "basic_agreement",
    "tier": "crew",
    "hourlyRate": 50.0,
    "guaranteedHours": 8.0,
    "accountCode": "2100",
}


def _project(client) -> str:
    pid = client.post(
        "/v1/projects",
        json={"title": "Shoot", "type": "scripted", "ppStartDate": "2025-01-01"},
    ).json()["id"]
    client.post(f"/v1/projects/{pid}/deal-memos", json=MEMO)
    client.post(f"/v1/projects/{pid}/deal-memos", json=CREW_MEMO)
    client.post(f"/v1/projects/{pid}/timecards", json=TIMECARD)
    # IATSE crew day on the same date — must NOT appear on Exhibit G (SAG form).
    client.post(
        f"/v1/projects/{pid}/timecards",
        json={
            "person": "Grip",
            "date": "2025-03-10",
            "call": "2025-03-10T07:00:00",
            "wrap": "2025-03-10T15:30:00",
            "meals": [{"start": "2025-03-10T12:00:00", "end": "2025-03-10T12:30:00"}],
        },
    )
    return pid


def test_exhibit_g_rows_are_sag_only_with_guild_fields(client):
    pid = _project(client)
    doc = client.get(f"/v1/projects/{pid}/exhibit-g", params={"date": "2025-03-10"}).json()
    assert len(doc["rows"]) == 1  # the IATSE grip is not on the SAG form
    row = doc["rows"][0]
    assert row["legalName"] == "Alice Q. Performer"
    assert row["workStatusCode"] == "W"
    assert row["workedTenths"] == 10.0  # tenths of an hour
    assert row["mpvCount"] == 2
    assert row["forcedCall"] is False
    assert row["isMinor"] is False
    assert row["signature"] is None  # unsigned until the performer signs


def test_exhibit_g_signature_flow_and_text_render(client):
    pid = _project(client)
    r = client.post(
        f"/v1/projects/{pid}/exhibit-g/Alice:sign",
        json={"date": "2025-03-10"},
        headers={"X-User-Id": "alice-mobile"},
    )
    assert r.status_code == 200
    row = client.get(f"/v1/projects/{pid}/exhibit-g", params={"date": "2025-03-10"}).json()["rows"][
        0
    ]
    assert row["signature"]["signedBy"] == "alice-mobile"

    text = client.get(
        f"/v1/projects/{pid}/exhibit-g", params={"date": "2025-03-10", "format": "text"}
    ).text
    assert "EXHIBIT G — PERFORMER TIME REPORT" in text
    assert "Alice Q. Performer" in text
    assert "✓ alice-mobile" in text


def test_sign_requires_a_timecard(client):
    pid = _project(client)
    r = client.post(f"/v1/projects/{pid}/exhibit-g/Nobody:sign", json={"date": "2025-03-10"})
    assert r.status_code == 404


def test_hot_costs_regenerate_from_the_exhibit_g_feed(client):
    pid = _project(client)
    doc = client.get(f"/v1/projects/{pid}/hot-costs", params={"date": "2025-03-10"}).json()
    by_person = {line["person"]: line for line in doc["lines"]}
    # Alice: budgeted 8h × 100 = 800; actual 1170 (OT + MPVs) → over by 370.
    assert by_person["Alice"]["budgeted"] == 800.0
    assert by_person["Alice"]["total"] == 1170.0
    assert by_person["Alice"]["variance"] == -370.0
    # Grip (IATSE): clean 8h day → 400 vs 400.
    assert by_person["Grip"]["total"] == 400.0
    assert by_person["Grip"]["variance"] == 0.0
    assert doc["totalActual"] == 1570.0


def test_hot_costs_empty_date(client):
    pid = _project(client)
    doc = client.get(f"/v1/projects/{pid}/hot-costs", params={"date": "2030-01-01"}).json()
    assert doc["lines"] == [] and doc["totalActual"] == 0.0
