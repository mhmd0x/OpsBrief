from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_check_reports_failure_when_database_unreachable() -> None:
    from app.database import get_db
    from app.main import app
    from fastapi.testclient import TestClient

    original_override = app.dependency_overrides.get(get_db)

    def broken_get_db():
        yield RuntimeError("database unreachable")

    app.dependency_overrides[get_db] = broken_get_db

    try:
        broken_client = TestClient(app)
        response = broken_client.get("/health")

        assert response.status_code == 503
        assert response.json() == {
            "detail": "Database is unavailable"
        }
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)
