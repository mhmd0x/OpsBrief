from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_test_asset() -> dict:
    response = client.post(
        "/assets",
        json={
            "name": "Lifecycle Test Asset",
            "asset_tag": "LIFECYCLE-001",
        },
    )
    assert response.status_code == 201
    return response.json()


def work_order_payload(asset_id: str) -> dict:
    return {
        "asset_id": asset_id,
        "title": "Repair lifecycle test",
        "due_date": "2026-08-20T08:00:00Z",
    }


def test_create_work_order_with_full_lifecycle_sequence() -> None:
    asset = create_test_asset()
    payload = work_order_payload(asset["id"])
    payload.update(
        {
            "failure_reported_at": "2026-08-10T08:00:00Z",
            "repair_started_at": "2026-08-10T09:00:00Z",
            "restored_at": "2026-08-10T10:00:00Z",
        }
    )

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 201
    assert response.json()["failure_reported_at"] == "2026-08-10T08:00:00"
    assert response.json()["repair_started_at"] == "2026-08-10T09:00:00"
    assert response.json()["restored_at"] == "2026-08-10T10:00:00"


def test_create_work_order_with_partial_lifecycle_timestamps() -> None:
    asset = create_test_asset()
    payload = work_order_payload(asset["id"])
    payload["restored_at"] = "2026-08-10T10:00:00Z"

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 201
    assert response.json()["failure_reported_at"] is None
    assert response.json()["repair_started_at"] is None
    assert response.json()["restored_at"] == "2026-08-10T10:00:00"


def test_create_work_order_rejects_invalid_lifecycle_ordering() -> None:
    asset = create_test_asset()
    payload = work_order_payload(asset["id"])
    payload.update(
        {
            "failure_reported_at": "2026-08-10T10:00:00Z",
            "repair_started_at": "2026-08-10T09:00:00Z",
        }
    )

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 422
    assert "lifecycle timestamps" in response.json()["detail"][0]["msg"]


def test_create_work_order_rejects_invalid_partial_lifecycle_ordering() -> None:
    asset = create_test_asset()
    payload = work_order_payload(asset["id"])
    payload.update(
        {
            "failure_reported_at": "2026-08-10T10:00:00Z",
            "restored_at": "2026-08-10T09:00:00Z",
        }
    )

    response = client.post("/work-orders", json=payload)

    assert response.status_code == 422


def test_update_work_order_with_valid_lifecycle_timestamps() -> None:
    asset = create_test_asset()
    create_response = client.post(
        "/work-orders",
        json=work_order_payload(asset["id"]),
    )
    work_order_id = create_response.json()["id"]

    response = client.patch(
        f"/work-orders/{work_order_id}",
        json={
            "failure_reported_at": "2026-08-10T08:00:00Z",
            "repair_started_at": "2026-08-10T09:00:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["failure_reported_at"] == "2026-08-10T08:00:00"
    assert response.json()["repair_started_at"] == "2026-08-10T09:00:00"
    assert response.json()["restored_at"] is None


def test_update_work_order_rejects_ordering_against_stored_values() -> None:
    asset = create_test_asset()
    payload = work_order_payload(asset["id"])
    payload.update(
        {
            "failure_reported_at": "2026-08-10T08:00:00Z",
            "repair_started_at": "2026-08-10T09:00:00Z",
            "restored_at": "2026-08-10T10:00:00Z",
        }
    )
    create_response = client.post("/work-orders", json=payload)
    work_order_id = create_response.json()["id"]

    response = client.patch(
        f"/work-orders/{work_order_id}",
        json={"repair_started_at": "2026-08-10T07:00:00Z"},
    )

    assert response.status_code == 422
    stored = client.get(f"/work-orders/{work_order_id}").json()
    assert stored["failure_reported_at"] == "2026-08-10T08:00:00"
    assert stored["repair_started_at"] == "2026-08-10T09:00:00"
    assert stored["restored_at"] == "2026-08-10T10:00:00"


def test_existing_work_order_response_includes_nullable_lifecycle_fields() -> None:
    asset = create_test_asset()
    response = client.post(
        "/work-orders",
        json=work_order_payload(asset["id"]),
    )

    assert response.status_code == 201
    work_order = response.json()
    assert {
        "failure_reported_at",
        "repair_started_at",
        "restored_at",
    } <= work_order.keys()
    assert work_order["failure_reported_at"] is None
    assert work_order["repair_started_at"] is None
    assert work_order["restored_at"] is None
