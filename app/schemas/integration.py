from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.integration import IntegrationProvider, IntegrationStatus


class IntegrationRead(BaseModel):
    """Integration data safe for the workspace UI; encrypted credentials stay private."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    provider: IntegrationProvider
    external_account_id: str | None
    configuration: dict[str, Any]
    status: IntegrationStatus
    last_synced_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
