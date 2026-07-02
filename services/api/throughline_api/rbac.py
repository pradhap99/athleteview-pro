"""Minimal RBAC + tenant isolation.

Every event carries an ``org_id``; a principal may only touch projects in its own org
(tenant isolation). Roles gate writes: viewers read, editors/owners write and — critically
— only editors/owners can *confirm* AI drafts or change diffs (the human-confirms gate).
Dev auth reads the principal from headers; production swaps in real SSO/JWT.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .events import org_of

ROLES = ("owner", "editor", "viewer")
_WRITE_ROLES = frozenset({"owner", "editor"})


class NotFoundError(Exception):
    """Project does not exist (→ 404)."""


class AuthzError(Exception):
    """Principal lacks access or permission (→ 403)."""


@dataclass(frozen=True)
class Principal:
    user_id: str
    org_id: str
    role: str = "editor"

    @property
    def can_write(self) -> bool:
        return self.role in _WRITE_ROLES


def authorize_project(session: Session, principal: Principal, project_id: str) -> str:
    """Ensure the project exists and belongs to the principal's org. Returns the org id."""
    org = org_of(session, project_id)
    if org is None:
        raise NotFoundError(project_id)
    if org != principal.org_id:
        raise AuthzError(f"{principal.user_id} may not access project {project_id}")
    return org


def require_write(principal: Principal) -> None:
    if not principal.can_write:
        raise AuthzError(f"role {principal.role!r} may not write (needs owner/editor)")
