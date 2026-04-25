from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from agentsheriff.api.auth import current_user
from agentsheriff.api.db import get_session
from agentsheriff.main import app
from agentsheriff.models.orm import Base, User


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    original_factory = app.state.session_factory
    app.state.session_factory = SessionLocal
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.session_factory = original_factory
        app.dependency_overrides.clear()


def _make_user(onboarded: bool = False) -> User:
    SessionLocal = app.state.session_factory
    user = User(
        id=str(uuid.uuid4()),
        google_sub="goog_" + str(uuid.uuid4()),
        email="sheriff@example.com",
        name="Test Sheriff",
        avatar_url=None,
        onboarded=onboarded,
    )
    with SessionLocal() as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        # detach so callers can read fields without holding the session
        session.expunge(user)
    return user


def _override_current_user(user_id: str) -> None:
    """Wire current_user to fetch the user from the request's DB session."""

    def override(db: Session = Depends(get_session)) -> User:
        loaded = db.get(User, user_id)
        assert loaded is not None
        return loaded

    app.dependency_overrides[current_user] = override


def test_me_returns_401_without_session(client: TestClient) -> None:
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_user_when_session_present(client: TestClient) -> None:
    user = _make_user()
    _override_current_user(user.id)

    response = client.get("/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["email"] == user.email
    assert body["name"] == user.name
    assert body["onboarded"] is False


def test_logout_returns_204(client: TestClient) -> None:
    response = client.post("/v1/auth/logout")
    assert response.status_code == 204


def test_mark_onboarded_flips_flag(client: TestClient) -> None:
    user = _make_user()
    _override_current_user(user.id)

    response = client.post("/v1/auth/me/onboarded")
    assert response.status_code == 200
    assert response.json()["onboarded"] is True

    SessionLocal = app.state.session_factory
    with SessionLocal() as session:
        refreshed = session.get(User, user.id)
        assert refreshed is not None
        assert refreshed.onboarded is True


def test_google_start_returns_503_when_oauth_not_configured(
    client: TestClient,
) -> None:
    response = client.get("/v1/auth/google/start", follow_redirects=False)
    assert response.status_code == 503
    body = response.json()
    # error envelope is { "error": { "code", "message" } } per api/errors.py
    assert body["error"]["message"] == "oauth_not_configured"
