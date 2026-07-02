"""Persistence: the append-only event log is the single durable source of truth.

Everything else (the materialized graph, DOOD, budget views) is a *projection* derived by
folding events — so any past state is reconstructable and the audit trail is complete
(PRODUCT_SPEC §9 consistency model). In prod this is PostgreSQL; SQLite backs unit tests.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Event(Base):
    """One immutable fact. ``id`` is the global total order (used for Time Machine).

    ``seq`` is a per-project sequence for cursor pagination. ``org_id`` scopes every event
    for tenant isolation (RBAC). Events are NEVER updated or deleted.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String, index=True)
    project_id: Mapped[str] = mapped_column(String, index=True)
    seq: Mapped[int] = mapped_column(Integer)
    ts: Mapped[dt.datetime] = mapped_column(DateTime)
    actor: Mapped[str] = mapped_column(String)  # user id, or "system" for deterministic projectors
    kind: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


def make_engine(url: str) -> Engine:
    connect_args: dict[str, Any] = {}
    kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool  # share one in-memory DB across sessions
    engine = create_engine(url, connect_args=connect_args, **kwargs)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
