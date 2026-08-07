from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssetModel, WorkOrderModel
from app.schemas import RecurringIssueSignal


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