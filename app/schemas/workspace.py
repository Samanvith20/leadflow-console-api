from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.workspace import WorkspaceStatus


class OrganizationConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    industry: str | None = None
    website_url: HttpUrl | None = None
    business_description: str | None = Field(default=None, max_length=4_000)
    services: list[str] = Field(default_factory=list)
    service_areas: list[str] = Field(default_factory=list)
    ideal_customer: str | None = Field(default=None, max_length=2_000)
    default_language: str = "en"


class AiGuidanceConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    brand_tone: str | None = Field(default=None, max_length=500)
    reply_goal: str | None = Field(default=None, max_length=1_000)
    must_not_claim: list[str] = Field(default_factory=list)
    escalate_when: list[str] = Field(default_factory=list)


class OperationalConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    lead_data_retention_days: int = Field(default=90, ge=1, le=3_650)
    business_hours: dict[str, str] = Field(default_factory=dict)


class WorkspaceConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    organization: OrganizationConfiguration = Field(default_factory=OrganizationConfiguration)
    ai_guidance: AiGuidanceConfiguration = Field(default_factory=AiGuidanceConfiguration)
    operational: OperationalConfiguration = Field(default_factory=OperationalConfiguration)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    timezone: str = Field(min_length=1, max_length=64)
    configuration: WorkspaceConfiguration = Field(default_factory=WorkspaceConfiguration)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    timezone: str
    status: WorkspaceStatus
    configuration: dict[str, Any]
    created_at: datetime
    updated_at: datetime
