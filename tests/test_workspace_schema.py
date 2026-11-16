import pytest
from pydantic import ValidationError

from app.schemas.workspace import WorkspaceCreate


def test_workspace_create_uses_default_configuration() -> None:
    workspace = WorkspaceCreate(name="Hyderabad Interiors", timezone="Asia/Kolkata")

    assert workspace.configuration.operational.lead_data_retention_days == 90
    assert workspace.configuration.organization.services == []


def test_workspace_configuration_allows_future_extension_fields() -> None:
    workspace = WorkspaceCreate.model_validate(
        {
            "name": "Hyderabad Interiors",
            "timezone": "Asia/Kolkata",
            "configuration": {
                "organization": {"industry": "Interior design", "future_brand_field": "value"},
                "ai_guidance": {"brand_tone": "Helpful, professional, concise"},
                "operational": {"lead_data_retention_days": 90},
            },
        }
    )

    assert workspace.configuration.organization.industry == "Interior design"
    assert workspace.configuration.organization.model_extra == {"future_brand_field": "value"}


def test_workspace_configuration_rejects_invalid_retention_period() -> None:
    with pytest.raises(ValidationError):
        WorkspaceCreate.model_validate(
            {
                "name": "Hyderabad Interiors",
                "timezone": "Asia/Kolkata",
                "configuration": {"operational": {"lead_data_retention_days": 0}},
            }
        )
