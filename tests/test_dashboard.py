from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "OpsBrief" in response.text
    assert "Daily Operations Brief" in response.text
    assert "Due soon" in response.text
    assert "due-soon-count" in response.text
    assert "due-soon-list" in response.text
    assert "<th>Asset</th>" in response.text
    assert "work-order-search" in response.text
    assert "priority-filter" in response.text


def test_dashboard_stylesheet() -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_dashboard_javascript() -> None:
    response = client.get("/static/dashboard.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert 'fetch("/assets"' in response.text
    assert "assetNames" in response.text
    assert "applyHighAttentionFilters" in response.text