from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status

from app.schemas import Asset, AssetCreate, AssetUpdate


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


@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: UUID) -> Asset:
    for asset in assets:
        if asset.id == asset_id:
            return asset

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Asset not found",
    )


@app.patch("/assets/{asset_id}", response_model=Asset)
def update_asset(asset_id: UUID, asset_data: AssetUpdate) -> Asset:
    for index, asset in enumerate(assets):
        if asset.id == asset_id:
            update_fields = asset_data.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            updated_asset = asset.model_copy(update=update_fields)
            assets[index] = updated_asset

            return updated_asset

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Asset not found",
    )


@app.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset(asset_id: UUID) -> None:
    for index, asset in enumerate(assets):
        if asset.id == asset_id:
            assets.pop(index)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Asset not found",
    )


