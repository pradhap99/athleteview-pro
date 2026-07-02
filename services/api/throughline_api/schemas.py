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
