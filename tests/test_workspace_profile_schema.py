import pytest
from pydantic import ValidationError

from app.schemas.workspace import OrganizationConfiguration, WorkspaceProfileUpdate


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
    )

    assert profile.organization is not None
    assert profile.organization.services == ["SEO"]


def test_workspace_profile_update_requires_a_change() -> None:
    with pytest.raises(ValidationError):
        WorkspaceProfileUpdate()
