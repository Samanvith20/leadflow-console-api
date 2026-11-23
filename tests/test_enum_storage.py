import pytest

from app.models.auth_token import AuthToken, AuthTokenPurpose
from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.models.intake_event import IntakeEvent, IntakeEventStatus
from app.models.integration import Integration, IntegrationProvider, IntegrationStatus
from app.models.lead import CrmSyncStatus, Lead, LeadStatus, QualificationStatus
from app.models.reply_draft import ReplyDraft, ReplyDraftStatus
from app.models.source import Source, SourceStatus, SourceType
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceStatus


@pytest.mark.parametrize(
    ("enum_class", "uppercase_input", "expected"),
    [
        (WorkspaceStatus, "ACTIVE", WorkspaceStatus.ACTIVE),
        (UserRole, "MANAGER", UserRole.MANAGER),
        (SourceType, "WEBSITE_FORM", SourceType.WEBSITE_FORM),
        (SourceStatus, "PAUSED", SourceStatus.PAUSED),
        (AuthTokenPurpose, "PASSWORD_RESET", AuthTokenPurpose.PASSWORD_RESET),
        (ReplyDraftStatus, "APPROVED", ReplyDraftStatus.APPROVED),
        (JobType, "SYNC_CRM", JobType.SYNC_CRM),
        (JobStatus, "RETRY_SCHEDULED", JobStatus.RETRY_SCHEDULED),
        (IntakeEventStatus, "PROCESSED", IntakeEventStatus.PROCESSED),
        (IntegrationProvider, "HUBSPOT", IntegrationProvider.HUBSPOT),
        (IntegrationStatus, "CONNECTED", IntegrationStatus.CONNECTED),
        (LeadStatus, "CLOSED_WON", LeadStatus.CLOSED_WON),
        (QualificationStatus, "NEEDS_REVIEW", QualificationStatus.NEEDS_REVIEW),
        (CrmSyncStatus, "NOT_REQUIRED", CrmSyncStatus.NOT_REQUIRED),
    ],
)
def test_enum_input_is_case_insensitive(enum_class, uppercase_input, expected) -> None:
    assert enum_class(uppercase_input) is expected


@pytest.mark.parametrize(
    ("column", "expected_values"),
    [
        (Workspace.__table__.c.status, ["active", "paused"]),
        (User.__table__.c.role, ["manager", "user"]),
        (
            Source.__table__.c.source_type,
            [
                "website_form",
                "meta",
                "generic_webhook",
                "csv_import",
                "manual_entry",
                "web_chat",
                "whatsapp",
            ],
        ),
        (Source.__table__.c.status, ["active", "paused", "archived"]),
        (AuthToken.__table__.c.purpose, ["password_reset", "email_verification"]),
        (ReplyDraft.__table__.c.status, ["draft", "approved", "discarded"]),
        (
            BackgroundJob.__table__.c.job_type,
            ["process_intake", "qualify_lead", "generate_reply", "sync_crm"],
        ),
        (
            BackgroundJob.__table__.c.status,
            ["queued", "running", "succeeded", "retry_scheduled", "failed"],
        ),
        (IntakeEvent.__table__.c.status, ["pending", "quarantined", "processed", "failed"]),
        (Integration.__table__.c.provider, ["hubspot"]),
        (Integration.__table__.c.status, ["connected", "disabled", "error"]),
        (
            Lead.__table__.c.lead_status,
            ["new", "in_progress", "contacted", "closed_won", "closed_lost"],
        ),
        (
            Lead.__table__.c.qualification_status,
            ["pending", "hot", "warm", "needs_review", "not_a_fit"],
        ),
        (Lead.__table__.c.crm_sync_status, ["not_required", "pending", "synced", "failed"]),
    ],
)
def test_sqlalchemy_persists_lowercase_enum_values(column, expected_values) -> None:
    assert column.type.enums == expected_values
