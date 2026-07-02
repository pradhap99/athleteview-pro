"""Task 5.5 via the API — deal memos, timecards vs rules engine, payroll export."""

from __future__ import annotations

MEMO = {
    "person": "Alice",
    "legalName": "Alice Q. Performer",
    "union": "SAG-AFTRA",
    "contract": "theatrical",
    "tier": "day_performer",
    "hourlyRate": 100.0,
    "guaranteedHours": 8.0,
    "accountCode": "1300",
    "boxKitRate": 25.0,
    "boxKitCadence": "daily",
    "boxKitAccountablePlan": True,
}

TIMECARD = {
    "person": "Alice",
    "date": "2025-03-10",
    "call": "2025-03-10T07:00:00",
    "wrap": "2025-03-10T17:30:00",
    "meals": [{"start": "2025-03-10T14:00:00", "end": "2025-03-10T14:30:00"}],
    "chain": ["dept_head", "upm"],
}


def _project(client) -> str:
    pid = client.post(
        "/v1/projects",
        json={"title": "Payroll", "type": "scripted", "ppStartDate": "2025-01-01"},
    ).json()["id"]
    r = client.post(f"/v1/projects/{pid}/deal-memos", json=MEMO)
    assert r.status_code == 201, r.text
    return pid


def test_deal_memo_requires_resolvable_rate_card(client):
    pid = client.post("/v1/projects", json={"title": "X"}).json()["id"]
    bad = {**MEMO, "union": "FICTIONAL-GUILD"}
    r = client.post(f"/v1/projects/{pid}/deal-memos", json=bad)
    assert r.status_code == 422 and "no rate card" in r.json()["detail"]


def test_timecard_requires_deal_memo(client):
    pid = client.post("/v1/projects", json={"title": "X"}).json()["id"]
    r = client.post(f"/v1/projects/{pid}/timecards", json=TIMECARD)
    assert r.status_code == 422 and "no deal memo" in r.json()["detail"]


def test_timecard_computes_against_rules_engine(client):
    pid = _project(client)
    r = client.post(f"/v1/projects/{pid}/timecards", json=TIMECARD)
    assert r.status_code == 201, r.text
    computed = r.json()["computed"]
    # 10h worked × $100 base; ×1.5 OT after 8h; 2024 meal ladder 30+40.
    assert computed["base"] == 1000.0
    assert computed["otPremium"] == 100.0
    assert computed["mealPenalties"] == 70.0
    assert computed["total"] == 1170.0
    assert computed["mpvCount"] == 2
    # Defaults to the memo's account code when no splits given.
    assert computed["splits"] == [{"code": "1300", "amount": 1170.0}]
    assert any("sag_aftra.yaml" in e for e in computed["explanations"])


def test_timecard_splits_across_account_codes(client):
    pid = _project(client)
    tc = {**TIMECARD, "splits": [{"code": "1300", "weight": 3}, {"code": "1400", "weight": 1}]}
    computed = client.post(f"/v1/projects/{pid}/timecards", json=tc).json()["computed"]
    assert computed["splits"] == [
        {"code": "1300", "amount": 877.5},
        {"code": "1400", "amount": 292.5},
    ]


def test_timecard_approval_chain_and_recalc_on_read(client):
    pid = _project(client)
    tc_id = client.post(f"/v1/projects/{pid}/timecards", json=TIMECARD).json()["id"]

    # Out-of-order approval refused.
    r = client.post(f"/v1/projects/{pid}/timecards/{tc_id}:approve", json={"role": "upm"})
    assert r.status_code == 409

    client.post(f"/v1/projects/{pid}/timecards/{tc_id}:approve", json={"role": "dept_head"})
    r = client.post(f"/v1/projects/{pid}/timecards/{tc_id}:approve", json={"role": "upm"})
    assert r.json()["status"] == "approved"

    # Read recomputes: a NEW deal memo at a higher rate auto-recalculates the same card.
    client.post(f"/v1/projects/{pid}/deal-memos", json={**MEMO, "hourlyRate": 200.0})
    computed = client.get(f"/v1/projects/{pid}/timecards/{tc_id}").json()["computed"]
    assert computed["base"] == 2000.0  # 10h × new $200 — no stale cache


def test_payroll_export_only_approved_timecards(client):
    pid = _project(client)
    approved_id = client.post(f"/v1/projects/{pid}/timecards", json=TIMECARD).json()["id"]
    client.post(f"/v1/projects/{pid}/timecards/{approved_id}:approve", json={"role": "dept_head"})
    client.post(f"/v1/projects/{pid}/timecards/{approved_id}:approve", json={"role": "upm"})
    # A second, unapproved timecard the next day.
    client.post(
        f"/v1/projects/{pid}/timecards",
        json={
            **TIMECARD,
            "date": "2025-03-11",
            "call": "2025-03-11T07:00:00",
            "wrap": "2025-03-11T15:30:00",
            "meals": [{"start": "2025-03-11T12:00:00", "end": "2025-03-11T12:30:00"}],
        },
    )
    client.post(
        f"/v1/projects/{pid}/start-packets/Alice",
        json={"forms": {"w4": True, "i9": True, "directDeposit": True}},
    )

    export = client.post(
        f"/v1/projects/{pid}/payroll:export",
        json={"provider": "wrapbook", "startDate": "2025-03-01", "endDate": "2025-03-31"},
    ).json()
    assert export["timecardCount"] == 1  # unapproved day excluded
    employee = export["employees"][0]
    assert employee["legalName"] == "Alice Q. Performer"
    assert employee["startPacketComplete"] is True
    assert employee["wageTotal"] == 1170.0
    # Box/kit: separate line, non-taxable under an accountable plan.
    assert employee["boxKit"] == {
        "amount": 25.0,
        "cadence": "daily",
        "taxable": False,
        "costCode": "1300",
    }
    # Wage-type breakdown with cost codes.
    types = {line["wageType"] for line in employee["earnings"]}
    assert types == {"straight", "premiums"}
    assert all(line["costCode"] == "1300" for line in employee["earnings"])
    # Union P&H wage base summary.
    assert export["phWageBaseSummary"] == [
        {"union": "SAG-AFTRA", "contract": "theatrical", "wageBase": 1170.0}
    ]


def test_payroll_export_rejects_unknown_provider(client):
    pid = _project(client)
    r = client.post(
        f"/v1/projects/{pid}/payroll:export",
        json={"provider": "quickbooks", "startDate": "2025-03-01", "endDate": "2025-03-31"},
    )
    assert r.status_code == 422
