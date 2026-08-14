from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import Asset, AssetCreate, AssetUpdate
from app.security import require_api_key


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


def find_asset(
    asset_id: UUID,
    database: Session,
) -> AssetModel:
    asset = database.get(AssetModel, asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    return asset


@router.post(
    "",
    response_model=Asset,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
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


@router.get("", response_model=list[Asset])
def list_assets(
    database: Session = Depends(get_db),
) -> list[AssetModel]:
    statement = select(AssetModel).order_by(
        AssetModel.created_at
    )
    return list(database.scalars(statement).all())


@router.get("/{asset_id}", response_model=Asset)
def get_asset(
    asset_id: UUID,
    database: Session = Depends(get_db),
) -> AssetModel:
    return find_asset(asset_id, database)


@router.patch(
    "/{asset_id}",
    response_model=Asset,
    dependencies=[Depends(require_api_key)],
)
def update_asset(
    asset_id: UUID,
    asset_data: AssetUpdate,
    database: Session = Depends(get_db),
) -> AssetModel:
    asset = find_asset(asset_id, database)

    update_fields = asset_data.model_dump(
        exclude_unset=True,
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


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_asset(
    asset_id: UUID,
    database: Session = Depends(get_db),
) -> None:
    asset = find_asset(asset_id, database)

    work_order_id = database.scalar(
        select(WorkOrderModel.id)
        .where(WorkOrderModel.asset_id == asset_id)
        .limit(1)
    )

    if work_order_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset has work orders and cannot be deleted",
        )

    database.delete(asset)
    database.commit()