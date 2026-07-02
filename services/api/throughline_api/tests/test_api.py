"""Task 0.2/1.1/2.x — API integration: ingest, RBAC, human-confirms, propose→confirm ripple."""

from __future__ import annotations

from throughline_api.tests.conftest import SAMPLE_FOUNTAIN


def _create_project(client) -> str:
    r = client.post("/v1/projects", json={"title": "Demo", "type": "scripted"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_import_and_graph(client):
    pid = _create_project(client)
    r = client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SAMPLE_FOUNTAIN})
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["sceneCount"] == 2
    assert set(summary["characters"]) == {"JANE", "BOB"}

    graph = client.get(f"/v1/projects/{pid}/graph").json()
    assert len(graph["scenes"]) == 2
    assert {e["name"] for e in graph["elements"]} == {"JANE", "BOB"}
    assert all(e["status"] == "draft" for e in graph["elements"])


def test_human_confirm_gate(client):
    pid = _create_project(client)
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SAMPLE_FOUNTAIN})
    r = client.post(f"/v1/projects/{pid}/elements/el-cast-jane:confirm")
    assert r.status_code == 200 and r.json()["status"] == "confirmed"
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    by_name = {e["name"]: e for e in graph["elements"]}
    assert by_name["JANE"]["status"] == "confirmed"
    assert by_name["BOB"]["status"] == "draft"  # untouched


def test_rbac_tenant_isolation_and_role(client):
    pid = _create_project(client)  # created in org-dev
    # cross-tenant read is forbidden
    assert (
        client.get(f"/v1/projects/{pid}/graph", headers={"X-Org-Id": "other-org"}).status_code
        == 403
    )
    # a viewer may not write
    r = client.post(
        f"/v1/projects/{pid}/scripts:import",
        json={"text": SAMPLE_FOUNTAIN},
        headers={"X-Role": "viewer"},
    )
    assert r.status_code == 403


def test_optimize_is_proposed_not_applied_then_confirmed(client):
    pid = _create_project(client)
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SAMPLE_FOUNTAIN})

    opt = client.post(f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 2}).json()
    assert opt["solver"]["status"] in ("optimal", "feasible")
    diff_id = opt["diff"]["id"]
    # Proposed, NOT applied: the graph has no schedule yet (never a silent write).
    assert client.get(f"/v1/projects/{pid}/graph").json()["numDays"] == 0

    r = client.post(f"/v1/projects/{pid}/changes/{diff_id}:confirm")
    assert r.status_code == 200 and r.json()["applied"] is True
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    assert graph["numDays"] == 2
    assert all(s["day"] is not None for s in graph["scenes"])


def test_reschedule_ripple_and_time_machine(client):
    pid = _create_project(client)
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SAMPLE_FOUNTAIN})
    opt = client.post(f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 2}).json()
    client.post(f"/v1/projects/{pid}/changes/{opt['diff']['id']}:confirm")

    graph = client.get(f"/v1/projects/{pid}/graph").json()
    sc1 = next(s for s in graph["scenes"] if s["id"] == "sc-1")
    target_day = 1 - sc1["day"]

    prop = client.post(
        f"/v1/projects/{pid}/changes",
        json={"type": "reschedule_scene", "sceneId": "sc-1", "toDay": target_day},
    ).json()
    assert prop["status"] == "pending"
    assert "hold days" in prop["summary"]
    # still not applied
    assert (
        next(
            s for s in client.get(f"/v1/projects/{pid}/graph").json()["scenes"] if s["id"] == "sc-1"
        )["day"]
        == sc1["day"]
    )

    # head event id before applying the reschedule (Time Machine anchor)
    head_before = client.get(f"/v1/projects/{pid}/events").json()["events"][-1]["id"]

    client.post(f"/v1/projects/{pid}/changes/{prop['id']}:confirm")
    after = next(
        s for s in client.get(f"/v1/projects/{pid}/graph").json()["scenes"] if s["id"] == "sc-1"
    )
    assert after["day"] == target_day

    # rewind: as of head_before, sc-1 was still on its original day
    past = client.get(f"/v1/projects/{pid}/graph", params={"at": head_before}).json()
    assert next(s for s in past["scenes"] if s["id"] == "sc-1")["day"] == sc1["day"]
