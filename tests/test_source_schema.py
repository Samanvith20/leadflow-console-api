from app.models.source import SourceStatus, SourceType
from app.schemas.source import SourceCreate
from app.services.source_identifiers import create_source_public_id


def test_source_create_uses_empty_configuration_by_default() -> None:
    source = SourceCreate(name="Website Form", source_type=SourceType.WEBSITE_FORM)

    assert source.configuration.fields == []
    assert source.configuration.qualification_rules == []


def test_source_public_id_is_safe_to_expose() -> None:
    public_id = create_source_public_id()

    assert public_id.startswith("src_")
    assert len(public_id) > 20
    assert public_id != create_source_public_id()


def test_source_status_defaults_to_active() -> None:
    assert SourceStatus.ACTIVE.value == "active"
