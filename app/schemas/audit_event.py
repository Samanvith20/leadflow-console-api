from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRead(BaseModel):
    """Safe audit data for authorised workspace users."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    workspace_id: UUID
    actor_user_id: UUID | None
    action: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: UUID
    metadata: dict[str, Any] = Field(
        validation_alias="metadata_json", serialization_alias="metadata"
    )
    occurred_at: datetime
