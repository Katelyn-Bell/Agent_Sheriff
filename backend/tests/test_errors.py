from __future__ import annotations

from fastapi.testclient import TestClient

from agentsheriff.main import app


def test_http_errors_use_error_envelope() -> None:
    response = TestClient(app).get("/v1/policies/missing-policy")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Policy version not found."}}


def test_validation_errors_use_error_envelope() -> None:
    response = TestClient(app).post("/v1/tool-call", json={"agent_id": "a1"})

    assert response.status_code == 422
    assert response.json() == {"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed."}}
