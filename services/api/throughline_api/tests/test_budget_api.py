"""Tasks 2.2/2.3/5.3 via the API — budget, cost report, $-ripples, AICP export."""

from __future__ import annotations

from throughline_api.tests.conftest import SAMPLE_FOUNTAIN


def _project_with_schedule(client) -> str:
    pid = client.post("/v1/projects", json={"title": "Spot", "type": "commercial"}).json()["id"]
    client.post(f"/v1/projects/{pid}/scripts:import", json={"text": SAMPLE_FOUNTAIN})
    opt = client.post(f"/v1/projects/{pid}/schedule:optimize", json={"numDays": 2}).json()
    client.post(f"/v1/projects/{pid}/changes/{opt['diff']['id']}:confirm")
    return pid


def test_budget_line_and_cost_report_flow(client):
    pid = _project_with_schedule(client)
    r = client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={
            "code": "2100",
            "category": "btl",
            "description": "Key Grip",
            "qty": 10,
            "unit": "day",
            "rate": 500,
            "fringes": [{"name": "P&H", "ratePct": 22.0}],
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["total"] == 6100.0  # 5000 + 22%

    client.post(f"/v1/projects/{pid}/budget/actuals", json={"code": "2100", "amount": 1200})
    client.post(f"/v1/projects/{pid}/budget/commitments", json={"code": "2100", "amount": 800})
    client.post(f"/v1/projects/{pid}/budget/etc", json={"code": "2100", "amount": 4000})

    report = client.get(f"/v1/projects/{pid}/cost-report").json()
    row = next(r for r in report["rows"] if r["code"] == "2100")
    assert row["efc"] == 6000.0  # 1200 + 800 + 4000
    assert row["variance"] == 100.0  # 6100 − 6000
    assert "EFC = actuals" in row["derivation"]


def test_cost_report_time_machine(client):
    """The cost report at a past event id excludes later actuals."""
    pid = _project_with_schedule(client)
    client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={"code": "2100", "category": "btl", "qty": 1, "unit": "flat", "rate": 1000},
    )
    head = client.get(f"/v1/projects/{pid}/events").json()["events"][-1]["id"]
    client.post(f"/v1/projects/{pid}/budget/actuals", json={"code": "2100", "amount": 999})

    now = client.get(f"/v1/projects/{pid}/cost-report").json()
    past = client.get(f"/v1/projects/{pid}/cost-report", params={"at": head}).json()
    assert next(r for r in now["rows"] if r["code"] == "2100")["actuals"] == 999.0
    assert next(r for r in past["rows"] if r["code"] == "2100")["actuals"] == 0.0


def test_reschedule_ripple_carries_dollar_delta(client):
    pid = _project_with_schedule(client)
    # A hold day costs $850 (rate lives on the line, driven by the graph fact).
    client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={
            "code": "1300",
            "category": "atl",
            "description": "Cast day rate (holds)",
            "qty": 1,
            "unit": "day",
            "rate": 850,
            "driver": {"kind": "hold_day"},
        },
    )
    graph = client.get(f"/v1/projects/{pid}/graph").json()
    sc1 = next(s for s in graph["scenes"] if s["id"] == "sc-1")
    prop = client.post(
        f"/v1/projects/{pid}/changes",
        json={"type": "reschedule_scene", "sceneId": "sc-1", "toDay": 1 - sc1["day"]},
    ).json()
    # dollarDelta = holdDaysDelta × 850 (may be 0 if the move creates no holds — assert link)
    assert prop["dollarDelta"] == prop["holdDaysDelta"] * 850.0
    assert "to the top sheet" in prop["summary"]


def test_aicp_export_endpoint(client):
    pid = _project_with_schedule(client)
    client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={
            "code": "B-05",
            "category": "btl",
            "description": "DP",
            "qty": 3,
            "unit": "day",
            "rate": 1200,
            "aicpSection": "B",
        },
    )
    doc = client.post(f"/v1/projects/{pid}/budget:export", params={"format": "aicp"}).json()
    assert doc["format"] == "aicp-bid"
    assert doc["grandTotal"] == 3600.0
    section_b = next(s for s in doc["sections"] if s["section"] == "B")
    assert section_b["lines"][0]["description"] == "DP"

    csv_text = client.post(f"/v1/projects/{pid}/budget:export", params={"format": "csv"}).text
    assert "GRAND TOTAL" in csv_text


def test_invalid_budget_category_is_422(client):
    pid = _project_with_schedule(client)
    r = client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={"code": "X", "category": "snacks", "qty": 1, "unit": "flat", "rate": 1},
    )
    assert r.status_code == 422
