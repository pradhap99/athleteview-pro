"""E-signature with enforced signing order (task 6.4).

One mechanism signs deal memos, releases, and approvals: a request names an ORDERED list
of signers; each signature is an event; out-of-order signing is refused; the request
completes when the last signer signs. The pending view is the reminders feed (who is next,
since when) for the coordinator to chase.
"""

from __future__ import annotations

from typing import Any


class SignatureError(Exception):
    """Signing-order or state violation (→ 409 at the API layer)."""


def require_next_signer(request: dict[str, Any] | None, signer: str) -> dict[str, Any]:
    if request is None:
        raise SignatureError("signature request not found")
    if request.get("status") == "complete":
        raise SignatureError("signature request is already complete")
    signers: list[str] = request.get("signers", [])
    signed: list[dict[str, Any]] = request.get("signed", [])
    expected = signers[len(signed)]
    if signer != expected:
        raise SignatureError(
            f"out-of-order signature: expected {expected!r} next "
            f"(step {len(signed) + 1} of {len(signers)}), got {signer!r}"
        )
    return request


def pending_view(requests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """The reminders feed: incomplete requests with who's next and since when."""
    out: list[dict[str, Any]] = []
    for req in requests.values():
        if req.get("status") == "complete":
            continue
        signers = req.get("signers", [])
        signed = req.get("signed", [])
        last_action = signed[-1]["at"] if signed else req.get("requestedAt", "")
        out.append(
            {
                "id": req["id"],
                "docType": req.get("docType", ""),
                "docRef": req.get("docRef", ""),
                "nextSigner": signers[len(signed)] if len(signed) < len(signers) else None,
                "signedCount": len(signed),
                "totalSigners": len(signers),
                "waitingSince": last_action,
            }
        )
    return sorted(out, key=lambda r: r["waitingSince"])
