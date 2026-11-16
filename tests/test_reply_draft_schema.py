from app.models.reply_draft import ReplyDraftStatus
from app.schemas.reply_draft import ReplyDraftUpdate


def test_reply_draft_update_accepts_a_subject_and_body() -> None:
    update = ReplyDraftUpdate(subject="Re: Your enquiry", body="Thanks for contacting us.")

    assert update.subject == "Re: Your enquiry"
    assert update.body == "Thanks for contacting us."


def test_reply_draft_update_rejects_a_blank_body() -> None:
    try:
        ReplyDraftUpdate(body="")
    except ValueError as error:
        assert "at least 1 character" in str(error)
    else:
        raise AssertionError("Expected a blank reply body to be rejected")


def test_reply_draft_status_has_the_mvp_approval_states() -> None:
    assert {status.value for status in ReplyDraftStatus} == {"draft", "approved", "discarded"}
