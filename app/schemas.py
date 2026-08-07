from datetime import datetime
from uuid import UUID
from enum import StrEnum
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    asset_tag: str = Field(min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=100)


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    asset_tag: str | None = Field(default=None, min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=100)
    

class Asset(AssetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class WorkOrderPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkOrderStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderCreate(BaseModel):
    asset_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    due_date: datetime
    failure_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
)
    
    @field_validator("due_date")
    @classmethod
    def due_date_must_include_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "due_date must include a timezone"
            )

        return value

class WorkOrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: WorkOrderPriority | None = None
    status: WorkOrderStatus | None = None
    due_date: datetime | None = None
    failure_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
)

    @field_validator("due_date")
    @classmethod
    def updated_due_date_must_include_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if (
            value is not None
            and (
                value.tzinfo is None
                or value.utcoffset() is None
            )
        ):
            raise ValueError(
                "due_date must include a timezone"
            )

        return value

class WorkOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    title: str
    description: str | None
    priority: WorkOrderPriority
    status: WorkOrderStatus
    due_date: datetime
    created_at: datetime
    updated_at: datetime
    failure_code: str | None


class RecurringIssueSignal(BaseModel):
    asset_id: UUID
    asset_name: str
    failure_code: str
    occurrence_count: int
    latest_occurrence: datetime


class DailyBriefSummary(BaseModel):
    overdue_count: int
    due_today_count: int
    high_attention_count: int
    recurring_issue_count: int


class DailyOperationsBrief(BaseModel):
    generated_at: datetime
    timezone: str
    summary: DailyBriefSummary
    overdue_work_orders: list[WorkOrder]
    due_today_work_orders: list[WorkOrder]
    high_attention_work_orders: list[WorkOrder]
    recurring_issues: list[RecurringIssueSignal]


