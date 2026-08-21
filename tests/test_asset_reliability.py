from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_asset_reliability_ranking() -> None:
    risk_asset_response = client.post(
        "/assets",
        json={
            "name": "High Risk Compressor",
            "asset_tag": "RISK-001",
            "location": "Utilities",
        },
    )
    stable_asset_response = client.post(
        "/assets",
        json={
            "name": "Stable Pump",
            "asset_tag": "STABLE-001",
            "location": "Cooling Station",
        },
    )

    assert risk_asset_response.status_code == 201
    assert stable_asset_response.status_code == 201

    risk_asset_id = risk_asset_response.json()["id"]
    stable_asset_id = stable_asset_response.json()["id"]

    risk_work_orders = [
        {
            "title": "Overdue high-temperature repair",
            "priority": "high",
            "due_date": (
                datetime.now(UTC) - timedelta(days=2)
            ).isoformat(),
        },
        {
            "title": "Inspect compressor cooling",
            "priority": "medium",
            "due_date": (
                datetime.now(UTC) + timedelta(days=2)
            ).isoformat(),
        },
        {
            "title": "Review temperature alarm",
            "priority": "medium",
            "due_date": (
                datetime.now(UTC) + timedelta(days=4)
            ).isoformat(),
        },
    ]

    for work_order in risk_work_orders:
        response = client.post(
            "/work-orders",
            json={
                "asset_id": risk_asset_id,
                "failure_code": "HIGH-TEMP",
                **work_order,
            },
        )
        assert response.status_code == 201

    stable_response = client.post(
        "/work-orders",
        json={
            "asset_id": stable_asset_id,
            "title": "Routine pump inspection",
            "priority": "medium",
            "due_date": (
                datetime.now(UTC) + timedelta(days=7)
            ).isoformat(),
        },
    )

    assert stable_response.status_code == 201

    response = client.get(
        "/insights/asset-reliability-ranking"
    )

    assert response.status_code == 200

    rankings = response.json()

    assert len(rankings) == 2

    highest_risk = rankings[0]
    lowest_risk = rankings[1]

    assert highest_risk["asset_name"] == "High Risk Compressor"
    assert highest_risk["active_work_order_count"] == 3
    assert highest_risk["overdue_work_order_count"] == 1
    assert highest_risk["high_priority_work_order_count"] == 1
    assert highest_risk["recurring_issue_count"] == 1
    assert highest_risk["risk_score"] == 12

    assert lowest_risk["asset_name"] == "Stable Pump"
    assert lowest_risk["risk_score"] == 1