from uuid import uuid4

from app.models.intake_event import IntakeEventStatus
from app.schemas.intake_event import IntakeEventReceipt


def test_webhook_receipt_marks_an_idempotent_redelivery() -> None:
    receipt = IntakeEventReceipt(
        receipt_id=uuid4(),
        status=IntakeEventStatus.PROCESSED,
        already_received=True,
    )

    assert receipt.already_received is True
