from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import APP_TIMEZONE
from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import (
    AssetReliabilityRanking,
    BacklogAgeBucket,
    MonthlyPMCompliance,
    MonthlyPMTrendPoint,
    RecurringIssueSignal,
    WorkOrderBacklogAging,
    YearToDatePMCompliance,
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

@router.get(
    "/ytd-pm-compliance",
    response_model=YearToDatePMCompliance,
)
def get_ytd_pm_compliance(
    database: Session = Depends(get_db),
) -> YearToDatePMCompliance:
    local_now = datetime.now(APP_TIMEZONE)

    local_year_start = local_now.replace(
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if local_now.month == 12:
        local_next_month = local_year_start.replace(
            year=local_now.year + 1,
        )
    else:
        local_next_month = local_now.replace(
            month=local_now.month + 1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    utc_year_start = local_year_start.astimezone(UTC)
    utc_next_month = local_next_month.astimezone(UTC)

    statement = select(WorkOrderModel).where(
        WorkOrderModel.maintenance_type == "preventive",
        WorkOrderModel.due_date >= utc_year_start,
        WorkOrderModel.due_date < utc_next_month,
        WorkOrderModel.status != "cancelled",
    )

    work_orders = list(
        database.scalars(statement).all()
    )

    monthly_counts = {
        month_number: {
            "planned": 0,
            "completed": 0,
        }
        for month_number in range(
            1,
            local_now.month + 1,
        )
    }

    for work_order in work_orders:
        due_date = work_order.due_date

        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)

        local_due_date = due_date.astimezone(
            APP_TIMEZONE
        )
        month_counts = monthly_counts[
            local_due_date.month
        ]

        month_counts["planned"] += 1

        if work_order.status == "completed":
            month_counts["completed"] += 1

    months = []

    for month_number, counts in monthly_counts.items():
        planned_count = counts["planned"]
        completed_count = counts["completed"]

        completion_percentage = (
            round(
                completed_count / planned_count * 100,
                1,
            )
            if planned_count
            else 0.0
        )

        months.append(
            MonthlyPMTrendPoint(
                month=f"{local_now.year}-{month_number:02d}",
                planned_count=planned_count,
                completed_count=completed_count,
                completion_percentage=completion_percentage,
            )
        )

    planned_count = sum(
        month.planned_count for month in months
    )
    completed_count = sum(
        month.completed_count for month in months
    )

    completion_percentage = (
        round(completed_count / planned_count * 100, 1)
        if planned_count
        else 0.0
    )

    return YearToDatePMCompliance(
        year=local_now.year,
        timezone=str(APP_TIMEZONE),
        planned_count=planned_count,
        completed_count=completed_count,
        completion_percentage=completion_percentage,
        months=months,
    )

@router.get(
    "/work-order-backlog-aging",
    response_model=WorkOrderBacklogAging,
)
def get_work_order_backlog_aging(
    database: Session = Depends(get_db),
) -> WorkOrderBacklogAging:
    now = datetime.now(UTC)

    statement = (
        select(WorkOrderModel)
        .where(
            WorkOrderModel.status.not_in(
                ["completed", "cancelled"]
            )
        )
        .order_by(WorkOrderModel.created_at)
    )

    work_orders = list(
        database.scalars(statement).all()
    )

    ages: list[int] = []

    for work_order in work_orders:
        created_at = work_order.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        age_days = max(
            (now - created_at.astimezone(UTC)).days,
            0,
        )
        ages.append(age_days)

    bucket_definitions = [
        ("0–7 days", 0, 7),
        ("8–30 days", 8, 30),
        ("31–60 days", 31, 60),
        ("More than 60 days", 61, None),
    ]

    buckets = []

    for label, minimum_days, maximum_days in bucket_definitions:
        count = sum(
            1
            for age in ages
            if age >= minimum_days
            and (
                maximum_days is None
                or age <= maximum_days
            )
        )

        buckets.append(
            BacklogAgeBucket(
                label=label,
                minimum_days=minimum_days,
                maximum_days=maximum_days,
                work_order_count=count,
            )
        )

    return WorkOrderBacklogAging(
        generated_at=now,
        timezone=str(APP_TIMEZONE),
        total_backlog_count=len(work_orders),
        average_age_days=(
            round(sum(ages) / len(ages), 1)
            if ages
            else 0.0
        ),
        oldest_age_days=max(ages, default=0),
        buckets=buckets,
    )


@router.get(
    "/asset-reliability-ranking",
    response_model=list[AssetReliabilityRanking],
)
def list_asset_reliability_ranking(
    database: Session = Depends(get_db),
) -> list[AssetReliabilityRanking]:
    now = datetime.now(UTC)

    assets = list(
        database.scalars(
            select(AssetModel).order_by(AssetModel.name)
        ).all()
    )
    active_work_orders = list(
        database.scalars(
            select(WorkOrderModel).where(
                WorkOrderModel.status.not_in(
                    ["completed", "cancelled"]
                )
            )
        ).all()
    )
    recurring_issues = list_recurring_issues(database)

    rankings = []

    for asset in assets:
        asset_work_orders = [
            work_order
            for work_order in active_work_orders
            if work_order.asset_id == asset.id
        ]

        overdue_count = sum(
            1
            for work_order in asset_work_orders
            if (
                work_order.due_date.replace(
                    tzinfo=UTC
                )
                if work_order.due_date.tzinfo is None
                else work_order.due_date.astimezone(UTC)
            )
            < now
        )

        high_priority_count = sum(
            1
            for work_order in asset_work_orders
            if work_order.priority in ["high", "critical"]
        )

        recurring_count = sum(
            1
            for issue in recurring_issues
            if issue.asset_id == asset.id
        )

        active_count = len(asset_work_orders)
        risk_score = (
            active_count
            + overdue_count * 3
            + high_priority_count * 2
            + recurring_count * 4
        )

        rankings.append(
            AssetReliabilityRanking(
                asset_id=asset.id,
                asset_name=asset.name,
                asset_tag=asset.asset_tag,
                active_work_order_count=active_count,
                overdue_work_order_count=overdue_count,
                high_priority_work_order_count=(
                    high_priority_count
                ),
                recurring_issue_count=recurring_count,
                risk_score=risk_score,
            )
        )

    return sorted(
        rankings,
        key=lambda ranking: (
            -ranking.risk_score,
            ranking.asset_name,
        ),
    )