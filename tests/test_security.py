import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import require_api_key


@pytest.fixture
def security_client(monkeypatch):
    original_override = app.dependency_overrides.pop(
        require_api_key,
        None,
    )
    monkeypatch.setenv(
        "OPSBRIEF_API_KEY",
        "test-only-api-key",
    )

    try:
        yield TestClient(app)
    finally:
        if original_override is not None:
            app.dependency_overrides[require_api_key] = (
                original_override
            )


def test_reject_missing_api_key(
    security_client: TestClient,
) -> None:
    response = security_client.post(
        "/assets",
        json={
            "name": "Unauthorized Asset",
            "asset_tag": "AUTH-001",
            "location": "Test Area",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_reject_incorrect_api_key(
    security_client: TestClient,
) -> None:
    response = security_client.post(
        "/assets",
        headers={"X-API-Key": "incorrect-key"},
        json={
            "name": "Unauthorized Asset",
            "asset_tag": "AUTH-002",
            "location": "Test Area",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_accept_correct_api_key(
    security_client: TestClient,
) -> None:
    response = security_client.post(
        "/assets",
        headers={"X-API-Key": "test-only-api-key"},
        json={
            "name": "Authorized Asset",
            "asset_tag": "AUTH-003",
            "location": "Test Area",
        },
    )

    assert response.status_code == 201


def test_allow_public_read_without_api_key(
    security_client: TestClient,
) -> None:
    response = security_client.get("/assets")

    assert response.status_code == 200