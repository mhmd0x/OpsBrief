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