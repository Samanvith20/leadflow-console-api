from app.models.integration import IntegrationProvider, IntegrationStatus
from app.schemas.integration import IntegrationRead


def test_integration_schema_never_exposes_encrypted_credentials() -> None:
    assert "credentials_ciphertext" not in IntegrationRead.model_fields


def test_integration_has_hubspot_and_safe_states_for_the_mvp() -> None:
    assert {provider.value for provider in IntegrationProvider} == {"hubspot"}
    assert {status.value for status in IntegrationStatus} == {"connected", "disabled", "error"}
