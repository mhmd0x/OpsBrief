from fastapi.testclient import TestClient
from datetime import UTC, datetime, timedelta
from app.main import APP_TIMEZONE, app


client = TestClient(app)


def create_test_asset() -> dict:
    response = client.post(
        "/assets",
        json={
            "name": "Test Compressor",
            "asset_tag": "TEST-COMP-001",
            "location": "Utilities Area",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_work_order() -> None:
    asset = create_test_asset()

    response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspect compressor vibration",
            "description": "Investigate increased vibration.",
            "priority": "high",
            "due_date": "2026-08-10T08:00:00Z",
        },
    )

    assert response.status_code == 201

    work_order = response.json()

    assert work_order["asset_id"] == asset["id"]
    assert work_order["title"] == "Inspect compressor vibration"
    assert work_order["priority"] == "high"
    assert work_order["status"] == "open"
    assert "id" in work_order
    assert "created_at" in work_order
    assert "updated_at" in work_order


def test_create_work_order_for_unknown_asset() -> None:
    unknown_asset_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        "/work-orders",
        json={
            "asset_id": unknown_asset_id,
            "title": "Inspect unknown asset",
            "priority": "medium",
            "due_date": "2026-08-10T08:00:00Z",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_list_work_orders() -> None:
    asset = create_test_asset()

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Replace compressor filter",
            "priority": "medium",
            "due_date": "2026-08-12T08:00:00Z",
        },
    )

    assert create_response.status_code == 201
    created_work_order = create_response.json()

    response = client.get("/work-orders")

    assert response.status_code == 200
    assert created_work_order in response.json()


def test_get_existing_work_order() -> None:
    asset = create_test_asset()

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspect motor bearings",
            "priority": "high",
            "due_date": "2026-08-15T08:00:00Z",
        },
    )

    created_work_order = create_response.json()

    response = client.get(
        f"/work-orders/{created_work_order['id']}"
    )

    assert response.status_code == 200
    assert response.json() == created_work_order


def test_get_unknown_work_order() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/work-orders/{unknown_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Work order not found"
    }


def test_update_existing_work_order() -> None:
    asset = create_test_asset()

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspect pump seal",
            "priority": "medium",
            "due_date": "2026-08-18T08:00:00Z",
        },
    )

    created_work_order = create_response.json()

    response = client.patch(
        f"/work-orders/{created_work_order['id']}",
        json={
            "priority": "critical",
            "status": "in_progress",
        },
    )

    assert response.status_code == 200

    updated_work_order = response.json()

    assert updated_work_order["title"] == "Inspect pump seal"
    assert updated_work_order["priority"] == "critical"
    assert updated_work_order["status"] == "in_progress"
    assert updated_work_order["id"] == created_work_order["id"]


def test_update_unknown_work_order() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(
        f"/work-orders/{unknown_id}",
        json={
            "status": "completed",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Work order not found"
    }


def test_delete_existing_work_order() -> None:
    asset = create_test_asset()

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Clean ventilation filter",
            "priority": "low",
            "due_date": "2026-08-20T08:00:00Z",
        },
    )

    created_work_order = create_response.json()
    work_order_id = created_work_order["id"]

    delete_response = client.delete(
        f"/work-orders/{work_order_id}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(
        f"/work-orders/{work_order_id}"
    )

    assert get_response.status_code == 404


def test_delete_unknown_work_order() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.delete(f"/work-orders/{unknown_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Work order not found"
    }


def test_list_overdue_work_orders() -> None:
    asset = create_test_asset()

    overdue_date = (
        datetime.now(UTC) - timedelta(days=1)
    ).isoformat()
    future_date = (
        datetime.now(UTC) + timedelta(days=1)
    ).isoformat()

    overdue_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Overdue inspection",
            "priority": "high",
            "due_date": overdue_date,
        },
    )

    future_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Future inspection",
            "priority": "medium",
            "due_date": future_date,
        },
    )

    completed_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Completed overdue inspection",
            "priority": "low",
            "due_date": overdue_date,
        },
    )

    completed_work_order = completed_response.json()

    client.patch(
        f"/work-orders/{completed_work_order['id']}",
        json={"status": "completed"},
    )

    assert overdue_response.status_code == 201
    assert future_response.status_code == 201
    assert completed_response.status_code == 201

    response = client.get("/work-orders/overdue")

    assert response.status_code == 200

    work_orders = response.json()
    returned_ids = {
        work_order["id"] for work_order in work_orders
    }

    assert overdue_response.json()["id"] in returned_ids
    assert future_response.json()["id"] not in returned_ids
    assert completed_response.json()["id"] not in returned_ids


def test_list_due_today_work_orders() -> None:
    asset = create_test_asset()

    due_today = datetime.now(APP_TIMEZONE).replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )
    due_tomorrow = due_today + timedelta(days=1)

    today_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspection due today",
            "priority": "high",
            "due_date": due_today.isoformat(),
        },
    )

    tomorrow_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspection due tomorrow",
            "priority": "medium",
            "due_date": due_tomorrow.isoformat(),
        },
    )

    response = client.get("/work-orders/due-today")

    assert response.status_code == 200

    returned_ids = {
        work_order["id"] for work_order in response.json()
    }

    assert today_response.json()["id"] in returned_ids
    assert tomorrow_response.json()["id"] not in returned_ids


