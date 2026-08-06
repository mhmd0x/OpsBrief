from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from enum import StrEnum

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