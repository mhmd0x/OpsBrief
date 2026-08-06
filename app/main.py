from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssetModel
from app.schemas import Asset, AssetCreate, AssetUpdate


app = FastAPI(
    title="OpsBrief API",
    description="Decision-support API for maintenance operations.",
    version="0.1.0",
)


def find_asset(asset_id: UUID, database: Session) -> AssetModel:
    asset = database.get(AssetModel, asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    return asset


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/assets",
    response_model=Asset,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    asset_data: AssetCreate,
    database: Session = Depends(get_db),
) -> AssetModel:
    asset = AssetModel(**asset_data.model_dump())

    database.add(asset)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset tag already exists",
        ) from error

    database.refresh(asset)
    return asset


@app.get("/assets", response_model=list[Asset])
def list_assets(
    database: Session = Depends(get_db),
) -> list[AssetModel]:
    statement = select(AssetModel).order_by(AssetModel.created_at)
    return list(database.scalars(statement).all())


@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(
    asset_id: UUID,
    database: Session = Depends(get_db),
) -> AssetModel:
    return find_asset(asset_id, database)


@app.patch("/assets/{asset_id}", response_model=Asset)
def update_asset(
    asset_id: UUID,
    asset_data: AssetUpdate,
    database: Session = Depends(get_db),
) -> AssetModel:
    asset = find_asset(asset_id, database)

    update_fields = asset_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    for field, value in update_fields.items():
        setattr(asset, field, value)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset tag already exists",
        ) from error

    database.refresh(asset)
    return asset


@app.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset(
    asset_id: UUID,
    database: Session = Depends(get_db),
) -> None:
    asset = find_asset(asset_id, database)

    database.delete(asset)
    database.commit()