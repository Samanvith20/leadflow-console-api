from uuid import uuid4

from app.models.lead import LeadStatus
from app.schemas.lead import LeadUpdate


def test_lead_update_accepts_human_assignment_and_status_change() -> None:
    assignee_id = uuid4()

    update = LeadUpdate(assignee_user_id=assignee_id, lead_status="contacted")

    assert update.assignee_user_id == assignee_id
    assert update.lead_status is LeadStatus.CONTACTED


def test_lead_update_rejects_an_overlong_enquiry_message() -> None:
    message = "x" * 20_001

    try:
        LeadUpdate(enquiry_message=message)
    except ValueError as error:
        assert "20000" in str(error)
    else:
        raise AssertionError("Expected an overlong enquiry message to be rejected")
