from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import APP_TIMEZONE
from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.routers.assets import router as assets_router
from app.routers.work_orders import (
    list_due_today_work_orders,
    list_high_attention_work_orders,
    list_overdue_work_orders,
    router as work_orders_router,
)
from app.schemas import (
    DailyBriefSummary,
    DailyOperationsBrief,
    RecurringIssueSignal,
)


app = FastAPI(
    title="OpsBrief API",
    description="Decision-support API for maintenance operations.",
    version="0.1.0",
)

app.include_router(assets_router)
app.include_router(work_orders_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


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
    return [
        RecurringIssueSignal(**result)
        for result in results
    ]


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