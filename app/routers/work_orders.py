from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import APP_TIMEZONE
from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import (
    WorkOrder,
    WorkOrderCreate,
    WorkOrderPriority,
    WorkOrderStatus,
    WorkOrderUpdate,
)
from app.security import require_api_key

router = APIRouter(
    prefix="/work-orders",
    tags=["Work Orders"],
)


def find_work_order(
    work_order_id: UUID,
    database: Session,
) -> WorkOrderModel:
    work_order = database.get(
        WorkOrderModel,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    return work_order


@router.post(
    "",
    response_model=WorkOrder,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
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


@router.get("", response_model=list[WorkOrder])
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


@router.get(
    "/overdue",
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


@router.get(
    "/due-today",
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


@router.get(
    "/high-attention",
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


@router.get(
    "/{work_order_id}",
    response_model=WorkOrder,
)
def get_work_order(
    work_order_id: UUID,
    database: Session = Depends(get_db),
) -> WorkOrderModel:
    return find_work_order(work_order_id, database)


@router.patch(
    "/{work_order_id}",
    response_model=WorkOrder,
    dependencies=[Depends(require_api_key)],
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
    database.commit()
    database.refresh(work_order)

    return work_order


@router.delete(
    "/{work_order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_work_order(
    work_order_id: UUID,
    database: Session = Depends(get_db),
) -> None:
    work_order = find_work_order(work_order_id, database)

    database.delete(work_order)
    database.commit()