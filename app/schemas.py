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


class MaintenanceType(StrEnum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    INSPECTION = "inspection"


class WorkOrderCreate(BaseModel):
    asset_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    maintenance_type: MaintenanceType = MaintenanceType.CORRECTIVE
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
    maintenance_type: MaintenanceType | None = None
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
    maintenance_type: MaintenanceType
    completed_at: datetime | None
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
    due_soon_count: int
    high_attention_count: int
    recurring_issue_count: int


class DailyOperationsBrief(BaseModel):
    generated_at: datetime
    timezone: str
    summary: DailyBriefSummary
    overdue_work_orders: list[WorkOrder]
    due_today_work_orders: list[WorkOrder]
    due_soon_work_orders: list[WorkOrder]
    high_attention_work_orders: list[WorkOrder]
    recurring_issues: list[RecurringIssueSignal]


class MonthlyPMCompliance(BaseModel):
    month: str
    timezone: str
    planned_count: int
    completed_count: int
    remaining_count: int
    planned_to_date_count: int
    completed_to_date_count: int
    overdue_count: int
    completion_percentage: float
    on_plan: bool
    calendar_days_remaining: int
    required_per_day: float
    planned_work_orders: list[WorkOrder]
    completed_work_orders: list[WorkOrder]
    remaining_work_orders: list[WorkOrder]
    overdue_work_orders: list[WorkOrder]


class MonthlyPMTrendPoint(BaseModel):
    month: str
    planned_count: int
    completed_count: int
    completion_percentage: float


class YearToDatePMCompliance(BaseModel):
    year: int
    timezone: str
    planned_count: int
    completed_count: int
    completion_percentage: float
    months: list[MonthlyPMTrendPoint]


class BacklogAgeBucket(BaseModel):
    label: str
    minimum_days: int
    maximum_days: int | None
    work_order_count: int


class WorkOrderBacklogAging(BaseModel):
    generated_at: datetime
    timezone: str
    total_backlog_count: int
    average_age_days: float
    oldest_age_days: int
    buckets: list[BacklogAgeBucket]


class AssetReliabilityRanking(BaseModel):
    asset_id: UUID
    asset_name: str
    asset_tag: str
    active_work_order_count: int
    overdue_work_order_count: int
    high_priority_work_order_count: int
    recurring_issue_count: int
    risk_score: int