from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.source import SourceStatus, SourceType


class SourceConfiguration(BaseModel):
    """Source-specific workflow settings; each section becomes active in later features."""

    model_config = ConfigDict(extra="allow")

    fields: list[dict[str, Any]] = Field(default_factory=list)
    field_mappings: dict[str, str] = Field(default_factory=dict)
    qualification_rules: list[dict[str, Any]] = Field(default_factory=list)
    reply_guidance: str | None = Field(default=None, max_length=4_000)
    crm_mapping: dict[str, str] = Field(default_factory=dict)


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    source_type: SourceType
    configuration: SourceConfiguration = Field(default_factory=SourceConfiguration)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    source_type: SourceType
    public_id: str
    status: SourceStatus
    configuration: dict[str, Any]
    created_at: datetime
    updated_at: datetime
