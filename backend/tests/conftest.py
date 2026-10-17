import os

# Must be set before app modules read their config.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SESSION_SECRET"] = "test-secret"
os.environ["CRON_SECRET"] = "cron-test"
os.environ["GARMIN_TOKEN_KEY"] = "ZmFrZS1rZXktZm9yLXRlc3RzLW9ubHktMzItYnl0ZXM="

from app.auth import hash_password  # noqa: E402

os.environ["APP_PASSWORD_HASH"] = hash_password("hunter2")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

import app.auth  # noqa: E402
import app.models  # noqa: E402,F401


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session, monkeypatch):
    from app.db import get_session
    from app.main import app as fastapi_app

    monkeypatch.setattr(app.auth, "APP_PASSWORD_HASH", os.environ["APP_PASSWORD_HASH"])
    fastapi_app.dependency_overrides[get_session] = lambda: session
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def logged_in(client):
    assert client.post("/api/auth/login", json={"password": "hunter2"}).status_code == 200
    return client
