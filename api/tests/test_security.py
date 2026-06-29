"""HTTP-level security checks: rate limiting and security response headers.

Uses a TestClient against the real app with an in-memory SQLite DB injected via
the get_db dependency override, so no Postgres is needed.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    # StaticPool + check_same_thread=False so the one in-memory DB (with its
    # schema) is shared across TestClient's worker threads.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def _override_get_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


class TestSecurityHeaders:
    def test_headers_present_on_responses(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


class TestAuthRateLimit:
    def test_request_magic_link_is_rate_limited(self, client: TestClient):
        # The limit is 5/minute; the 6th request from the same client gets 429.
        statuses = [
            client.post("/api/auth/request", json={"email": "spammer@test.com"}).status_code
            for _ in range(6)
        ]
        assert statuses[:5] == [200, 200, 200, 200, 200]
        assert statuses[5] == 429
