from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.audit_event import AuditEventRead


def test_audit_event_schema_returns_database_metadata_as_metadata() -> None:
    event = AuditEventRead(
        id=uuid4(),
        workspace_id=uuid4(),
        actor_user_id=None,
        action="lead.status_changed",
        entity_type="lead",
        entity_id=uuid4(),
        metadata_json={"from": "new", "to": "contacted"},
        occurred_at=datetime.now(UTC),
    )

    assert event.metadata == {"from": "new", "to": "contacted"}
