"""Task 1.3 (server side) via the API — revision diff proposed, confirmed, applied."""

from __future__ import annotations

# Production revisions carry sticky scene numbers (locked pages, §7A.4) — the diff keys
# on them. V1 has scenes 1 (kitchen) and 2 (park).
V1 = """INT. KITCHEN - DAY #1#

JANE
Morning.

EXT. PARK - DAY #2#

BOB
Over here.
"""

# Kitchen (1) goes NIGHT and gains JOHN; park (2) is cut; alley (3) is new.
V2 = """INT. KITCHEN - NIGHT #1#

JANE
Morning.

JOHN
Barely.

EXT. ALLEY - NIGHT #3#

JANE
Follow me.
"""


def _project(client) -> str:
    pid = client.post("/v1/projects", json={"title": "Rev", "type": "scripted"}).json()["id"]
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": V1})
    return pid


def test_revision_diff_is_proposed_not_applied(client):
    pid = _project(client)
    r = client.post(f"/v1/projects/{pid}/scripts:diff", json={"text": V2}).json()
    assert r["diff"] is not None
    assert "Script revision" in r["diff"]["summary"]

    detail = r["detail"]
    assert detail["changed"][0]["charactersAdded"] == ["JOHN"]
    assert len(detail["added"]) == 1 and len(detail["removed"]) == 1

    # Not applied: the graph still shows the V1 scenes.
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    locations = {s["location"] for s in graph["scenes"]}
    assert locations == {"KITCHEN", "PARK"}


def test_confirming_revision_applies_scene_ops(client):
    pid = _project(client)
    r = client.post(f"/v1/projects/{pid}/scripts:diff", json={"text": V2}).json()
    diff_id = r["diff"]["id"]

    confirm = client.post(f"/v1/projects/{pid}/changes/{diff_id}:confirm")
    assert confirm.status_code == 200, confirm.text

    graph = client.get(f"/v1/projects/{pid}/graph").json()
    by_location = {s["location"]: s for s in graph["scenes"]}
    assert set(by_location) == {"KITCHEN", "ALLEY"}  # park removed, alley added
    kitchen = by_location["KITCHEN"]
    assert kitchen["timeOfDay"] == "NIGHT"  # updated in place
    assert kitchen["characters"] == ["JANE", "JOHN"]


def test_identical_revision_proposes_nothing(client):
    pid = _project(client)
    r = client.post(f"/v1/projects/{pid}/scripts:diff", json={"text": V1}).json()
    assert r["diff"] is None
    assert r["summary"].startswith("Script revision: No scene-level changes")
