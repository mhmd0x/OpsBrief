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


def test_delete_asset_with_work_orders() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "Process Pump",
            "asset_tag": "PUMP-WO-001",
            "location": "Production Area",
        },
    )

    asset = asset_response.json()

    work_order_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspect mechanical seal",
            "priority": "high",
            "due_date": "2026-08-20T08:00:00Z",
        },
    )

    assert work_order_response.status_code == 201

    delete_response = client.delete(
        f"/assets/{asset['id']}"
    )

    assert delete_response.status_code == 409
    assert delete_response.json() == {
        "detail": "Asset has work orders and cannot be deleted"
    }

    get_response = client.get(f"/assets/{asset['id']}")
    assert get_response.status_code == 200


def test_list_high_attention_work_orders() -> None:
    asset = create_test_asset()

    past_date = (
        datetime.now(UTC) - timedelta(days=1)
    ).isoformat()
    future_date = (
        datetime.now(UTC) + timedelta(days=7)
    ).isoformat()

    critical_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Critical future repair",
            "priority": "critical",
            "due_date": future_date,
        },
    )

    overdue_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Low-priority overdue task",
            "priority": "low",
            "due_date": past_date,
        },
    )

    normal_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Normal future task",
            "priority": "medium",
            "due_date": future_date,
        },
    )

    completed_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Completed critical task",
            "priority": "critical",
            "due_date": future_date,
        },
    )

    completed_work_order = completed_response.json()

    client.patch(
        f"/work-orders/{completed_work_order['id']}",
        json={"status": "completed"},
    )

    response = client.get("/work-orders/high-attention")

    assert response.status_code == 200

    returned_ids = {
        work_order["id"] for work_order in response.json()
    }

    assert critical_response.json()["id"] in returned_ids
    assert overdue_response.json()["id"] in returned_ids
    assert normal_response.json()["id"] not in returned_ids
    assert completed_response.json()["id"] not in returned_ids


def test_list_recurring_issues() -> None:
    asset = create_test_asset()
    due_date = (
        datetime.now(UTC) + timedelta(days=1)
    ).isoformat()

    for number in range(3):
        response = client.post(
            "/work-orders",
            json={
                "asset_id": asset["id"],
                "title": f"Bearing inspection {number + 1}",
                "failure_code": "BEARING_VIBRATION",
                "priority": "medium",
                "due_date": due_date,
            },
        )

        assert response.status_code == 201

    response = client.get("/insights/recurring-issues")

    assert response.status_code == 200

    signals = response.json()

    assert len(signals) == 1
    assert signals[0]["asset_id"] == asset["id"]
    assert signals[0]["asset_name"] == "Test Compressor"
    assert signals[0]["failure_code"] == "BEARING_VIBRATION"
    assert signals[0]["occurrence_count"] == 3
    assert "latest_occurrence" in signals[0]


def test_get_daily_operations_brief() -> None:
    asset = create_test_asset()

    overdue_date = (
        datetime.now(UTC) - timedelta(days=1)
    ).isoformat()

    local_now = datetime.now(APP_TIMEZONE)
    due_today = local_now.replace(
        hour=23,
        minute=59,
        second=0,
        microsecond=0,
    ).isoformat()

    future_date = (
        datetime.now(UTC) + timedelta(days=7)
    ).isoformat()

    overdue_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Overdue lubrication",
            "priority": "low",
            "due_date": overdue_date,
        },
    )

    today_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Inspection due today",
            "priority": "medium",
            "due_date": due_today,
        },
    )

    for number in range(3):
        recurring_response = client.post(
            "/work-orders",
            json={
                "asset_id": asset["id"],
                "title": f"Seal leak occurrence {number + 1}",
                "failure_code": "SEAL_LEAK",
                "priority": "medium",
                "due_date": future_date,
            },
        )

        assert recurring_response.status_code == 201

    assert overdue_response.status_code == 201
    assert today_response.status_code == 201

    response = client.get("/briefs/daily")

    assert response.status_code == 200

    brief = response.json()

    assert brief["timezone"] == str(APP_TIMEZONE)
    assert brief["summary"] == {
        "overdue_count": 1,
        "due_today_count": 1,
        "high_attention_count": 1,
        "recurring_issue_count": 1,
    }
    assert len(brief["overdue_work_orders"]) == 1
    assert len(brief["due_today_work_orders"]) == 1
    assert len(brief["high_attention_work_orders"]) == 1
    assert len(brief["recurring_issues"]) == 1
    assert "generated_at" in brief


def test_filter_work_orders() -> None:
    asset = create_test_asset()
    due_date = (
        datetime.now(UTC) + timedelta(days=7)
    ).isoformat()

    low_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Low-priority task",
            "priority": "low",
            "due_date": due_date,
        },
    )

    critical_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Critical task",
            "priority": "critical",
            "due_date": due_date,
        },
    )

    critical_work_order = critical_response.json()

    update_response = client.patch(
        f"/work-orders/{critical_work_order['id']}",
        json={"status": "in_progress"},
    )

    assert low_response.status_code == 201
    assert critical_response.status_code == 201
    assert update_response.status_code == 200

    response = client.get(
        "/work-orders"
        "?status=in_progress"
        "&priority=critical"
    )


def test_paginate_work_orders() -> None:
    asset = create_test_asset()
    due_date = (
        datetime.now(UTC) + timedelta(days=7)
    ).isoformat()
    created_ids = []

    for number in range(3):
        response = client.post(
            "/work-orders",
            json={
                "asset_id": asset["id"],
                "title": f"Paginated task {number + 1}",
                "priority": "medium",
                "due_date": due_date,
            },
        )

        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    response = client.get(
        "/work-orders?limit=2&offset=1"
    )

    assert response.status_code == 200

    returned_ids = [
        work_order["id"] for work_order in response.json()
    ]

    assert returned_ids == created_ids[1:]


def test_reject_invalid_status_transition() -> None:
    asset = create_test_asset()

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Completed inspection",
            "priority": "medium",
            "due_date": (
                datetime.now(UTC) + timedelta(days=1)
            ).isoformat(),
        },
    )

    work_order = create_response.json()

    complete_response = client.patch(
        f"/work-orders/{work_order['id']}",
        json={"status": "completed"},
    )

    assert complete_response.status_code == 200

    reopen_response = client.patch(
        f"/work-orders/{work_order['id']}",
        json={"status": "open"},
    )

    assert reopen_response.status_code == 409
    assert reopen_response.json() == {
        "detail": (
            "Cannot transition work order "
            "from completed to open"
        )
    }


def test_reject_due_date_without_timezone() -> None:
    asset = create_test_asset()

    response = client.post(
        "/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Ambiguous inspection time",
            "priority": "medium",
            "due_date": "2026-08-20T08:00:00",
        },
    )

    assert response.status_code == 422


