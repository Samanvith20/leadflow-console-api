from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.background_job import JobStatus, JobType


class BackgroundJobRead(BaseModel):
    """Internal job state; this is not exposed to webhook senders."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    intake_event_id: UUID | None
    lead_id: UUID | None
    job_type: JobType
    status: JobStatus
    job_key: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int
    run_after: datetime
    locked_at: datetime | None
    locked_by: str | None
    last_error: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
