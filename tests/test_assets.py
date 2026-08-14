from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_asset() -> None:
    response = client.post(
        "/assets",
        json={
            "name": "Main Air Compressor",
            "asset_tag": "COMP-001",
            "location": "Utility Building",
        },
    )

    assert response.status_code == 201

    asset = response.json()

    assert asset["name"] == "Main Air Compressor"
    assert asset["asset_tag"] == "COMP-001"
    assert asset["location"] == "Utility Building"
    assert "id" in asset
    assert "created_at" in asset

def test_list_assets() -> None:
    create_response = client.post(
        "/assets",
        json={
            "name": "Cooling Water Pump",
            "asset_tag": "PUMP-001",
            "location": "Pump Room",
        },
    )

    created_asset = create_response.json()

    response = client.get("/assets")

    assert response.status_code == 200
    assert created_asset in response.json()


def test_get_existing_asset() -> None:
    create_response = client.post(
        "/assets",
        json={
            "name": "Emergency Generator",
            "asset_tag": "GEN-001",
            "location": "Generator Building",
        },
    )

    created_asset = create_response.json()

    response = client.get(f"/assets/{created_asset['id']}")

    assert response.status_code == 200
    assert response.json() == created_asset


def test_get_unknown_asset() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/assets/{unknown_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_update_existing_asset() -> None:
    create_response = client.post(
        "/assets",
        json={
            "name": "Boiler Feed Pump",
            "asset_tag": "PUMP-002",
            "location": "Boiler House",
        },
    )

    created_asset = create_response.json()

    response = client.patch(
        f"/assets/{created_asset['id']}",
        json={
            "location": "Maintenance Workshop",
        },
    )

    assert response.status_code == 200

    updated_asset = response.json()

    assert updated_asset["name"] == "Boiler Feed Pump"
    assert updated_asset["asset_tag"] == "PUMP-002"
    assert updated_asset["location"] == "Maintenance Workshop"
    assert updated_asset["id"] == created_asset["id"]


def test_update_unknown_asset() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(
        f"/assets/{unknown_id}",
        json={
            "location": "Maintenance Workshop",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_delete_existing_asset() -> None:
    create_response = client.post(
        "/assets",
        json={
            "name": "Exhaust Fan",
            "asset_tag": "FAN-001",
            "location": "Production Area",
        },
    )

    created_asset = create_response.json()
    asset_id = created_asset["id"]

    delete_response = client.delete(f"/assets/{asset_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/assets/{asset_id}")

    assert get_response.status_code == 404


def test_delete_unknown_asset() -> None:
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.delete(f"/assets/{unknown_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_clear_asset_location_with_null() -> None:
    create_response = client.post(
        "/assets",
        json={
            "name": "Boiler Feed Pump",
            "asset_tag": "PUMP-LOC-001",
            "location": "Boiler House",
        },
    )

    created_asset = create_response.json()
    asset_id = created_asset["id"]

    response = client.patch(
        f"/assets/{asset_id}",
        json={"location": None},
    )

    assert response.status_code == 200
    assert response.json()["location"] is None

    get_response = client.get(f"/assets/{asset_id}")
    assert get_response.json()["location"] is None


def test_update_work_order_clears_failure_code_with_null() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "Seal Test Pump",
            "asset_tag": "PUMP-FC-001",
            "location": "Pump Room",
        },
    )
    asset_id = asset_response.json()["id"]

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset_id,
            "title": "Inspect seal leak",
            "failure_code": "SEAL_LEAK",
            "priority": "medium",
            "due_date": "2026-08-18T08:00:00Z",
        },
    )
    work_order_id = create_response.json()["id"]

    response = client.patch(
        f"/work-orders/{work_order_id}",
        json={"failure_code": None},
    )

    assert response.status_code == 200
    assert response.json()["failure_code"] is None

    get_response = client.get(f"/work-orders/{work_order_id}")
    assert get_response.json()["failure_code"] is None


def test_update_work_order_keeps_fields_when_omitted() -> None:
    asset_response = client.post(
        "/assets",
        json={
            "name": "Omit Test Pump",
            "asset_tag": "PUMP-OMIT-001",
            "location": "Pump Room",
        },
    )
    asset_id = asset_response.json()["id"]

    create_response = client.post(
        "/work-orders",
        json={
            "asset_id": asset_id,
            "title": "Original title",
            "failure_code": "ORIGINAL_CODE",
            "priority": "medium",
            "due_date": "2026-08-18T08:00:00Z",
        },
    )
    work_order_id = create_response.json()["id"]

    response = client.patch(
        f"/work-orders/{work_order_id}",
        json={"title": "Updated title"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated title"
    assert updated["failure_code"] == "ORIGINAL_CODE"
    assert updated["priority"] == "medium"


def test_create_asset_with_duplicate_tag() -> None:
    asset_data = {
        "name": "Primary Compressor",
        "asset_tag": "COMP-200",
        "location": "Utilities Area",
    }

    first_response = client.post("/assets", json=asset_data)
    second_response = client.post(
        "/assets",
        json={
            "name": "Backup Compressor",
            "asset_tag": "COMP-200",
            "location": "Workshop",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Asset tag already exists"
    }


def test_update_asset_with_duplicate_tag() -> None:
    first_response = client.post(
        "/assets",
        json={
            "name": "Primary Pump",
            "asset_tag": "PUMP-100",
            "location": "Pump Room",
        },
    )

    second_response = client.post(
        "/assets",
        json={
            "name": "Standby Pump",
            "asset_tag": "PUMP-200",
            "location": "Pump Room",
        },
    )

    second_asset = second_response.json()

    update_response = client.patch(
        f"/assets/{second_asset['id']}",
        json={"asset_tag": "PUMP-100"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert update_response.status_code == 409
    assert update_response.json() == {
        "detail": "Asset tag already exists"
    }

