"""FastAPI app — the graph API (tasks 0.2, 1.1, 2.1/2.2 seams).

Every write appends to the event log; reads are projections; downstream effects are always
*proposed diffs* a human confirms. Dev auth reads the principal from ``X-User-Id`` /
``X-Org-Id`` / ``X-Role`` headers; production swaps in SSO/JWT.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session, sessionmaker

from throughline_ml.scheduler import Scene as SchedScene
from throughline_ml.scheduler import SchedulingProblem, solve_schedule

from .budget import build_cost_report, line_from_payload
from .budget.model import BudgetLine, Fringe
from .config import settings
from .db import init_db, make_engine, make_session_factory
from .events import EventKind, append_event, list_events
from .graph import GraphState, reconstruct
from .ingest import ingest_script
from .interop import to_aicp, to_aicp_csv
from .propagation import (
    apply_change,
    diff_to_dict,
    propose_reschedule,
    propose_schedule,
    reject_change,
)
from .rbac import AuthzError, NotFoundError, Principal, authorize_project, require_write
from .revision import propose_revision
from .schemas import (
    BudgetLineReq,
    CreateProjectReq,
    EtcReq,
    ImportScriptReq,
    LedgerEntryReq,
    OptimizeReq,
    RescheduleChangeReq,
    ScriptDiffReq,
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
            payload={"title": body.title, "type": body.type},
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
