from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import (
    Asset,
    AssetCreate,
    AssetUpdate,
    WorkOrder,
    WorkOrderCreate,
    WorkOrderUpdate,
)


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


def find_work_order(
    work_order_id: UUID,
    database: Session,
) -> WorkOrderModel:
    work_order = database.get(WorkOrderModel, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    return work_order


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


@app.post(
    "/work-orders",
    response_model=WorkOrder,
    status_code=status.HTTP_201_CREATED,
)
def create_work_order(
    work_order_data: WorkOrderCreate,
    database: Session = Depends(get_db),
) -> WorkOrderModel:
    asset = database.get(AssetModel, work_order_data.asset_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    work_order = WorkOrderModel(**work_order_data.model_dump())

    database.add(work_order)
    database.commit()
    database.refresh(work_order)

    return work_order


@app.get("/work-orders", response_model=list[WorkOrder])
def list_work_orders(
    database: Session = Depends(get_db),
) -> list[WorkOrderModel]:
    statement = select(WorkOrderModel).order_by(
        WorkOrderModel.created_at
    )
    return list(database.scalars(statement).all())


@app.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
)
def get_work_order(
    work_order_id: UUID,
    database: Session = Depends(get_db),
) -> WorkOrderModel:
    return find_work_order(work_order_id, database)


@app.patch(
    "/work-orders/{work_order_id}",
    response_model=WorkOrder,
)
def update_work_order(
    work_order_id: UUID,
    work_order_data: WorkOrderUpdate,
    database: Session = Depends(get_db),
) -> WorkOrderModel:
    work_order = find_work_order(work_order_id, database)

    update_fields = work_order_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    for field, value in update_fields.items():
        setattr(work_order, field, value)

    database.commit()
    database.refresh(work_order)

    return work_order


@app.delete(
    "/work-orders/{work_order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_work_order(
    work_order_id: UUID,
    database: Session = Depends(get_db),
) -> None:
    work_order = find_work_order(work_order_id, database)

    database.delete(work_order)
    database.commit()