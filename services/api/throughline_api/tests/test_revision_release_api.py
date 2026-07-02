"""Task 6.1 via the API — release colors advance; locked pages force A-scene numbers."""

from __future__ import annotations

V1 = """INT. KITCHEN - DAY #1#

JANE
Morning.

EXT. PARK - DAY #2#

BOB
Over here.
"""

# A scene inserted BETWEEN 1 and 2 (draft numbered #9#) and one BEFORE 1 (#8#).
V2 = """EXT. STOOP - DAWN #8#

JANE
(early)
Can't sleep.

INT. KITCHEN - DAY #1#

JANE
Morning.

INT. HALLWAY - DAY #9#

JANE
Keys, keys...

EXT. PARK - DAY #2#

BOB
Over here.
"""


def _project(client) -> str:
    pid = client.post("/v1/projects", json={"title": "Colors", "type": "scripted"}).json()["id"]
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": V1})
    return pid


def test_release_advances_the_color_order(client):
    pid = _project(client)
    first = client.post(f"/v1/projects/{pid}/script-revisions:release", json={}).json()
    second = client.post(
        f"/v1/projects/{pid}/script-revisions:release", json={"note": "after table read"}
    ).json()
    assert (first["index"], first["color"]) == (0, "White")
    assert (second["index"], second["color"]) == (1, "Blue")
    assert "Blue Revision — " in second["slug"]

    history = client.get(f"/v1/projects/{pid}/script-revisions").json()
    assert history["pagesLocked"] is True
    assert [h["color"] for h in history["history"]] == ["White", "Blue"]


def test_unlocked_project_keeps_draft_numbers(client):
    pid = _project(client)  # no release yet → numbering not locked
    r = client.post(f"/v1/projects/{pid}/scripts:diff", json={"text": V2}).json()
    added_numbers = {c["scene"]["number"] for c in r["diff"]["changes"] if c["op"] == "add_scene"}
    assert added_numbers == {"8", "9"}  # draft numbers pass through


def test_locked_pages_assign_a_scene_numbers(client):
    pid = _project(client)
    client.post(f"/v1/projects/{pid}/script-revisions:release", json={})  # White → locked

    r = client.post(f"/v1/projects/{pid}/scripts:diff", json={"text": V2}).json()
    adds = {
        c["scene"]["renumberedFrom"]: c["scene"]["number"]
        for c in r["diff"]["changes"]
        if c["op"] == "add_scene"
    }
    # Inserted before scene 1 → A1; inserted after scene 1 → 1A. Existing numbers untouched.
    assert adds == {"8": "A1", "9": "1A"}

    client.post(f"/v1/projects/{pid}/changes/{r['diff']['id']}:confirm")
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    numbers = {s["number"] for s in graph["scenes"]}
    assert numbers == {"1", "2", "A1", "1A"}  # no renumbering of 1 or 2
