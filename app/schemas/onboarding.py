from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.workspace import (
    AiGuidanceConfiguration,
    OrganizationConfiguration,
    QualificationConfiguration,
)

OnboardingStep = Literal["business_profile", "qualification", "ai_guidance", "connect_source"]


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
