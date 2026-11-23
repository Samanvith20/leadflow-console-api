from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.intake_event import IntakeEventStatus


class IntakeEventReceipt(BaseModel):
    """Safe webhook receipt returned to a sender after durable event acceptance."""

    receipt_id: UUID
    status: IntakeEventStatus
    already_received: bool = False


class IntakeEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    source_id: UUID
    source_event_id: str
    payload_hash: str
    status: IntakeEventStatus
    mapping_warnings: list[dict[str, Any]]
    received_at: datetime
    processed_at: datetime | None
    purge_at: datetime
