from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import APP_TIMEZONE
from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import (
    MonthlyPMCompliance,
    RecurringIssueSignal,
)


router = APIRouter(
    prefix="/insights",
    tags=["Insights"],
)


@router.get(
    "/recurring-issues",
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

    return [
        RecurringIssueSignal(**result)
        for result in results
    ]


@router.get(
    "/monthly-pm-compliance",
    response_model=MonthlyPMCompliance,
)
def get_monthly_pm_compliance(
    database: Session = Depends(get_db),
) -> MonthlyPMCompliance:
    local_now = datetime.now(APP_TIMEZONE)

    local_month_start = local_now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if local_month_start.month == 12:
        local_next_month = local_month_start.replace(
            year=local_month_start.year + 1,
            month=1,
        )
    else:
        local_next_month = local_month_start.replace(
            month=local_month_start.month + 1,
        )

    local_next_day = local_now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=1)

    utc_month_start = local_month_start.astimezone(UTC)
    utc_next_month = local_next_month.astimezone(UTC)
    utc_next_day = local_next_day.astimezone(UTC)
    utc_now = local_now.astimezone(UTC)

    def due_date_as_utc(
        work_order: WorkOrderModel,
    ) -> datetime:
        due_date = work_order.due_date

        if due_date.tzinfo is None:
            return due_date.replace(tzinfo=UTC)

        return due_date.astimezone(UTC)

    statement = (
        select(WorkOrderModel)
        .where(
            WorkOrderModel.maintenance_type
            == "preventive",
            WorkOrderModel.due_date >= utc_month_start,
            WorkOrderModel.due_date < utc_next_month,
            WorkOrderModel.status != "cancelled",
        )
        .order_by(WorkOrderModel.due_date)
    )

    planned_work_orders = list(
        database.scalars(statement).all()
    )

    completed_work_orders = [
        work_order
        for work_order in planned_work_orders
        if work_order.status == "completed"
    ]
    remaining_work_orders = [
        work_order
        for work_order in planned_work_orders
        if work_order.status != "completed"
    ]

    planned_to_date = [
        work_order
        for work_order in planned_work_orders
        if due_date_as_utc(work_order) < utc_next_day
    ]

    completed_to_date = [
        work_order
        for work_order in planned_to_date
        if work_order.status == "completed"
    ]

    overdue_work_orders = [
        work_order
        for work_order in planned_work_orders
        if (
            due_date_as_utc(work_order) < utc_now
            and work_order.status != "completed"
        )
    ]

    planned_count = len(planned_work_orders)
    completed_count = len(completed_work_orders)
    remaining_count = planned_count - completed_count

    calendar_days_remaining = (
        local_next_month.date() - local_now.date()
    ).days

    completion_percentage = (
        round(completed_count / planned_count * 100, 1)
        if planned_count
        else 0.0
    )

    required_per_day = (
        round(
            remaining_count / calendar_days_remaining,
            2,
        )
        if calendar_days_remaining
        else 0.0
    )

    return MonthlyPMCompliance(
        month=local_now.strftime("%Y-%m"),
        timezone=str(APP_TIMEZONE),
        planned_count=planned_count,
        completed_count=completed_count,
        remaining_count=remaining_count,
        planned_to_date_count=len(planned_to_date),
        completed_to_date_count=len(completed_to_date),
        overdue_count=len(overdue_work_orders),
        completion_percentage=completion_percentage,
        on_plan=(
            len(completed_to_date)
            >= len(planned_to_date)
        ),
        calendar_days_remaining=calendar_days_remaining,
        required_per_day=required_per_day,
        planned_work_orders=planned_work_orders,
        completed_work_orders=completed_work_orders,
        remaining_work_orders=remaining_work_orders,
        overdue_work_orders=overdue_work_orders,
    )