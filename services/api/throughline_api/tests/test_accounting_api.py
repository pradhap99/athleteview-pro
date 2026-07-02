"""Task 5.4 via the API — PO lifecycle → cost report; sign-off chain; petty cash."""

from __future__ import annotations


def _project(client) -> str:
    pid = client.post("/v1/projects", json={"title": "Acct", "type": "scripted"}).json()["id"]
    client.post(
        f"/v1/projects/{pid}/budget/lines",
        json={
            "code": "2100",
            "category": "btl",
            "description": "Grip & electric",
            "qty": 1,
            "unit": "flat",
            "rate": 10_000,
        },
    )
    return pid


def _report_row(client, pid, code):
    report = client.get(f"/v1/projects/{pid}/cost-report").json()
    return next(r for r in report["rows"] if r["code"] == code)


def test_po_lifecycle_moves_cost_report_columns(client):
    pid = _project(client)
    po = client.post(
        f"/v1/projects/{pid}/purchase-orders",
        json={"code": "2100", "vendor": "GripCo", "amount": 4_000},
    ).json()
    po_id = po["id"]

    # Draft PO commits nothing.
    assert _report_row(client, pid, "2100")["committed"] == 0.0

    # Approved-uninvoiced PO = committed cost.
    r = client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:approve")
    assert r.status_code == 200
    row = _report_row(client, pid, "2100")
    assert row["committed"] == 4_000.0 and row["actuals"] == 0.0
    assert row["efc"] == 10_000.0  # ETC absorbs: 0 + 4000 + 6000

    # Goods receipt, then invoice (3-way match) → commitment releases, actual books.
    client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:receive", json={"amount": 4_000})
    r = client.post(
        f"/v1/projects/{pid}/purchase-orders/{po_id}:invoice",
        json={"amount": 4_000, "invoiceRef": "INV-77"},
    )
    assert r.status_code == 200
    row = _report_row(client, pid, "2100")
    assert row["committed"] == 0.0 and row["actuals"] == 4_000.0


def test_three_way_mismatch_is_rejected_with_all_legs(client):
    pid = _project(client)
    po_id = client.post(
        f"/v1/projects/{pid}/purchase-orders",
        json={"code": "2100", "vendor": "GripCo", "amount": 4_000},
    ).json()["id"]
    client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:approve")

    # No goods receipt yet → invoice refused.
    r = client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:invoice", json={"amount": 4_000})
    assert r.status_code == 409 and "no goods receipt" in r.json()["detail"]

    # Receipt disagrees with invoice → refused, all three legs cited.
    client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:receive", json={"amount": 3_500})
    r = client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:invoice", json={"amount": 4_000})
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "4,000.00" in detail and "3,500.00" in detail
    # Nothing booked.
    row = _report_row(client, pid, "2100")
    assert row["actuals"] == 0.0 and row["committed"] == 4_000.0


def test_cancelled_po_releases_commitment(client):
    pid = _project(client)
    po_id = client.post(
        f"/v1/projects/{pid}/purchase-orders",
        json={"code": "2100", "vendor": "GripCo", "amount": 2_000},
    ).json()["id"]
    client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:approve")
    assert _report_row(client, pid, "2100")["committed"] == 2_000.0
    client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:cancel")
    assert _report_row(client, pid, "2100")["committed"] == 0.0


def test_invalid_po_transition_is_409(client):
    pid = _project(client)
    po_id = client.post(
        f"/v1/projects/{pid}/purchase-orders",
        json={"code": "2100", "vendor": "GripCo", "amount": 1_000},
    ).json()["id"]
    # Cannot invoice a draft.
    r = client.post(f"/v1/projects/{pid}/purchase-orders/{po_id}:invoice", json={"amount": 1_000})
    assert r.status_code == 409 and "draft" in r.json()["detail"]


def test_check_request_chain_enforced_in_order(client):
    pid = _project(client)
    req_id = client.post(
        f"/v1/projects/{pid}/check-requests",
        json={
            "code": "2100",
            "amount": 900,
            "payee": "Hardware Store",
            "chain": ["dept_head", "upm"],
        },
    ).json()["id"]

    # UPM cannot sign before the department head.
    r = client.post(f"/v1/projects/{pid}/check-requests/{req_id}:approve", json={"role": "upm"})
    assert r.status_code == 409 and "out-of-order" in r.json()["detail"]

    r = client.post(
        f"/v1/projects/{pid}/check-requests/{req_id}:approve", json={"role": "dept_head"}
    )
    assert r.json()["status"] == "pending"  # chain not yet complete → no actual
    assert _report_row(client, pid, "2100")["actuals"] == 0.0

    r = client.post(f"/v1/projects/{pid}/check-requests/{req_id}:approve", json={"role": "upm"})
    assert r.json()["status"] == "approved"
    assert _report_row(client, pid, "2100")["actuals"] == 900.0  # books on completion

    # No further approvals accepted.
    r = client.post(f"/v1/projects/{pid}/check-requests/{req_id}:approve", json={"role": "upm"})
    assert r.status_code == 409


def test_petty_cash_envelope_reconciles_to_the_cent(client):
    pid = _project(client)
    env_id = client.post(
        f"/v1/projects/{pid}/petty-cash",
        json={"custodian": "Priya", "floatAmount": 500},
    ).json()["id"]
    client.post(
        f"/v1/projects/{pid}/petty-cash/{env_id}/receipts",
        json={"code": "2100", "amount": 123.45, "memo": "gaff tape"},
    )
    client.post(
        f"/v1/projects/{pid}/petty-cash/{env_id}/receipts",
        json={"code": "2100", "amount": 76.55, "memo": "lunch"},
    )
    # Receipts are actuals against their codes.
    assert _report_row(client, pid, "2100")["actuals"] == 200.0

    # Wrong returned cash → 409 naming the shortfall.
    r = client.post(f"/v1/projects/{pid}/petty-cash/{env_id}:reconcile", json={"returnedCash": 250})
    assert r.status_code == 409 and "short" in r.json()["detail"]

    # receipts (200) + returned (300) == float (500) → reconciled.
    r = client.post(f"/v1/projects/{pid}/petty-cash/{env_id}:reconcile", json={"returnedCash": 300})
    assert r.json()["status"] == "reconciled"

    # Reconciled envelopes accept no more receipts.
    r = client.post(
        f"/v1/projects/{pid}/petty-cash/{env_id}/receipts",
        json={"code": "2100", "amount": 5},
    )
    assert r.status_code == 409
