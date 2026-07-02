"""Task 6.2 via the API — watermarked sides, capability links, tracking."""

from __future__ import annotations

import datetime as dt

SCRIPT = """INT. KITCHEN - DAY #1#

JANE stands at the counter, pouring coffee.

JANE
Morning.

EXT. PARK - DAY #2#

BOB waits on a bench.

BOB
Over here.

INT. OFFICE - NIGHT #3#

CARLA types.

CARLA
Late again.
"""


def _project_with_schedule(client) -> str:
    pid = client.post("/v1/projects", json={"title": "Sides", "type": "scripted"}).json()["id"]
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SCRIPT})
    opt = client.post(f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 1}).json()
    client.post(f"/v1/projects/{pid}/changes/{opt['diff']['id']}:confirm")
    return pid


def _issue(client, pid, **overrides) -> dict:
    body = {
        "dayIndex": 0,
        "recipientName": "Priya C",
        "recipientEmail": "priya@example.com",
        **overrides,
    }
    r = client.post(f"/v1/projects/{pid}/sides/links", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_sides_generate_in_scene_order_with_body(client):
    pid = _project_with_schedule(client)
    link = _issue(client, pid)
    doc = client.get(f"/v1/projects/{pid}/sides/links/{link['id']}/view").json()
    numbers = [p["number"] for p in doc["pages"]]
    assert numbers == ["1", "2", "3"]  # shooting order (scene-number order within the day)
    assert "pouring coffee" in doc["pages"][0]["body"]  # script text present


def test_watermark_burned_into_every_page(client):
    pid = _project_with_schedule(client)
    link = _issue(client, pid)
    doc = client.get(f"/v1/projects/{pid}/sides/links/{link['id']}/view").json()
    for page in doc["pages"]:
        assert "Priya C" in page["watermark"]
        assert "priya@example.com" in page["watermark"]
        assert link["id"] in page["watermark"]

    text = client.get(
        f"/v1/projects/{pid}/sides/links/{link['id']}/view", params={"format": "text"}
    ).text
    # One watermark at top and bottom of each of the 3 pages.
    assert text.count("CONFIDENTIAL — Priya C") == 6


def test_character_filtered_sides(client):
    pid = _project_with_schedule(client)
    link = _issue(client, pid, character="CARLA")
    doc = client.get(f"/v1/projects/{pid}/sides/links/{link['id']}/view").json()
    assert [p["number"] for p in doc["pages"]] == ["3"]


def test_expired_link_is_gone(client):
    pid = _project_with_schedule(client)
    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat()
    link = _issue(client, pid, expiresAt=past)
    r = client.get(f"/v1/projects/{pid}/sides/links/{link['id']}/view")
    assert r.status_code == 410 and "expired" in r.json()["detail"]


def test_revoked_link_is_gone_and_tracked(client):
    pid = _project_with_schedule(client)
    link = _issue(client, pid)
    client.post(f"/v1/projects/{pid}/sides/links/{link['id']}:revoke")
    r = client.get(f"/v1/projects/{pid}/sides/links/{link['id']}/view")
    assert r.status_code == 410 and "revoked" in r.json()["detail"]


def test_delivery_and_ack_tracking_with_chase_list(client):
    pid = _project_with_schedule(client)
    opened = _issue(client, pid, recipientName="Opened Only", recipientEmail="a@x.com")
    acked = _issue(client, pid, recipientName="Acked", recipientEmail="b@x.com")
    _issue(client, pid, recipientName="Never Opened", recipientEmail="c@x.com")

    client.get(f"/v1/projects/{pid}/sides/links/{opened['id']}/view")
    client.get(f"/v1/projects/{pid}/sides/links/{acked['id']}/view")
    client.post(f"/v1/projects/{pid}/sides/links/{acked['id']}:acknowledge")

    tracking = client.get(f"/v1/projects/{pid}/sides/tracking").json()
    by_name = {r["recipientName"]: r for r in tracking["recipients"]}
    assert by_name["Opened Only"]["opened"] and not by_name["Opened Only"]["acknowledged"]
    assert by_name["Acked"]["acknowledged"]
    assert not by_name["Never Opened"]["opened"]
    # Chase list = everyone who hasn't acknowledged (and isn't revoked).
    chase_names = {r["recipientName"] for r in tracking["chase"]}
    assert chase_names == {"Opened Only", "Never Opened"}


def test_issue_requires_scheduled_scenes(client):
    pid = client.post("/v1/projects", json={"title": "Empty"}).json()["id"]
    r = client.post(
        f"/v1/projects/{pid}/sides/links",
        json={"dayIndex": 0, "recipientName": "X", "recipientEmail": "x@x.com"},
    )
    assert r.status_code == 422
