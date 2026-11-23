from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.workspace import WorkspaceStatus

ShortListItem = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class OrganizationConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    industry: str | None = Field(default=None, min_length=2, max_length=100)
    website_url: HttpUrl | None = None
    business_description: str | None = Field(default=None, min_length=20, max_length=4_000)
    services: list[ShortListItem] = Field(default_factory=list, max_length=20)
    service_areas: list[ShortListItem] = Field(default_factory=list, max_length=20)
    ideal_customer: str | None = Field(default=None, max_length=2_000)
    default_language: str = "en"

    @field_validator("services", "service_areas")
    @classmethod
    def normalize_unique_list_items(cls, values: list[str]) -> list[str]:
        """Keep clean display values while preventing duplicates that differ only by case."""
        normalized_values: list[str] = []
        seen: set[str] = set()
        for value in values:
            comparison_value = value.casefold()
            if comparison_value not in seen:
                normalized_values.append(value)
                seen.add(comparison_value)
        return normalized_values


class AiGuidanceConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    brand_tone: str | None = Field(default=None, max_length=500)
    reply_goal: str | None = Field(default=None, max_length=1_000)
    must_not_claim: list[str] = Field(default_factory=list)
    escalate_when: list[str] = Field(default_factory=list)


class QualificationConfiguration(BaseModel):
    """Business-owned criteria that determine whether an enquiry deserves attention."""

    model_config = ConfigDict(extra="forbid")

    ideal_lead_description: str | None = Field(default=None, min_length=30, max_length=2_000)
    must_have: list[str] = Field(default_factory=list, max_length=20)
    disqualifiers: list[str] = Field(default_factory=list, max_length=20)


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
    onboarding_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkspaceProfileRead(BaseModel):
    """The manager-editable business profile used by qualification and reply drafts."""

    id: UUID
    name: str
    timezone: str
    organization: OrganizationConfiguration
    qualification: QualificationConfiguration
    ai_guidance: AiGuidanceConfiguration


class WorkspaceProfileUpdate(BaseModel):
    """A partial manager-only update to the workspace's business profile."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=150)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    organization: OrganizationConfiguration | None = None
    qualification: QualificationConfiguration | None = None
    ai_guidance: AiGuidanceConfiguration | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "WorkspaceProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile value to update")
        return self
