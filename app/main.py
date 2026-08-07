from uuid import UUID
import os
from zoneinfo import ZoneInfo
from datetime import UTC, datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, or_, select
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
    RecurringIssueSignal,
    DailyBriefSummary,
    DailyOperationsBrief,
    WorkOrderPriority,
    WorkOrderStatus,
)


APP_TIMEZONE = ZoneInfo(
    os.getenv("APP_TIMEZONE", "Asia/Riyadh")
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

    work_order_fields = work_order_data.model_dump()
    work_order_fields["due_date"] = (
        work_order_data.due_date.astimezone(UTC)
    )

    work_order = WorkOrderModel(**work_order_fields)

    database.add(work_order)
    database.commit()
    database.refresh(work_order)

    return work_order


@app.get("/work-orders", response_model=list[WorkOrder])
def list_work_orders(
    asset_id: UUID | None = None,
    work_order_status: WorkOrderStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: WorkOrderPriority | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    database: Session = Depends(get_db),
) -> list[WorkOrderModel]:
    statement = select(WorkOrderModel)

    if asset_id is not None:
        statement = statement.where(
            WorkOrderModel.asset_id == asset_id
        )

    if work_order_status is not None:
        statement = statement.where(
            WorkOrderModel.status
            == work_order_status.value
        )

    if priority is not None:
        statement = statement.where(
            WorkOrderModel.priority == priority.value
        )

    statement = (
        statement
        .order_by(WorkOrderModel.created_at)
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())


@app.get(
    "/work-orders/overdue",
    response_model=list[WorkOrder],
)
def list_overdue_work_orders(
    database: Session = Depends(get_db),
) -> list[WorkOrderModel]:
    statement = (
        select(WorkOrderModel)
        .where(
            WorkOrderModel.due_date < datetime.now(UTC),
            WorkOrderModel.status.notin_(
                ["completed", "cancelled"]
            ),
        )
        .order_by(WorkOrderModel.due_date)
    )

    return list(database.scalars(statement).all())


@app.get(
    "/work-orders/due-today",
    response_model=list[WorkOrder],
)
def list_due_today_work_orders(
    database: Session = Depends(get_db),
) -> list[WorkOrderModel]:
    local_now = datetime.now(APP_TIMEZONE)
    local_day_start = local_now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    local_next_day = local_day_start + timedelta(days=1)

    utc_day_start = local_day_start.astimezone(UTC)
    utc_next_day = local_next_day.astimezone(UTC)

    statement = (
        select(WorkOrderModel)
        .where(
            WorkOrderModel.due_date >= utc_day_start,
            WorkOrderModel.due_date < utc_next_day,
            WorkOrderModel.status.notin_(
                ["completed", "cancelled"]
            ),
        )
        .order_by(WorkOrderModel.due_date)
    )

    return list(database.scalars(statement).all())


@app.get(
    "/work-orders/high-attention",
    response_model=list[WorkOrder],
)
def list_high_attention_work_orders(
    database: Session = Depends(get_db),
) -> list[WorkOrderModel]:
    statement = (
        select(WorkOrderModel)
        .where(
            WorkOrderModel.status.notin_(
                ["completed", "cancelled"]
            ),
            or_(
                WorkOrderModel.priority.in_(
                    ["high", "critical"]
                ),
                WorkOrderModel.due_date < datetime.now(UTC),
            ),
        )
        .order_by(
            WorkOrderModel.priority.desc(),
            WorkOrderModel.due_date,
        )
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

    update_fields = work_order_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "due_date" in update_fields:
        update_fields["due_date"] = update_fields[
            "due_date"
        ].astimezone(UTC)

    new_status = update_fields.get("status")

    if new_status is not None:
        new_status_value = new_status.value

        allowed_transitions = {
            "open": {
                "in_progress",
                "completed",
                "cancelled",
            },
            "in_progress": {
                "completed",
                "cancelled",
            },
            "completed": set(),
            "cancelled": set(),
        }

        if (
            new_status_value != work_order.status
            and new_status_value
            not in allowed_transitions[work_order.status]
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot transition work order "
                    f"from {work_order.status} "
                    f"to {new_status_value}"
                ),
            )

        update_fields["status"] = new_status_value

    for field, value in update_fields.items():
        setattr(work_order, field, value)

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


@app.get(
    "/insights/recurring-issues",
    response_model=list[RecurringIssueSignal],
)
def list_recurring_issues(
    database: Session = Depends(get_db),
) -> list[RecurringIssueSignal]:
    cutoff_date = datetime.now(UTC) - timedelta(days=90)
    occurrence_count = func.count(WorkOrderModel.id)

    statement = (
        select(
            AssetModel.id.label("asset_id"),
            AssetModel.name.label("asset_name"),
            WorkOrderModel.failure_code.label(
                "failure_code"
            ),
            occurrence_count.label("occurrence_count"),
            func.max(WorkOrderModel.created_at).label(
                "latest_occurrence"
            ),
        )
        .join(
            WorkOrderModel,
            WorkOrderModel.asset_id == AssetModel.id,
        )
        .where(
            WorkOrderModel.failure_code.is_not(None),
            WorkOrderModel.created_at >= cutoff_date,
        )
        .group_by(
            AssetModel.id,
            AssetModel.name,
            WorkOrderModel.failure_code,
        )
        .having(occurrence_count >= 3)
        .order_by(occurrence_count.desc())
    )

    results = database.execute(statement).mappings().all()
    return [RecurringIssueSignal(**result) for result in results]


@app.get(
    "/briefs/daily",
    response_model=DailyOperationsBrief,
)
def get_daily_operations_brief(
    database: Session = Depends(get_db),
) -> DailyOperationsBrief:
    overdue = list_overdue_work_orders(database)
    due_today = list_due_today_work_orders(database)
    high_attention = list_high_attention_work_orders(
        database
    )
    recurring_issues = list_recurring_issues(database)

    return DailyOperationsBrief(
        generated_at=datetime.now(UTC),
        timezone=str(APP_TIMEZONE),
        summary=DailyBriefSummary(
            overdue_count=len(overdue),
            due_today_count=len(due_today),
            high_attention_count=len(high_attention),
            recurring_issue_count=len(recurring_issues),
        ),
        overdue_work_orders=overdue,
        due_today_work_orders=due_today,
        high_attention_work_orders=high_attention,
        recurring_issues=recurring_issues,
    )