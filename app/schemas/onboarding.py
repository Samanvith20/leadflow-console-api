from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.workspace import AiGuidanceConfiguration, OrganizationConfiguration

OnboardingStep = Literal["business_profile", "qualification", "ai_guidance", "connect_source"]


class QualificationConfiguration(BaseModel):
    """Business-owned rules that help Leadflow decide whether an enquiry is worth pursuing."""

    model_config = ConfigDict(extra="forbid")

    ideal_lead_description: str | None = Field(default=None, min_length=30, max_length=2_000)
    must_have: list[str] = Field(default_factory=list, max_length=20)
    disqualifiers: list[str] = Field(default_factory=list, max_length=20)


class OnboardingUpdate(BaseModel):
    """One autosaved wizard step. At least one section or current step must be supplied."""

    model_config = ConfigDict(extra="forbid")

    current_step: OnboardingStep | None = None
    organization: OrganizationConfiguration | None = None
    qualification: QualificationConfiguration | None = None
    ai_guidance: AiGuidanceConfiguration | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "OnboardingUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide onboarding data or a current step")
        return self


class OnboardingRead(BaseModel):
    current_step: OnboardingStep
    completed_at: datetime | None
    organization: OrganizationConfiguration
    qualification: QualificationConfiguration
    ai_guidance: AiGuidanceConfiguration


class OnboardingCompleteResponse(BaseModel):
    completed_at: datetime
