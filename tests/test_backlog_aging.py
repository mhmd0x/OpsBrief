from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkOrderModel

from conftest import TestingSessionLocal


client = TestClient(app)


def test_work_order_backlog_aging() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "Backlog Test Asset",
            "asset_tag": "BACKLOG-001",
            "location": "Utilities",
        },
    )

    assert asset_response.status_code == 201
    asset_id = asset_response.json()["id"]

    work_order_ids = []

    for title in [
        "Recent backlog item",
        "Older backlog item",
        "Completed backlog item",
    ]:
        response = client.post(
            "/work-orders",
            json={
                "asset_id": asset_id,
                "title": title,
                "priority": "medium",
                "due_date": (
                    datetime.now(UTC)
                    + timedelta(days=7)
                ).isoformat(),
            },
        )

        assert response.status_code == 201
        work_order_ids.append(
            UUID(response.json()["id"])
        )

    with TestingSessionLocal() as database:
        recent = database.get(
            WorkOrderModel,
            work_order_ids[0],
        )
        older = database.get(
            WorkOrderModel,
            work_order_ids[1],
        )

        recent.created_at = (
            datetime.now(UTC) - timedelta(days=4)
        )
        older.created_at = (
            datetime.now(UTC) - timedelta(days=40)
        )
        database.commit()

    complete_response = client.patch(
        f"/work-orders/{work_order_ids[2]}",
        json={"status": "completed"},
    )

    assert complete_response.status_code == 200

    response = client.get(
        "/insights/work-order-backlog-aging"
    )

    assert response.status_code == 200

    backlog = response.json()

    assert backlog["total_backlog_count"] == 2
    assert backlog["oldest_age_days"] == 40
    assert backlog["average_age_days"] == 22.0
    assert [
        bucket["work_order_count"]
        for bucket in backlog["buckets"]
    ] == [1, 0, 1, 0]
