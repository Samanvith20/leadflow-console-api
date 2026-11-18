import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def record_audit_event(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Queue a safe audit record inside the caller's existing database transaction."""
    event = AuditEvent(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
