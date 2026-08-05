from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, status

from app.schemas import Asset, AssetCreate


app = FastAPI(
    title="OpsBrief API",
    description="Decision-support API for maintenance operations.",
    version="0.1.0",
)

assets: list[Asset] = []


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(asset_data: AssetCreate) -> Asset:
    asset = Asset(
        id=uuid4(),
        created_at=datetime.now(UTC),
        **asset_data.model_dump(),
    )

    assets.append(asset)
    return asset


@app.get("/assets", response_model=list[Asset])
def list_assets() -> list[Asset]:
    return assets