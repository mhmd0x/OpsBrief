from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import APP_TIMEZONE
from app.database import get_db
from app.routers.insights import list_recurring_issues
from app.routers.work_orders import (
    list_due_today_work_orders,
    list_high_attention_work_orders,
    list_overdue_work_orders,
)
from app.schemas import (
    DailyBriefSummary,
    DailyOperationsBrief,
)


router = APIRouter(
    prefix="/briefs",
    tags=["Briefs"],
)


@router.get(
    "/daily",
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