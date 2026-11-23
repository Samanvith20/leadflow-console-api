from app.models.source import SourceStatus, SourceType
from app.schemas.source import SourceCreate
from app.services.source_identifiers import create_source_public_id


def test_manual_source_can_use_empty_configuration_by_default() -> None:
    source = SourceCreate(name="Manual entry", source_type=SourceType.MANUAL_ENTRY)

    assert source.configuration.field_definitions == []


def test_source_public_id_is_safe_to_expose() -> None:
    public_id = create_source_public_id()

    assert public_id.startswith("src_")
    assert len(public_id) > 20
    assert public_id != create_source_public_id()


def test_source_status_defaults_to_active() -> None:
    assert SourceStatus.ACTIVE.value == "active"
