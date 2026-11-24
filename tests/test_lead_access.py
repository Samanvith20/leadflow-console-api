from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models.lead import Lead, LeadStatus
from app.models.user import UserRole
from app.schemas.lead import LeadUpdate
from app.services.leads import LeadPermissionError, LeadService


def test_standard_user_scope_always_contains_their_assignee_id() -> None:
    actor = SimpleNamespace(id=uuid4(), workspace_id=uuid4(), role=UserRole.USER)
    service = LeadService(SimpleNamespace())

    statement = select(Lead).where(*service._scope_conditions(actor, assignment="all"))
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "leads.assignee_user_id" in compiled
    assert actor.id.hex in compiled


def test_standard_user_cannot_reassign_a_lead() -> None:
    actor = SimpleNamespace(id=uuid4(), workspace_id=uuid4(), role=UserRole.USER)
    lead = SimpleNamespace(id=uuid4())
    service = LeadService(SimpleNamespace())
    service._get_authorised_lead = lambda _actor, _lead_id: lead  # type: ignore[method-assign]

    with pytest.raises(LeadPermissionError):
        service.update(actor, lead.id, LeadUpdate(assignee_user_id=uuid4()))


def test_lead_update_can_explicitly_set_a_status() -> None:
    update = LeadUpdate(lead_status=LeadStatus.CONTACTED)

    assert update.model_fields_set == {"lead_status"}


def test_empty_lead_update_is_rejected_by_service_not_schema() -> None:
    update = LeadUpdate()

    assert update.model_fields_set == set()
    with pytest.raises(ValidationError):
        LeadUpdate(lead_status="not-a-real-status")
