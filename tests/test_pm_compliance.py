from datetime import datetime

from fastapi.testclient import TestClient

from app.config import APP_TIMEZONE
from app.main import app


client = TestClient(app)


def test_monthly_pm_compliance() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "PM Test Pump",
            "asset_tag": "PM-TEST-001",
            "location": "Utilities",
        },
    )

    assert asset_response.status_code == 201
    asset_id = asset_response.json()["id"]

    local_noon = datetime.now(APP_TIMEZONE).replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )

    work_order_ids = []

    for title in [
        "Monthly lubrication PM",
        "Monthly inspection PM",
    ]:
        response = client.post(
            "/work-orders",
            json={
                "asset_id": asset_id,
                "title": title,
                "priority": "medium",
                "maintenance_type": "preventive",
                "due_date": local_noon.isoformat(),
            },
        )

        assert response.status_code == 201
        work_order_ids.append(response.json()["id"])

    complete_response = client.patch(
        f"/work-orders/{work_order_ids[0]}",
        json={"status": "completed"},
    )

    assert complete_response.status_code == 200

    response = client.get(
        "/insights/monthly-pm-compliance"
    )

    assert response.status_code == 200

    compliance = response.json()

    assert compliance["planned_count"] == 2
    assert compliance["completed_count"] == 1
    assert compliance["remaining_count"] == 1
    assert len(compliance["planned_work_orders"]) == 2
    assert len(compliance["completed_work_orders"]) == 1
    assert len(compliance["remaining_work_orders"]) == 1
    assert len(compliance["overdue_work_orders"]) in {0, 1}
    assert compliance["planned_to_date_count"] == 2
    assert compliance["completed_to_date_count"] == 1
    assert compliance["completion_percentage"] == 50.0
    assert compliance["on_plan"] is False
    assert compliance["calendar_days_remaining"] >= 1
    assert compliance["required_per_day"] == round(
        1 / compliance["calendar_days_remaining"],
        2,
    )