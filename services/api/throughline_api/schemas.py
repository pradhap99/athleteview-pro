"""Request bodies (camelCase JSON, per conventions). Responses are built as dicts."""

from __future__ import annotations

from pydantic import BaseModel


class CreateProjectReq(BaseModel):
    title: str
    type: str = "scripted"  # scripted | commercial | episodic


class ImportScriptReq(BaseModel):
    text: str
    format: str | None = None  # fdx | fountain | pdf (inferred if omitted)


class RescheduleChangeReq(BaseModel):
    type: str = "reschedule_scene"
    sceneId: str
    toDay: int


class OptimizeReq(BaseModel):
    numDays: int
    capacityEighths: int | None = None
    timeBudgetS: float = 10.0


class FringeReq(BaseModel):
    name: str
    ratePct: float
    cap: float | None = None


class BudgetLineReq(BaseModel):
    code: str
    category: str = "other"  # atl | btl | post | other
    description: str = ""
    qty: float = 1.0
    unit: str = "flat"
    rate: float = 0.0
    fringes: list[FringeReq] = []
    driver: dict | None = None  # e.g. {"kind": "hold_day"}
    aicpSection: str | None = None


class LedgerEntryReq(BaseModel):
    """An actual or commitment against an account code (human-entered/approved)."""

    code: str
    amount: float
    memo: str = ""


class EtcReq(BaseModel):
    code: str
    amount: float


class ScriptDiffReq(BaseModel):
    text: str
    format: str | None = None
