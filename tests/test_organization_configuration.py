import pytest
from pydantic import ValidationError

from app.schemas.onboarding import QualificationConfiguration
from app.schemas.workspace import OrganizationConfiguration


def test_organization_configuration_trims_and_deduplicates_list_values() -> None:
    configuration = OrganizationConfiguration(
        industry="Marketing agency",
        business_description="We help B2B companies turn website traffic into qualified enquiries.",
        services=[" SEO ", "seo", "Website development"],
        service_areas=[" Hyderabad ", "hyderabad", "Bengaluru"],
    )

    assert configuration.services == ["SEO", "Website development"]
    assert configuration.service_areas == ["Hyderabad", "Bengaluru"]


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("industry", "A"),
        ("business_description", "Too short"),
        ("services", ["  "]),
        ("service_areas", [""]),
    ],
)
def test_organization_configuration_rejects_invalid_values(field_name: str, value: object) -> None:
    values = {
        "industry": "Marketing agency",
        "business_description": "We help B2B companies turn website traffic into qualified enquiries.",
        "services": ["SEO"],
        "service_areas": ["Hyderabad"],
    }
    values[field_name] = value

    with pytest.raises(ValidationError):
        OrganizationConfiguration(**values)


def test_qualification_configuration_requires_a_useful_ideal_lead_description() -> None:
    with pytest.raises(ValidationError):
        QualificationConfiguration(ideal_lead_description="Too short")
