from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    asset_tag: str = Field(min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=100)


class Asset(AssetCreate):
    id: UUID
    created_at: datetime