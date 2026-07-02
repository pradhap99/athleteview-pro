"""Org-scoped crew/contacts directory + deal-memo templates (task 6.4).

The reusable cross-project database: a person is entered ONCE and reused across shows —
roles, union, agency, default rates, and an **engagement history** assembled from deal
memos across every production in the org (the cross-project memory that makes estimates
smarter show over show). Lives on the per-org event stream (``org:{org_id}``), so it is
shared org-wide and isolated from other tenants.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .events import EventKind, list_org_events, org_stream_id


def fold_contacts(session: Session, org_id: str) -> dict[str, dict[str, Any]]:
    """contact_id -> contact, latest upsert wins per id."""
    contacts: dict[str, dict[str, Any]] = {}
    for ev in list_org_events(session, org_id, kinds=(EventKind.CONTACT_UPSERTED,)):
        if ev.project_id != org_stream_id(org_id):
            continue
        contacts[ev.payload["id"]] = dict(ev.payload)
    return contacts


def fold_templates(session: Session, org_id: str) -> dict[str, dict[str, Any]]:
    templates: dict[str, dict[str, Any]] = {}
    for ev in list_org_events(session, org_id, kinds=(EventKind.DEAL_MEMO_TEMPLATE_SAVED,)):
        if ev.project_id != org_stream_id(org_id):
            continue
        templates[ev.payload["id"]] = dict(ev.payload)
    return templates


def engagement_history(
    session: Session, org_id: str, contact: dict[str, Any]
) -> list[dict[str, Any]]:
    """Every deal memo across the org's shows for this contact — rates carry between shows."""
    history: list[dict[str, Any]] = []
    for ev in list_org_events(session, org_id, kinds=(EventKind.DEAL_MEMO_CREATED,)):
        memo = ev.payload
        if memo.get("contactId") == contact["id"] or memo.get("person") == contact.get("name"):
            history.append(
                {
                    "projectId": ev.project_id,
                    "person": memo.get("person"),
                    "union": memo.get("union"),
                    "contract": memo.get("contract"),
                    "tier": memo.get("tier"),
                    "hourlyRate": memo.get("hourlyRate"),
                    "accountCode": memo.get("accountCode"),
                    "startDate": memo.get("startDate"),
                }
            )
    return history


# Template fields that flow into a deal memo when the memo doesn't set them itself.
TEMPLATE_MEMO_FIELDS = (
    "union",
    "contract",
    "tier",
    "hourlyRate",
    "guaranteedHours",
    "accountCode",
    "boxKitRate",
    "boxKitCadence",
    "boxKitAccountablePlan",
    "boxKitAccountCode",
)


def apply_template(memo: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Merge template defaults into a memo — explicit memo values always win."""
    defaults = template.get("defaults", {})
    merged = dict(memo)
    for field in TEMPLATE_MEMO_FIELDS:
        if merged.get(field) is None and field in defaults:
            merged[field] = defaults[field]
    return merged


REQUIRED_MEMO_FIELDS = ("union", "contract", "tier", "hourlyRate", "guaranteedHours", "accountCode")


def missing_memo_fields(memo: dict[str, Any]) -> list[str]:
    return [f for f in REQUIRED_MEMO_FIELDS if memo.get(f) in (None, "")]
