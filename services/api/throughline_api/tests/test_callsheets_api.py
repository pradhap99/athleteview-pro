"""Task 4.1 — call sheets auto-populate; revisions supersede + re-notify only affected."""

from __future__ import annotations

SCRIPT = """INT. STAGE A - DAY #1#

ALICE
Places.

INT. STAGE A - DAY #2#

ALICE
Again.

EXT. PARK - DAY #3#

BOB
Out here.
"""


def _project(client) -> str:
    pid = client.post("/v1/projects", json={"title": "CS", "type": "scripted"}).json()["id"]
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SCRIPT})
    # Force a 2-day split so day 0 = STAGE A (Alice), day 1 = PARK (Bob).
    opt = client.post(
        f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 2, "capacityEighths": 2}
    ).json()
    client.post(f"/v1/projects/{pid}/changes/{opt['diff']['id']}:confirm")
    # A matching location record enriches the sheet with sun/hospital info.
    client.post(
        f"/v1/projects/{pid}/locations",
        json={
            "name": "Park",
            "lat": 34.05,
            "lng": -118.24,
            "nearestHospital": "LAC+USC (24h)",
            "parking": "Lot 4",
        },
    )
    return pid


def _day_for(client, pid, location: str) -> int:
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    return next(s["day"] for s in graph["scenes"] if s["location"] == location)


def test_call_sheet_autopopulates_from_graph(client):
    pid = _project(client)
    park_day = _day_for(client, pid, "PARK")
    r = client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={
            "dayIndex": park_day,
            "date": "2025-06-21",
            "generalCall": "06:30",
            "extraRecipients": [{"name": "Priya", "email": "p@x.com", "role": "coordinator"}],
        },
    )
    assert r.status_code == 201, r.text
    sheet = r.json()
    content = sheet["content"]
    assert content["generalCall"] == "06:30"
    assert [s["number"] for s in content["scenes"]] == ["3"]
    assert content["cast"][0]["character"] == "BOB"
    assert content["cast"][0]["doodCode"] in ("SW", "SWF", "W", "WF")
    # Location day-info matched by name (case-insensitive): sun + hospital + parking.
    assert content["locationInfo"]["nearestHospital"].startswith("LAC+USC")
    assert content["locationInfo"]["sunriseUtc"].startswith("2025-06-21T")
    # Company move INTO the park day (from STAGE A).
    assert content["companyMoveIn"]["fromLocation"] == "STAGE A"
    # First publish notifies everyone.
    assert set(sheet["renotify"]) == {"BOB", "Priya"}


def test_ack_by_capability_token_and_tracking(client):
    pid = _project(client)
    park_day = _day_for(client, pid, "PARK")
    sheet = client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={"dayIndex": park_day, "date": "2025-06-21"},
    ).json()
    token = sheet["recipients"][0]["ackToken"]

    r = client.post(
        f"/v1/projects/{pid}/call-sheets/{sheet['id']}:acknowledge", json={"ackToken": token}
    )
    assert r.json()["acknowledged"] is True
    # Wrong token → 404, nothing recorded.
    r = client.post(
        f"/v1/projects/{pid}/call-sheets/{sheet['id']}:acknowledge", json={"ackToken": "bogus"}
    )
    assert r.status_code == 404

    sheets = client.get(f"/v1/projects/{pid}/call-sheets").json()["callSheets"]
    recipient = sheets[-1]["recipients"][0]
    assert recipient["acknowledgedAt"]


def test_revision_supersedes_and_renotifies_only_affected(client):
    pid = _project(client)
    stage_day = _day_for(client, pid, "STAGE A")
    v1 = client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={
            "dayIndex": stage_day,
            "date": "2025-06-21",
            "generalCall": "07:00",
            "extraRecipients": [{"name": "Priya", "email": "p@x.com"}],
        },
    ).json()

    # Re-publish with the SAME content → supersedes v1, but nobody's day changed.
    v2 = client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={
            "dayIndex": stage_day,
            "date": "2025-06-21",
            "generalCall": "07:00",
            "extraRecipients": [{"name": "Priya", "email": "p@x.com"}],
        },
    ).json()
    assert v2["revision"] == 2 and v2["supersedes"] == v1["id"]
    assert v2["renotify"] == []  # no one affected → no re-notification

    # Change the general call → EVERYONE on the sheet is affected.
    v3 = client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={
            "dayIndex": stage_day,
            "date": "2025-06-21",
            "generalCall": "05:45",
            "extraRecipients": [{"name": "Priya", "email": "p@x.com"}],
        },
    ).json()
    assert set(v3["renotify"]) == {"ALICE", "Priya"}

    # Graph marks the chain: v1 and v2 superseded, v3 current.
    sheets = client.get(f"/v1/projects/{pid}/call-sheets", params={"day": stage_day}).json()[
        "callSheets"
    ]
    superseded = {s["revision"]: s["supersededBy"] for s in sheets}
    assert superseded[1] is not None and superseded[2] is not None
    assert superseded[3] is None


def test_publish_requires_scheduled_day(client):
    pid = client.post("/v1/projects", json={"title": "Empty"}).json()["id"]
    r = client.post(
        f"/v1/projects/{pid}/call-sheets:publish", json={"dayIndex": 0, "date": "2025-06-21"}
    )
    assert r.status_code == 422


def test_copilot_nudges_per_role(client):
    pid = _project(client)
    stage_day = _day_for(client, pid, "STAGE A")
    client.post(
        f"/v1/projects/{pid}/call-sheets:publish",
        json={"dayIndex": stage_day, "date": "2025-06-21"},
    )
    # An over-budget account for the LP nudge.
    client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={
            "code": "2100",
            "category": "btl",
            "description": "G&E",
            "qty": 1,
            "unit": "flat",
            "rate": 1000,
        },
    )
    client.post(f"/v1/projects/{pid}/budget/actuals", json={"code": "2100", "amount": 1500})

    coord = client.get(f"/v1/projects/{pid}/copilot/nudges", params={"role": "coordinator"}).json()[
        "nudges"
    ]
    assert any(n["kind"] == "callsheet_unacked" and "ALICE" in n["message"] for n in coord)

    ad = client.get(f"/v1/projects/{pid}/copilot/nudges", params={"role": "first_ad"}).json()[
        "nudges"
    ]
    assert any(n["kind"] == "company_move" and "STAGE A" in n["message"] for n in ad)

    lp = client.get(f"/v1/projects/{pid}/copilot/nudges", params={"role": "line_producer"}).json()[
        "nudges"
    ]
    assert any(n["kind"] == "over_budget" and "2100" in n["message"] for n in lp)
    # Every nudge cites its graph fact.
    assert all(n["ref"] for n in coord + ad + lp)

    r = client.get(f"/v1/projects/{pid}/copilot/nudges", params={"role": "gaffer"})
    assert r.status_code == 422
