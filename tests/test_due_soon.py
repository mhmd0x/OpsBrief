from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_work_orders_due_within_seven_days() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "Boiler Feed Pump",
            "asset_tag": "PUMP-202",
            "location": "Boiler House",
        },
    )
    asset_id = asset_response.json()["id"]

    work_orders = [
        {
            "title": "Due tomorrow",
            "due_date": datetime.now(UTC) + timedelta(days=1),
        },
        {
            "title": "Due after eight days",
            "due_date": datetime.now(UTC) + timedelta(days=8),
        },
        {
            "title": "Already overdue",
            "due_date": datetime.now(UTC) - timedelta(days=1),
        },
    ]

    for work_order in work_orders:
        response = client.post(
            "/work-orders",
            json={
                "asset_id": asset_id,
                "title": work_order["title"],
                "priority": "medium",
                "due_date": work_order["due_date"].isoformat(),
            },
        )
        assert response.status_code == 201

    response = client.get("/work-orders/due-soon")

    assert response.status_code == 200

    titles = [
        work_order["title"]
        for work_order in response.json()
    ]

    assert titles == ["Due tomorrow"]