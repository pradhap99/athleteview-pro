"""FastAPI app — the graph API (tasks 0.2, 1.1, 2.1/2.2 seams).

Every write appends to the event log; reads are projections; downstream effects are always
*proposed diffs* a human confirms. Dev auth reads the principal from ``X-User-Id`` /
``X-Org-Id`` / ``X-Role`` headers; production swaps in SSO/JWT.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session, sessionmaker

from throughline_ml.scheduler import Scene as SchedScene
from throughline_ml.scheduler import SchedulingProblem, solve_schedule

from .accounting import (
    AccountingError,
    check_reconciliation,
    check_three_way_match,
    require_next_approver,
    require_po_transition,
)
from .budget import build_cost_report, compute_hot_costs, line_from_payload
from .budget.model import BudgetLine, Fringe
from .callsheets import affected_recipients, build_call_sheet
from .colored_pages import next_color, revision_slug
from .config import settings
from .copilot import nudges_for
from .db import init_db, make_engine, make_session_factory
from .events import EventKind, append_event, list_events, org_of, org_stream_id
from .exhibit_g import build_exhibit_g, render_exhibit_g_text
from .graph import GraphState, reconstruct
from .ingest import ingest_script
from .interop import to_aicp, to_aicp_csv
from .locations import company_moves, day_info, expiry_alerts
from .org_directory import (
    apply_template,
    engagement_history,
    fold_contacts,
    fold_templates,
    missing_memo_fields,
)
from .payroll import build_payroll_export
from .propagation import (
    apply_change,
    diff_to_dict,
    propose_reschedule,
    propose_schedule,
    reject_change,
)
from .rbac import AuthzError, NotFoundError, Principal, authorize_project, require_write
from .revision import propose_revision
from .rules import RulesEngine
from .schemas import (
    BudgetLineReq,
    CallSheetAckReq,
    CallSheetPublishReq,
    CheckRequestApproveReq,
    CheckRequestCreateReq,
    ContactReq,
    CreateProjectReq,
    DealMemoReq,
    DealMemoTemplateReq,
    EtcReq,
    ExhibitGSignReq,
    ImportScriptReq,
    LedgerEntryReq,
    LocationDocReq,
    LocationReq,
    OptimizeReq,
    PayrollExportReq,
    PettyCashIssueReq,
    PettyCashReceiptReq,
    PettyCashReconcileReq,
    PoCreateReq,
    PoInvoiceReq,
    PoReceiveReq,
    RescheduleChangeReq,
    RevisionReleaseReq,
    ScriptDiffReq,
    SidesLinkReq,
    SignatureRequestReq,
    SignReq,
    StartPacketReq,
    TimecardApproveReq,
    TimecardSubmitReq,
)
from .sides import (
    SidesError,
    check_link_access,
    generate_sides,
    render_sides_text,
    tracking_summary,
    watermark,
)
from .signatures import SignatureError, pending_view, require_next_signer
from .timecard_service import (
    TimecardError,
    calc_to_dict,
    compute_for_state,
    daywork_from_timecard,
    memo_for,
    resolve_card,
)


def serialize_graph(state: GraphState) -> dict[str, Any]:
    return {
        "projectId": state.project_id,
        "title": state.title,
        "type": state.project_type,
        "atEventId": state.at_event_id,
        "scenes": [
            {
                "id": s.id,
                "number": s.number,
                "intExt": s.int_ext,
                "location": s.location,
                "timeOfDay": s.time_of_day,
                "heading": s.heading,
                "pageEighths": s.page_eighths,
                "characters": s.characters,
                "day": state.assignments.get(s.id),
            }
            for s in state.scenes.values()
        ],
        "elements": [
            {
                "id": e.id,
                "etype": e.etype,
                "name": e.name,
                "confidence": e.confidence,
                "source": e.source,
                "status": e.status,
                "needsReview": e.needs_review,
                "sceneIds": e.scene_ids,
            }
            for e in state.elements.values()
        ],
        "dood": state.dood,
        "numDays": state.num_days,
        "budgetLines": state.budget_lines,
        "proposedDiffs": [diff_to_dict(d) for d in state.proposed_diffs.values()],
    }


def create_app(session_factory: sessionmaker | None = None) -> FastAPI:
    if session_factory is None:
        engine = make_engine(settings.database_url)
        init_db(engine)
        session_factory = make_session_factory(engine)

    app = FastAPI(title=settings.app_name, version=settings.version)
    app.state.session_factory = session_factory
    rules_engine = RulesEngine()  # loads the effective-dated rate-card tables once

    def get_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_principal(
        x_user_id: str = Header(default="dev-user"),
        x_org_id: str = Header(default="org-dev"),
        x_role: str = Header(default="editor"),
    ) -> Principal:
        return Principal(user_id=x_user_id, org_id=x_org_id, role=x_role)

    def _authz(session: Session, principal: Principal, project_id: str) -> str:
        try:
            return authorize_project(session, principal, project_id)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="project not found") from None
        except AuthzError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from None

    def _require_write(principal: Principal) -> None:
        try:
            require_write(principal)
        except AuthzError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from None

    # -- health ---------------------------------------------------------------

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": settings.version}

    # -- projects -------------------------------------------------------------

    @app.post("/v1/projects", status_code=201)
    def create_project(
        body: CreateProjectReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_write(principal)
        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        append_event(
            session,
            org_id=principal.org_id,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.PROJECT_CREATED,
            payload={"title": body.title, "type": body.type, "ppStartDate": body.ppStartDate},
        )
        session.commit()
        return {"id": project_id, "title": body.title, "type": body.type}

    # -- script ingest (task 1.1) --------------------------------------------

    @app.post("/v1/projects/{project_id}/scripts:import")
    def import_script(
        project_id: str,
        body: ImportScriptReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        summary = ingest_script(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            text=body.text,
            fmt=body.format,
        )
        session.commit()
        return summary

    # -- graph snapshot + Time Machine (task 0.2) ----------------------------

    @app.get("/v1/projects/{project_id}/graph")
    def get_graph(
        project_id: str,
        at: int | None = Query(default=None, description="reconstruct as of this event id"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        return serialize_graph(reconstruct(session, project_id, at_event_id=at))

    @app.get("/v1/projects/{project_id}/events")
    def get_events(
        project_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        events = list_events(session, project_id)
        return {
            "events": [
                {"id": e.id, "seq": e.seq, "kind": e.kind, "actor": e.actor, "payload": e.payload}
                for e in events
            ]
        }

    # -- human-confirms gate on drafts (task 1.3 seam) -----------------------

    @app.post("/v1/projects/{project_id}/elements/{element_id}:confirm")
    def confirm_element(
        project_id: str,
        element_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        if element_id not in state.elements:
            raise HTTPException(status_code=404, detail="element not found")
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.ELEMENT_CONFIRMED,
            payload={"id": element_id},
        )
        session.commit()
        el = reconstruct(session, project_id).elements[element_id]
        return {"id": el.id, "status": el.status, "needsReview": el.needs_review}

    @app.post("/v1/projects/{project_id}/elements/{element_id}:reject")
    def reject_element(
        project_id: str,
        element_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        if element_id not in state.elements:
            raise HTTPException(status_code=404, detail="element not found")
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.ELEMENT_REJECTED,
            payload={"id": element_id},
        )
        session.commit()
        el = reconstruct(session, project_id).elements[element_id]
        return {"id": el.id, "status": el.status}

    # -- reactive propagation: propose / confirm / reject (task 2.2) ---------

    @app.post("/v1/projects/{project_id}/changes")
    def propose_change(
        project_id: str,
        body: RescheduleChangeReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        if body.type != "reschedule_scene":
            raise HTTPException(status_code=400, detail=f"unsupported change type {body.type!r}")
        try:
            diff = propose_reschedule(
                state,
                diff_id=f"diff-{uuid.uuid4().hex[:12]}",
                scene_id=body.sceneId,
                to_day=body.toDay,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from None
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.CHANGE_PROPOSED,
            payload=diff_to_dict(diff),
        )
        session.commit()
        return diff_to_dict(diff)

    @app.post("/v1/projects/{project_id}/changes/{diff_id}:confirm")
    def confirm_change(
        project_id: str,
        diff_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        diff = state.proposed_diffs.get(diff_id)
        if diff is None:
            raise HTTPException(status_code=404, detail="diff not found")
        if diff.status != "pending":
            raise HTTPException(status_code=409, detail=f"diff already {diff.status}")
        event_ids = apply_change(
            session, org_id=org, project_id=project_id, actor=principal.user_id, diff=diff
        )
        session.commit()
        return {"applied": True, "eventIds": event_ids, "headEventId": event_ids[-1]}

    @app.post("/v1/projects/{project_id}/changes/{diff_id}:reject")
    def reject_change_endpoint(
        project_id: str,
        diff_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        diff = state.proposed_diffs.get(diff_id)
        if diff is None:
            raise HTTPException(status_code=404, detail="diff not found")
        reject_change(
            session, org_id=org, project_id=project_id, actor=principal.user_id, diff_id=diff_id
        )
        session.commit()
        return {"rejected": True}

    # -- script revision → proposed diff (task 1.3) --------------------------

    @app.post("/v1/projects/{project_id}/scripts:diff")
    def script_revision_diff(
        project_id: str,
        body: ScriptDiffReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        diff, detail = propose_revision(
            state,
            diff_id=f"diff-{uuid.uuid4().hex[:12]}",
            new_text=body.text,
            fmt=body.format,
        )
        if not diff.changes:
            return {"diff": None, "detail": detail, "summary": diff.summary}
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.CHANGE_PROPOSED,
            payload=diff_to_dict(diff),
        )
        session.commit()
        return {"diff": diff_to_dict(diff), "detail": detail}

    # -- budget (tasks 2.3 / 5.3) ---------------------------------------------

    @app.post("/v1/projects/{project_id}/budget/lines", status_code=201)
    def add_budget_line(
        project_id: str,
        body: BudgetLineReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        try:
            line = BudgetLine(
                id=f"bl-{uuid.uuid4().hex[:12]}",
                code=body.code,
                category=body.category,
                description=body.description,
                qty=body.qty,
                unit=body.unit,
                rate=body.rate,
                fringes=[Fringe(f.name, f.ratePct, f.cap) for f in body.fringes],
                driver=body.driver,
                aicp_section=body.aicpSection,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.BUDGET_LINE_ADDED,
            payload=line.to_payload(),
        )
        session.commit()
        return line.to_payload()

    @app.post("/v1/projects/{project_id}/budget/actuals", status_code=201)
    def record_actual(
        project_id: str,
        body: LedgerEntryReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        ev = append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.ACTUAL_RECORDED,
            payload={"code": body.code, "amount": body.amount, "memo": body.memo},
        )
        session.commit()
        return {"eventId": ev.id, "code": body.code, "amount": body.amount}

    @app.post("/v1/projects/{project_id}/budget/commitments", status_code=201)
    def record_commitment(
        project_id: str,
        body: LedgerEntryReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        ev = append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.COMMITMENT_RECORDED,
            payload={"code": body.code, "amount": body.amount, "memo": body.memo},
        )
        session.commit()
        return {"eventId": ev.id, "code": body.code, "amount": body.amount}

    @app.post("/v1/projects/{project_id}/budget/etc")
    def set_etc(
        project_id: str,
        body: EtcReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)  # ETC override is a human judgment call
        ev = append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.ETC_SET,
            payload={"code": body.code, "amount": body.amount},
        )
        session.commit()
        return {"eventId": ev.id, "code": body.code, "etc": body.amount}

    @app.get("/v1/projects/{project_id}/cost-report")
    def cost_report(
        project_id: str,
        at: int | None = Query(default=None),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id, at_event_id=at)
        report = build_cost_report(
            [line_from_payload(p) for p in state.budget_lines],
            actuals=state.actuals,
            commitments=state.commitments,
            etc_overrides=state.etc_overrides,
        )
        return {
            "atEventId": state.at_event_id,
            "rows": [r.__dict__ for r in report.rows],
            "byCategory": report.by_category,
            "totals": report.totals,
        }

    @app.post("/v1/projects/{project_id}/budget:export")
    def export_budget(
        project_id: str,
        format: str = Query(default="aicp", pattern="^(aicp|csv)$"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> Any:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        lines = [line_from_payload(p) for p in state.budget_lines]
        if format == "csv":
            return PlainTextResponse(to_aicp_csv(lines), media_type="text/csv")
        return to_aicp(lines, title=state.title)

    # -- POs / check requests / petty cash (task 5.4) -------------------------

    def _write_ctx(session: Session, principal: Principal, project_id: str) -> str:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        return org

    def _commit_event(
        session: Session, org: str, project_id: str, actor: str, kind: str, payload: dict
    ) -> int:
        ev = append_event(
            session, org_id=org, project_id=project_id, actor=actor, kind=kind, payload=payload
        )
        session.commit()
        return ev.id

    @app.post("/v1/projects/{project_id}/purchase-orders", status_code=201)
    def create_po(
        project_id: str,
        body: PoCreateReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        po_id = f"po-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.PO_CREATED,
            {
                "id": po_id,
                "code": body.code,
                "vendor": body.vendor,
                "amount": body.amount,
                "memo": body.memo,
            },
        )
        return {"id": po_id, "status": "draft"}

    def _po_action(
        session: Session, principal: Principal, project_id: str, po_id: str, action: str
    ) -> dict[str, Any]:
        """Shared PO transition guard; returns (org, po)."""
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            po = require_po_transition(state.purchase_orders.get(po_id), action)
        except AccountingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        return {"org": org, "po": po}

    @app.post("/v1/projects/{project_id}/purchase-orders/{po_id}:approve")
    def approve_po(
        project_id: str,
        po_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        ctx = _po_action(session, principal, project_id, po_id, "approve")
        _commit_event(
            session,
            ctx["org"],
            project_id,
            principal.user_id,
            EventKind.PO_APPROVED,
            {"id": po_id},
        )
        return {"id": po_id, "status": "approved", "committed": ctx["po"]["amount"]}

    @app.post("/v1/projects/{project_id}/purchase-orders/{po_id}:receive")
    def receive_po(
        project_id: str,
        po_id: str,
        body: PoReceiveReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        ctx = _po_action(session, principal, project_id, po_id, "receive")
        _commit_event(
            session,
            ctx["org"],
            project_id,
            principal.user_id,
            EventKind.PO_RECEIVED,
            {"id": po_id, "amount": body.amount},
        )
        return {"id": po_id, "receivedAmount": body.amount}

    @app.post("/v1/projects/{project_id}/purchase-orders/{po_id}:invoice")
    def invoice_po(
        project_id: str,
        po_id: str,
        body: PoInvoiceReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        ctx = _po_action(session, principal, project_id, po_id, "invoice")
        try:
            check_three_way_match(ctx["po"], body.amount)
        except AccountingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        _commit_event(
            session,
            ctx["org"],
            project_id,
            principal.user_id,
            EventKind.PO_INVOICED,
            {"id": po_id, "amount": body.amount, "invoiceRef": body.invoiceRef},
        )
        return {"id": po_id, "status": "invoiced", "actual": body.amount}

    @app.post("/v1/projects/{project_id}/purchase-orders/{po_id}:cancel")
    def cancel_po(
        project_id: str,
        po_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        ctx = _po_action(session, principal, project_id, po_id, "cancel")
        _commit_event(
            session,
            ctx["org"],
            project_id,
            principal.user_id,
            EventKind.PO_CANCELLED,
            {"id": po_id},
        )
        return {"id": po_id, "status": "cancelled"}

    @app.post("/v1/projects/{project_id}/check-requests", status_code=201)
    def create_check_request(
        project_id: str,
        body: CheckRequestCreateReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        req_id = f"cr-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.CHECK_REQUEST_CREATED,
            {
                "id": req_id,
                "code": body.code,
                "amount": body.amount,
                "payee": body.payee,
                "chain": body.chain,
            },
        )
        return {"id": req_id, "status": "pending", "chain": body.chain}

    @app.post("/v1/projects/{project_id}/check-requests/{req_id}:approve")
    def approve_check_request(
        project_id: str,
        req_id: str,
        body: CheckRequestApproveReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            require_next_approver(state.check_requests.get(req_id), body.role)
        except AccountingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.CHECK_REQUEST_APPROVED,
            {"id": req_id, "approver": principal.user_id, "role": body.role},
        )
        req = reconstruct(session, project_id).check_requests[req_id]
        return {"id": req_id, "status": req["status"], "approvals": req["approvals"]}

    @app.post("/v1/projects/{project_id}/petty-cash", status_code=201)
    def issue_petty_cash(
        project_id: str,
        body: PettyCashIssueReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        env_id = f"pc-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.PETTY_CASH_ISSUED,
            {"id": env_id, "custodian": body.custodian, "float": body.floatAmount},
        )
        return {"id": env_id, "custodian": body.custodian, "float": body.floatAmount}

    @app.post("/v1/projects/{project_id}/petty-cash/{env_id}/receipts", status_code=201)
    def record_petty_cash_receipt(
        project_id: str,
        env_id: str,
        body: PettyCashReceiptReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        envelope = state.petty_cash.get(env_id)
        if envelope is None:
            raise HTTPException(status_code=404, detail="petty-cash envelope not found")
        if envelope["status"] == "reconciled":
            raise HTTPException(status_code=409, detail="envelope is already reconciled")
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.PETTY_CASH_RECEIPT,
            {"envelopeId": env_id, "code": body.code, "amount": body.amount, "memo": body.memo},
        )
        return {"envelopeId": env_id, "amount": body.amount}

    @app.post("/v1/projects/{project_id}/petty-cash/{env_id}:reconcile")
    def reconcile_petty_cash(
        project_id: str,
        env_id: str,
        body: PettyCashReconcileReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            check_reconciliation(state.petty_cash.get(env_id), body.returnedCash)
        except AccountingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.PETTY_CASH_RECONCILED,
            {"envelopeId": env_id, "returnedCash": body.returnedCash},
        )
        return {"envelopeId": env_id, "status": "reconciled"}

    # -- deal memos / timecards / Exhibit G / payroll (task 5.5) ---------------

    @app.post("/v1/projects/{project_id}/deal-memos", status_code=201)
    def create_deal_memo(
        project_id: str,
        body: DealMemoReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        payload = body.model_dump()

        # Merge org template defaults (explicit memo values win) — task 6.4.
        if body.templateId:
            template = fold_templates(session, org).get(body.templateId)
            if template is None:
                raise HTTPException(status_code=404, detail="deal-memo template not found")
            payload = apply_template(payload, template)
        # Link to the org crew DB: fill names from the contact, feed cross-show history.
        if body.contactId:
            contact = fold_contacts(session, org).get(body.contactId)
            if contact is None:
                raise HTTPException(status_code=404, detail="contact not found")
            if not payload.get("legalName"):
                payload["legalName"] = contact.get("name", payload["person"])

        missing = missing_memo_fields(payload)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"deal memo missing required terms: {', '.join(missing)} "
                "(set them or supply a templateId that does)",
            )
        # Validate the union/contract/tier resolves to a real rate card up front.
        state = reconstruct(session, project_id)
        try:
            resolve_card(
                rules_engine, state, payload, body.startDate or dt.date.today().isoformat()
            )
        except LookupError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        _commit_event(
            session, org, project_id, principal.user_id, EventKind.DEAL_MEMO_CREATED, payload
        )
        return {
            "person": payload["person"],
            "union": payload["union"],
            "hourlyRate": payload["hourlyRate"],
        }

    @app.post("/v1/projects/{project_id}/start-packets/{person}")
    def update_start_packet(
        project_id: str,
        person: str,
        body: StartPacketReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.START_PACKET_UPDATED,
            {"person": person, "forms": body.forms},
        )
        packet = reconstruct(session, project_id).start_packets[person]
        return {"person": person, "forms": packet["forms"]}

    @app.post("/v1/projects/{project_id}/timecards", status_code=201)
    def submit_timecard(
        project_id: str,
        body: TimecardSubmitReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        tc_id = f"tc-{uuid.uuid4().hex[:12]}"
        payload = {"id": tc_id, **body.model_dump()}
        try:
            # Validate now (memo exists, datetimes parse, card resolves) — compute on read.
            memo_for(state, body.person)
            daywork_from_timecard(payload)
            calc = compute_for_state(state, rules_engine, payload)
        except TimecardError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except LookupError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        _commit_event(
            session, org, project_id, principal.user_id, EventKind.TIMECARD_SUBMITTED, payload
        )
        return {"id": tc_id, "status": "submitted", "computed": calc_to_dict(calc)}

    @app.post("/v1/projects/{project_id}/timecards/{tc_id}:approve")
    def approve_timecard(
        project_id: str,
        tc_id: str,
        body: TimecardApproveReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            require_next_approver(state.timecards.get(tc_id), body.role)
        except AccountingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.TIMECARD_APPROVED,
            {"id": tc_id, "approver": principal.user_id, "role": body.role},
        )
        tc = reconstruct(session, project_id).timecards[tc_id]
        return {"id": tc_id, "status": tc["status"], "approvals": tc["approvals"]}

    @app.get("/v1/projects/{project_id}/timecards/{tc_id}")
    def get_timecard(
        project_id: str,
        tc_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        tc = state.timecards.get(tc_id)
        if tc is None:
            raise HTTPException(status_code=404, detail="timecard not found")
        # Computed fresh on every read — memo/rate-card changes auto-recalculate.
        calc = compute_for_state(state, rules_engine, tc)
        return {**tc, "computed": calc_to_dict(calc)}

    @app.get("/v1/projects/{project_id}/exhibit-g")
    def get_exhibit_g(
        project_id: str,
        date: str = Query(..., description="shoot date (ISO)"),
        format: str = Query(default="json", pattern="^(json|text)$"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> Any:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        rows = build_exhibit_g(state, rules_engine, date)
        if format == "text":
            return PlainTextResponse(render_exhibit_g_text(rows, production=state.title))
        return {"date": date, "rows": rows}

    @app.post("/v1/projects/{project_id}/exhibit-g/{person}:sign")
    def sign_exhibit_g(
        project_id: str,
        person: str,
        body: ExhibitGSignReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        if not any(
            tc["person"] == person and tc["date"] == body.date for tc in state.timecards.values()
        ):
            raise HTTPException(status_code=404, detail="no timecard for that person/date")
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.EXHIBIT_G_SIGNED,
            {
                "person": person,
                "date": body.date,
                "signedBy": principal.user_id,
                "signedAt": dt.datetime.now(dt.UTC).isoformat(),
            },
        )
        return {"person": person, "date": body.date, "signed": True}

    @app.get("/v1/projects/{project_id}/hot-costs")
    def hot_costs(
        project_id: str,
        date: str = Query(..., description="prior shoot date (ISO)"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        """Daily hot costs regenerated from the date's timecards (the Exhibit G feed)."""
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        day_tcs = [tc for tc in state.timecards.values() if tc.get("date") == date]
        if not day_tcs:
            return {
                "date": date,
                "lines": [],
                "totalBudgeted": 0.0,
                "totalActual": 0.0,
                "totalVariance": 0.0,
            }
        # Group by resolved rate card so mixed-union days price correctly.
        lines = []
        for tc in day_tcs:
            memo = memo_for(state, tc["person"])
            card = resolve_card(rules_engine, state, memo, tc["date"])
            budgeted = round(float(memo["hourlyRate"]) * float(memo["guaranteedHours"]), 2)
            report = compute_hot_costs(
                [daywork_from_timecard(tc)],
                engine=rules_engine,
                card=card,
                hourly_rates={tc["person"]: float(memo["hourlyRate"])},
                budgeted={tc["person"]: budgeted},
            )
            lines.extend(report.lines)
        return {
            "date": date,
            "lines": [line.__dict__ for line in lines],
            "totalBudgeted": round(sum(line.budgeted for line in lines), 2),
            "totalActual": round(sum(line.total for line in lines), 2),
            "totalVariance": round(sum(line.variance for line in lines), 2),
        }

    @app.post("/v1/projects/{project_id}/payroll:export")
    def payroll_export(
        project_id: str,
        body: PayrollExportReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            return build_payroll_export(
                state,
                rules_engine,
                provider=body.provider,
                start_date=body.startDate,
                end_date=body.endDate,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

    # -- sides + watermarked distribution (task 6.2) ----------------------------

    @app.post("/v1/projects/{project_id}/sides/links", status_code=201)
    def issue_sides_link(
        project_id: str,
        body: SidesLinkReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        pages = generate_sides(state, day_index=body.dayIndex, character=body.character)
        if not pages:
            raise HTTPException(
                status_code=422,
                detail=f"no scenes scheduled on day {body.dayIndex}"
                + (f" featuring {body.character!r}" if body.character else ""),
            )
        link_id = f"sl-{uuid.uuid4().hex[:16]}"  # the token IS the credential
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.SIDES_LINK_ISSUED,
            {"id": link_id, **body.model_dump()},
        )
        return {
            "id": link_id,
            "pageCount": len(pages),
            "viewPath": f"/v1/projects/{project_id}/sides/links/{link_id}/view",
        }

    @app.post("/v1/projects/{project_id}/sides/links/{link_id}:revoke")
    def revoke_sides_link(
        project_id: str,
        link_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        if link_id not in state.sides_links:
            raise HTTPException(status_code=404, detail="sides link not found")
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.SIDES_LINK_REVOKED,
            {"id": link_id},
        )
        return {"id": link_id, "revoked": True}

    @app.get("/v1/projects/{project_id}/sides/links/{link_id}/view")
    def view_sides(
        project_id: str,
        link_id: str,
        format: str = Query(default="json", pattern="^(json|text)$"),
        session: Session = Depends(get_session),
    ) -> Any:
        """Capability-URL access: the link token is the credential (viewers need no seat).

        Expiry/revocation are checked on every view; each open appends a delivery event.
        """
        org = org_of(session, project_id)
        if org is None:
            raise HTTPException(status_code=404, detail="project not found")
        state = reconstruct(session, project_id)
        try:
            link = check_link_access(state.sides_links.get(link_id), now=dt.datetime.now())
        except SidesError as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from None
        pages = generate_sides(state, day_index=link["dayIndex"], character=link.get("character"))
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=f"link:{link_id}",
            kind=EventKind.SIDES_OPENED,
            payload={"id": link_id, "at": dt.datetime.now(dt.UTC).isoformat()},
        )
        session.commit()
        if format == "text":
            return PlainTextResponse(render_sides_text(pages, link))
        return {
            "watermark": watermark(link),
            "allowDownload": link.get("allowDownload", False),
            "allowPrint": link.get("allowPrint", False),
            "pages": [{**page, "watermark": watermark(link)} for page in pages],
        }

    @app.post("/v1/projects/{project_id}/sides/links/{link_id}:acknowledge")
    def acknowledge_sides(
        project_id: str,
        link_id: str,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        """Recipient acknowledgment — also capability-based (no seat required)."""
        org = org_of(session, project_id)
        if org is None:
            raise HTTPException(status_code=404, detail="project not found")
        state = reconstruct(session, project_id)
        try:
            check_link_access(state.sides_links.get(link_id), now=dt.datetime.now())
        except SidesError as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from None
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=f"link:{link_id}",
            kind=EventKind.SIDES_ACKNOWLEDGED,
            payload={"id": link_id, "at": dt.datetime.now(dt.UTC).isoformat()},
        )
        session.commit()
        return {"id": link_id, "acknowledged": True}

    @app.get("/v1/projects/{project_id}/sides/tracking")
    def sides_tracking(
        project_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        rows = tracking_summary(state)
        return {"recipients": rows, "chase": [r for r in rows if r["needsChase"]]}

    # -- locations (task 6.3) ----------------------------------------------------

    @app.post("/v1/projects/{project_id}/locations", status_code=201)
    def add_location(
        project_id: str,
        body: LocationReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        loc_id = f"loc-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.LOCATION_ADDED,
            {"id": loc_id, **body.model_dump()},
        )
        return {"id": loc_id, "name": body.name}

    @app.post("/v1/projects/{project_id}/locations/{loc_id}/documents", status_code=201)
    def add_location_document(
        project_id: str,
        loc_id: str,
        body: LocationDocReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        if loc_id not in state.locations:
            raise HTTPException(status_code=404, detail="location not found")
        if body.type not in ("release", "permit", "coi"):
            raise HTTPException(status_code=422, detail=f"unknown document type {body.type!r}")
        doc_id = f"doc-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.LOCATION_DOC_ADDED,
            {"locationId": loc_id, "docId": doc_id, **body.model_dump()},
        )
        return {"docId": doc_id, "locationId": loc_id, "type": body.type}

    @app.get("/v1/projects/{project_id}/locations/{loc_id}/day-info")
    def location_day_info(
        project_id: str,
        loc_id: str,
        date: str = Query(..., description="ISO date"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        location = state.locations.get(loc_id)
        if location is None:
            raise HTTPException(status_code=404, detail="location not found")
        return day_info(location, dt.date.fromisoformat(date))

    @app.get("/v1/projects/{project_id}/locations:alerts")
    def location_alerts(
        project_id: str,
        within_days: int = Query(default=30, ge=0),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        alerts = expiry_alerts(state, today=dt.date.today(), within_days=within_days)
        return {"withinDays": within_days, "alerts": alerts}

    @app.get("/v1/projects/{project_id}/company-moves")
    def get_company_moves(
        project_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        return {"moves": company_moves(state)}

    # -- org crew directory + templates (task 6.4) ------------------------------
    # Cross-project by design: contacts/templates live on the org stream, so a person is
    # entered once and reused across every show in the org (never re-enter crew).

    @app.post("/v1/org/contacts", status_code=201)
    def upsert_contact(
        body: ContactReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_write(principal)
        contact_id = body.id or f"ct-{uuid.uuid4().hex[:12]}"
        payload = {**body.model_dump(), "id": contact_id}
        append_event(
            session,
            org_id=principal.org_id,
            project_id=org_stream_id(principal.org_id),
            actor=principal.user_id,
            kind=EventKind.CONTACT_UPSERTED,
            payload=payload,
        )
        session.commit()
        return {"id": contact_id, "name": body.name}

    @app.get("/v1/org/contacts")
    def list_contacts(
        q: str | None = Query(default=None, description="name/role filter"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        contacts = list(fold_contacts(session, principal.org_id).values())
        if q:
            needle = q.lower()
            contacts = [
                c
                for c in contacts
                if needle in c.get("name", "").lower()
                or any(needle in role.lower() for role in c.get("roles", []))
            ]
        return {"contacts": sorted(contacts, key=lambda c: c.get("name", ""))}

    @app.get("/v1/org/contacts/{contact_id}")
    def get_contact(
        contact_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        contact = fold_contacts(session, principal.org_id).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="contact not found")
        history = engagement_history(session, principal.org_id, contact)
        return {**contact, "history": history}

    @app.post("/v1/org/deal-memo-templates", status_code=201)
    def save_template(
        body: DealMemoTemplateReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _require_write(principal)
        template_id = f"tpl-{uuid.uuid4().hex[:12]}"
        append_event(
            session,
            org_id=principal.org_id,
            project_id=org_stream_id(principal.org_id),
            actor=principal.user_id,
            kind=EventKind.DEAL_MEMO_TEMPLATE_SAVED,
            payload={"id": template_id, "name": body.name, "defaults": body.defaults},
        )
        session.commit()
        return {"id": template_id, "name": body.name}

    @app.get("/v1/org/deal-memo-templates")
    def list_templates(
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        return {"templates": list(fold_templates(session, principal.org_id).values())}

    # -- e-signature: ordered signing chain (task 6.4) ----------------------------

    @app.post("/v1/projects/{project_id}/signature-requests", status_code=201)
    def create_signature_request(
        project_id: str,
        body: SignatureRequestReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        if not body.signers:
            raise HTTPException(status_code=422, detail="signers must not be empty")
        req_id = f"sig-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.SIGNATURE_REQUEST_CREATED,
            {
                "id": req_id,
                "docType": body.docType,
                "docRef": body.docRef,
                "signers": body.signers,
                "requestedAt": dt.datetime.now(dt.UTC).isoformat(),
            },
        )
        return {"id": req_id, "signers": body.signers, "status": "pending"}

    @app.post("/v1/projects/{project_id}/signature-requests/{req_id}:sign")
    def sign_request(
        project_id: str,
        req_id: str,
        body: SignReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            require_next_signer(state.signature_requests.get(req_id), body.signer)
        except SignatureError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.SIGNATURE_SIGNED,
            {"id": req_id, "signer": body.signer, "at": dt.datetime.now(dt.UTC).isoformat()},
        )
        request = reconstruct(session, project_id).signature_requests[req_id]
        return {"id": req_id, "status": request["status"], "signed": request["signed"]}

    @app.get("/v1/projects/{project_id}/signature-requests")
    def list_signature_requests(
        project_id: str,
        pending: bool = Query(default=False, description="only incomplete (reminders feed)"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        if pending:
            return {"pending": pending_view(state.signature_requests)}
        return {"requests": list(state.signature_requests.values())}

    # -- call sheets (task 4.1) ------------------------------------------------------

    @app.post("/v1/projects/{project_id}/call-sheets:publish", status_code=201)
    def publish_call_sheet(
        project_id: str,
        body: CallSheetPublishReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            content = build_call_sheet(
                state, day_index=body.dayIndex, date_iso=body.date, general_call=body.generalCall
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

        # Recipients: the day's cast (auto) + explicit extras; each gets an ack token.
        recipients = [
            {
                "name": c["character"],
                "character": c["character"],
                "role": "cast",
                "ackToken": uuid.uuid4().hex,
                "acknowledgedAt": None,
            }
            for c in content["cast"]
        ] + [
            {
                "name": r.get("name", ""),
                "email": r.get("email", ""),
                "role": r.get("role", "crew"),
                "character": r.get("character"),
                "ackToken": uuid.uuid4().hex,
                "acknowledgedAt": None,
            }
            for r in body.extraRecipients
        ]

        priors = [cs for cs in state.call_sheets.values() if cs["dayIndex"] == body.dayIndex]
        revision = max((cs["revision"] for cs in priors), default=0) + 1
        latest_prior = max(priors, key=lambda cs: cs["revision"], default=None)
        renotify = (
            affected_recipients(latest_prior["content"], content, recipients)
            if latest_prior is not None
            else recipients
        )

        cs_id = f"cs-{uuid.uuid4().hex[:12]}"
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.CALL_SHEET_PUBLISHED,
            {
                "id": cs_id,
                "dayIndex": body.dayIndex,
                "revision": revision,
                "content": content,
                "recipients": recipients,
                "publishedAt": dt.datetime.now(dt.UTC).isoformat(),
            },
        )
        return {
            "id": cs_id,
            "revision": revision,
            "supersedes": latest_prior["id"] if latest_prior is not None else None,
            "content": content,
            "recipients": [
                {"name": r["name"], "role": r["role"], "ackToken": r["ackToken"]}
                for r in recipients
            ],
            "renotify": [r["name"] for r in renotify],
        }

    @app.post("/v1/projects/{project_id}/call-sheets/{cs_id}:acknowledge")
    def acknowledge_call_sheet(
        project_id: str,
        cs_id: str,
        body: CallSheetAckReq,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        """Capability-token ack — recipients need no seat."""
        org = org_of(session, project_id)
        if org is None:
            raise HTTPException(status_code=404, detail="project not found")
        state = reconstruct(session, project_id)
        sheet = state.call_sheets.get(cs_id)
        if sheet is None:
            raise HTTPException(status_code=404, detail="call sheet not found")
        if not any(r.get("ackToken") == body.ackToken for r in sheet.get("recipients", [])):
            raise HTTPException(status_code=404, detail="unknown ack token")
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=f"ack:{body.ackToken[:8]}",
            kind=EventKind.CALL_SHEET_ACKED,
            payload={
                "id": cs_id,
                "ackToken": body.ackToken,
                "at": dt.datetime.now(dt.UTC).isoformat(),
            },
        )
        session.commit()
        return {"id": cs_id, "acknowledged": True}

    @app.get("/v1/projects/{project_id}/call-sheets")
    def list_call_sheets(
        project_id: str,
        day: int | None = Query(default=None),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        sheets = [cs for cs in state.call_sheets.values() if day is None or cs["dayIndex"] == day]
        return {"callSheets": sorted(sheets, key=lambda c: (c["dayIndex"], c["revision"]))}

    # -- per-role copilot nudges (task 4.1) --------------------------------------

    @app.get("/v1/projects/{project_id}/copilot/nudges")
    def copilot_nudges(
        project_id: str,
        role: str = Query(..., description="coordinator | first_ad | line_producer"),
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        try:
            return {"role": role, "nudges": nudges_for(state, role)}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

    # -- colored-page revisions (task 6.1) ------------------------------------

    @app.post("/v1/projects/{project_id}/script-revisions:release", status_code=201)
    def release_revision(
        project_id: str,
        body: RevisionReleaseReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _write_ctx(session, principal, project_id)
        state = reconstruct(session, project_id)
        index, color = next_color(state.revision_history)
        date_iso = dt.date.today().isoformat()
        _commit_event(
            session,
            org,
            project_id,
            principal.user_id,
            EventKind.SCRIPT_REVISION_RELEASED,
            {
                "index": index,
                "color": color,
                "date": date_iso,
                "slug": revision_slug(color, date_iso),
                "note": body.note,
            },
        )
        return {
            "index": index,
            "color": color,
            "date": date_iso,
            "slug": revision_slug(color, date_iso),
            "pagesLocked": True,
        }

    @app.get("/v1/projects/{project_id}/script-revisions")
    def revision_history(
        project_id: str,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        _authz(session, principal, project_id)
        state = reconstruct(session, project_id)
        return {"pagesLocked": state.pages_locked, "history": state.revision_history}

    # -- schedule optimize (task 2.1) → proposed re-board --------------------

    @app.post("/v1/projects/{project_id}/schedule:optimize")
    def optimize_schedule(
        project_id: str,
        body: OptimizeReq,
        session: Session = Depends(get_session),
        principal: Principal = Depends(get_principal),
    ) -> dict[str, Any]:
        org = _authz(session, principal, project_id)
        _require_write(principal)
        state = reconstruct(session, project_id)
        if not state.scenes:
            raise HTTPException(status_code=400, detail="no scenes to schedule")
        problem = SchedulingProblem(
            scenes=[
                SchedScene(
                    id=s.id,
                    location=s.location or "UNSET",
                    cast=frozenset(s.characters),
                    page_eighths=s.page_eighths,
                    int_ext=s.int_ext,
                    time_of_day=s.time_of_day,
                )
                for s in state.scenes.values()
            ],
            num_days=body.numDays,
            capacity_eighths=body.capacityEighths,
            time_budget_s=body.timeBudgetS,
        )
        solution = solve_schedule(problem)
        if not solution.feasible:
            raise HTTPException(status_code=422, detail=f"schedule {solution.status.value}")
        diff = propose_schedule(
            state,
            diff_id=f"diff-{uuid.uuid4().hex[:12]}",
            assignments=solution.assignments,
            dood=solution.dood,
            num_days=body.numDays,
        )
        append_event(
            session,
            org_id=org,
            project_id=project_id,
            actor=principal.user_id,
            kind=EventKind.CHANGE_PROPOSED,
            payload=diff_to_dict(diff),
        )
        session.commit()
        return {
            "diff": diff_to_dict(diff),
            "solver": {
                "status": solution.status.value,
                "locationDays": solution.location_days,
                "totalHoldDays": solution.total_hold_days,
                "optimalityGap": solution.optimality_gap,
                "solveTimeS": solution.solve_time_s,
            },
        }

    return app


app = create_app()
