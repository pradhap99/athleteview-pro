"""Task 6.4 — cross-project crew DB, templates, e-signature signing order."""

from __future__ import annotations


def test_contact_reused_across_projects_in_same_org(client):
    # Contact entered once (org-scoped)...
    contact = client.post(
        "/v1/org/contacts",
        json={
            "name": "Rosa Vega",
            "roles": ["Key Grip"],
            "union": "IATSE",
            "defaultHourlyRate": 55.0,
        },
    ).json()

    # ...is visible regardless of which project you're working in.
    contacts = client.get("/v1/org/contacts").json()["contacts"]
    assert [c["name"] for c in contacts] == ["Rosa Vega"]

    # Filter by role works.
    assert client.get("/v1/org/contacts", params={"q": "grip"}).json()["contacts"]
    assert not client.get("/v1/org/contacts", params={"q": "gaffer"}).json()["contacts"]

    # Upsert by id updates rather than duplicating.
    client.post(
        "/v1/org/contacts",
        json={"id": contact["id"], "name": "Rosa Vega", "roles": ["Key Grip", "Best Boy"]},
    )
    contacts = client.get("/v1/org/contacts").json()["contacts"]
    assert len(contacts) == 1 and contacts[0]["roles"] == ["Key Grip", "Best Boy"]


def test_contacts_are_tenant_isolated(client):
    client.post("/v1/org/contacts", json={"name": "Org Dev Person"})
    other_org = client.get("/v1/org/contacts", headers={"X-Org-Id": "other-org"}).json()
    assert other_org["contacts"] == []


def test_engagement_history_spans_projects(client):
    contact = client.post("/v1/org/contacts", json={"name": "Rosa Vega"}).json()
    memo = {
        "person": "Rosa Vega",
        "contactId": contact["id"],
        "union": "IATSE",
        "contract": "basic_agreement",
        "tier": "crew",
        "hourlyRate": 55.0,
        "guaranteedHours": 8.0,
        "accountCode": "2100",
    }
    for title, rate in (("Show One", 55.0), ("Show Two", 65.0)):
        pid = client.post("/v1/projects", json={"title": title}).json()["id"]
        client.post(f"/v1/projects/{pid}/deal-memos", json={**memo, "hourlyRate": rate})

    detail = client.get(f"/v1/org/contacts/{contact['id']}").json()
    rates = sorted(h["hourlyRate"] for h in detail["history"])
    assert rates == [55.0, 65.0]  # rates/history carry between shows (the moat)
    assert len({h["projectId"] for h in detail["history"]}) == 2


def test_template_defaults_merge_into_deal_memo(client):
    template = client.post(
        "/v1/org/deal-memo-templates",
        json={
            "name": "IATSE crew day-player",
            "defaults": {
                "union": "IATSE",
                "contract": "basic_agreement",
                "tier": "crew",
                "hourlyRate": 50.0,
                "guaranteedHours": 8.0,
                "accountCode": "2100",
            },
        },
    ).json()
    pid = client.post("/v1/projects", json={"title": "Tpl"}).json()["id"]

    # Memo with only a person + template: template fills the terms.
    r = client.post(
        f"/v1/projects/{pid}/deal-memos",
        json={"person": "Grip A", "templateId": template["id"]},
    )
    assert r.status_code == 201, r.text
    assert r.json()["union"] == "IATSE" and r.json()["hourlyRate"] == 50.0

    # Explicit values beat the template.
    r = client.post(
        f"/v1/projects/{pid}/deal-memos",
        json={"person": "Grip B", "templateId": template["id"], "hourlyRate": 60.0},
    )
    assert r.json()["hourlyRate"] == 60.0


def test_memo_without_terms_or_template_is_422(client):
    pid = client.post("/v1/projects", json={"title": "NoTpl"}).json()["id"]
    r = client.post(f"/v1/projects/{pid}/deal-memos", json={"person": "Nobody"})
    assert r.status_code == 422 and "missing required terms" in r.json()["detail"]


def test_signature_signing_order_enforced(client):
    pid = client.post("/v1/projects", json={"title": "Sig"}).json()["id"]
    req = client.post(
        f"/v1/projects/{pid}/signature-requests",
        json={
            "docType": "deal_memo",
            "docRef": "Rosa Vega",
            "signers": ["Rosa Vega", "UPM", "Accountant"],
        },
    ).json()
    rid = req["id"]

    # UPM cannot sign before the hire.
    r = client.post(f"/v1/projects/{pid}/signature-requests/{rid}:sign", json={"signer": "UPM"})
    assert r.status_code == 409 and "out-of-order" in r.json()["detail"]

    for signer in ("Rosa Vega", "UPM"):
        r = client.post(
            f"/v1/projects/{pid}/signature-requests/{rid}:sign", json={"signer": signer}
        )
        assert r.json()["status"] == "pending"

    # Reminders feed shows who's next.
    pending = client.get(f"/v1/projects/{pid}/signature-requests", params={"pending": True}).json()[
        "pending"
    ]
    assert pending[0]["nextSigner"] == "Accountant"
    assert pending[0]["signedCount"] == 2

    r = client.post(
        f"/v1/projects/{pid}/signature-requests/{rid}:sign", json={"signer": "Accountant"}
    )
    assert r.json()["status"] == "complete"

    # Complete requests leave the reminders feed and refuse more signatures.
    assert (
        client.get(f"/v1/projects/{pid}/signature-requests", params={"pending": True}).json()[
            "pending"
        ]
        == []
    )
    r = client.post(
        f"/v1/projects/{pid}/signature-requests/{rid}:sign", json={"signer": "Accountant"}
    )
    assert r.status_code == 409
