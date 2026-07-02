"""Shared fixtures — an isolated in-memory event store + TestClient per test."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from throughline_api.app import create_app
from throughline_api.db import init_db, make_engine, make_session_factory


@pytest.fixture
def session_factory() -> sessionmaker:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    return make_session_factory(engine)


@pytest.fixture
def session(session_factory):
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(session_factory) -> TestClient:
    return TestClient(create_app(session_factory))


SAMPLE_FOUNTAIN = """INT. KITCHEN - DAY

JANE stands at the counter.

JANE
Morning.

EXT. PARK - DAY

BOB waits on a bench.

BOB
Over here.
"""
