"""Production accounting workflows (task 5.4): POs, check requests, petty cash.

Business rules live here as pure functions the endpoints call BEFORE appending events;
the graph fold stays mechanical. The cost-report linkage is the point:

* an **approved, uninvoiced PO is a committed cost** (shows in the Committed column);
* invoicing performs a **3-way match** (PO amount ⇄ goods receipt ⇄ invoice) and, on
  success, releases the commitment and books the actual;
* **check requests** route through an ordered sign-off chain (e.g. dept head → UPM →
  accountant) and book an actual only when the chain completes;
* **petty cash** uses the envelope model: receipts + returned cash must reconcile to the
  issued float, to the cent.

Amounts are user data (never code constants). All state transitions are events, so the
full audit trail and Time Machine come for free.
"""

from __future__ import annotations

from typing import Any


class AccountingError(Exception):
    """A business-rule violation (→ 409 at the API layer)."""


def _money(x: Any) -> float:
    return round(float(x), 2)


# ---- purchase orders ---------------------------------------------------------


def require_po_transition(po: dict[str, Any] | None, action: str) -> dict[str, Any]:
    """Validate a PO lifecycle transition; returns the PO or raises."""
    if po is None:
        raise AccountingError("purchase order not found")
    status = po.get("status")
    allowed = {
        "approve": ("draft",),
        "receive": ("approved",),
        "invoice": ("approved",),
        "cancel": ("draft", "approved"),
    }[action]
    if status not in allowed:
        raise AccountingError(
            f"cannot {action} a PO in status {status!r} (allowed from: {', '.join(allowed)})"
        )
    return po


def check_three_way_match(po: dict[str, Any], invoice_amount: float) -> None:
    """3-way match: PO amount ⇄ goods receipt ⇄ invoice must agree to the cent.

    A mismatch is surfaced with all three legs (explainability) — never silently booked.
    """
    po_amount = _money(po["amount"])
    received = po.get("receivedAmount")
    if received is None:
        raise AccountingError(
            "3-way match failed: no goods receipt recorded for this PO (receive it first)"
        )
    received = _money(received)
    invoice = _money(invoice_amount)
    if not (po_amount == received == invoice):
        raise AccountingError(
            "3-way match failed: "
            f"PO {po_amount:,.2f} ⇄ received {received:,.2f} ⇄ invoice {invoice:,.2f} "
            "must agree; correct the discrepancy or issue a change order"
        )


# ---- check requests ----------------------------------------------------------


def require_next_approver(req: dict[str, Any] | None, role: str) -> dict[str, Any]:
    """Enforce the ordered sign-off chain; returns the request or raises."""
    if req is None:
        raise AccountingError("check request not found")
    if req.get("status") == "approved":
        raise AccountingError("check request is already fully approved")
    chain: list[str] = req.get("chain", [])
    approvals: list[dict[str, Any]] = req.get("approvals", [])
    if len(approvals) >= len(chain):
        raise AccountingError("approval chain already complete")
    expected = chain[len(approvals)]
    if role != expected:
        raise AccountingError(
            f"out-of-order approval: expected {expected!r} next "
            f"(step {len(approvals) + 1} of {len(chain)}), got {role!r}"
        )
    return req


# ---- petty cash ---------------------------------------------------------------


def check_reconciliation(envelope: dict[str, Any] | None, returned_cash: float) -> float:
    """Receipts + returned cash must equal the float, to the cent. Returns the delta 0.0."""
    if envelope is None:
        raise AccountingError("petty-cash envelope not found")
    if envelope.get("status") == "reconciled":
        raise AccountingError("envelope is already reconciled")
    float_amount = _money(envelope["float"])
    receipts = _money(sum(_money(r["amount"]) for r in envelope.get("receipts", [])))
    returned = _money(returned_cash)
    delta = _money(float_amount - receipts - returned)
    if delta != 0.0:
        kind = "short" if delta > 0.0 else "over"
        raise AccountingError(
            f"reconciliation failed ({kind} {abs(delta):,.2f}): float {float_amount:,.2f} "
            f"≠ receipts {receipts:,.2f} + returned {returned:,.2f}"
        )
    return delta
