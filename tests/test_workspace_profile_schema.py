import pytest
from pydantic import ValidationError

from app.schemas.workspace import (
    AiGuidanceConfiguration,
    OrganizationConfiguration,
    QualificationConfiguration,
    WorkspaceProfileUpdate,
)


def test_workspace_profile_update_accepts_saved_business_profile() -> None:
    profile = WorkspaceProfileUpdate(
        name="BrightPath Growth",
        timezone="Asia/Kolkata",
        organization=OrganizationConfiguration(
            industry="Marketing agency",
            business_description="We help B2B companies turn website traffic into qualified enquiries.",
            services=["SEO"],
            service_areas=["Hyderabad"],
        ),
        qualification=QualificationConfiguration(
            ideal_lead_description="B2B business owners who need qualified website leads this month."
        ),
        ai_guidance=AiGuidanceConfiguration(
            brand_tone="Helpful and professional",
            reply_goal="Book a consultation",
        ),
    )

    assert profile.organization is not None
    assert profile.organization.services == ["SEO"]
    assert profile.qualification is not None
    assert profile.ai_guidance is not None


def test_workspace_profile_update_requires_a_change() -> None:
    with pytest.raises(ValidationError):
        WorkspaceProfileUpdate()
