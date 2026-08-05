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