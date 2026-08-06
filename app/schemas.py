from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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