"""Role-scoped lead retrieval, assignment, status updates, and dashboard summaries."""

from typing import Literal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.audit_event import AuditEvent
from app.models.contact import Contact
from app.models.intake_event import IntakeEvent
from app.models.lead import Lead, LeadStatus, QualificationStatus
from app.models.reply_draft import ReplyDraft, ReplyDraftStatus
from app.models.source import Source
from app.models.user import User, UserRole
from app.schemas.audit_event import AuditEventRead
from app.schemas.dashboard import DashboardMetrics, DashboardRead
from app.schemas.lead import (
    LeadAssigneeSummary,
    LeadContactSummary,
    LeadDetailRead,
    LeadListResponse,
    LeadSourceSummary,
    LeadSummaryRead,
    LeadUpdate,
)
from app.services.audit import record_audit_event

AssignmentFilter = Literal["all", "mine", "unassigned"]


class LeadNotFoundError(Exception):
    """Raised without revealing whether a lead exists in another workspace."""


class LeadPermissionError(Exception):
    """Raised when a standard User attempts a Manager-only lead action."""


class DashboardPermissionError(Exception):
    """Raised when a standard User requests the Manager overview."""


class LeadValidationError(Exception):
    """Raised for valid JSON that is not a permitted lead change."""


class LeadService:
    """Use workspace and role scope on every lead read and write."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_leads(
        self,
        actor: User,
        *,
        lead_status: LeadStatus | None,
        qualification_status: QualificationStatus | None,
        assignment: AssignmentFilter,
        limit: int,
        offset: int,
    ) -> LeadListResponse:
        """Return a filtered, paginated lead list limited to the actor's permitted scope."""
        conditions = self._scope_conditions(
            actor,
            lead_status=lead_status,
            qualification_status=qualification_status,
            assignment=assignment,
        )
        total = self._db.scalar(select(func.count()).select_from(Lead).where(*conditions)) or 0
        rows = self._summary_statement(conditions).order_by(Lead.updated_at.desc()).limit(limit).offset(
            offset
        )
        return LeadListResponse(
            items=[self._to_summary(*row) for row in self._db.execute(rows).all()],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, actor: User, lead_id: UUID) -> LeadDetailRead:
        """Return one authorised lead with contact, source, and assignee summaries."""
        row = self._db.execute(
            self._summary_statement(self._scope_conditions(actor)).where(Lead.id == lead_id)
        ).one_or_none()
        if row is None:
            raise LeadNotFoundError
        lead, contact, source, assignee = row
        summary = self._to_summary(lead, contact, source, assignee)
        return LeadDetailRead(
            **summary.model_dump(),
            custom_fields=lead.custom_fields,
            qualification_reason=lead.qualification_reason,
            crm_sync_status=lead.crm_sync_status,
        )

    def update(self, actor: User, lead_id: UUID, payload: LeadUpdate) -> LeadDetailRead:
        """Apply a permitted human lead action and record a complete audit timeline."""
        lead = self._get_authorised_lead(actor, lead_id)
        changed_fields = payload.model_fields_set
        if not changed_fields:
            raise LeadValidationError("Provide at least one lead field to update")

        manager_only_fields = {"assignee_user_id", "enquiry_message", "custom_fields"}
        if actor.role is UserRole.USER and changed_fields.intersection(manager_only_fields):
            raise LeadPermissionError("Users can update only the status of their assigned leads")
        if actor.role is UserRole.USER and "lead_status" not in changed_fields:
            raise LeadValidationError("Choose a lead status to update")

        if "assignee_user_id" in changed_fields:
            self._update_assignee(actor, lead, payload.assignee_user_id)
        if "lead_status" in changed_fields and payload.lead_status is not None:
            self._update_status(actor, lead, payload.lead_status)
        if actor.role is UserRole.MANAGER and "enquiry_message" in changed_fields:
            lead.enquiry_message = payload.enquiry_message
        if actor.role is UserRole.MANAGER and "custom_fields" in changed_fields:
            lead.custom_fields = payload.custom_fields or {}

        self._db.commit()
        return self.get(actor, lead.id)

    def dashboard(self, manager: User) -> DashboardRead:
        """Return Manager-only operational counts, attention queue, and recent audit activity."""
        if manager.role is not UserRole.MANAGER:
            raise DashboardPermissionError("Only workspace Managers can view the overview")
        workspace_condition = Lead.workspace_id == manager.workspace_id
        metrics = DashboardMetrics(
            new_leads=self._count_leads(workspace_condition, Lead.lead_status == LeadStatus.NEW),
            unassigned_leads=self._count_leads(
                workspace_condition, Lead.assignee_user_id.is_(None)
            ),
            awaiting_qualification=self._count_leads(
                workspace_condition,
                Lead.qualification_status.in_(
                    [QualificationStatus.PENDING, QualificationStatus.NEEDS_REVIEW]
                ),
            ),
            reply_drafts_waiting_approval=self._db.scalar(
                select(func.count()).select_from(ReplyDraft).where(
                    ReplyDraft.workspace_id == manager.workspace_id,
                    ReplyDraft.status == ReplyDraftStatus.DRAFT,
                )
            )
            or 0,
        )
        attention_conditions = [
            workspace_condition,
            or_(
                Lead.assignee_user_id.is_(None),
                Lead.qualification_status == QualificationStatus.NEEDS_REVIEW,
                Lead.lead_status == LeadStatus.NEW,
            ),
        ]
        attention_rows = self._db.execute(
            self._summary_statement(attention_conditions).order_by(Lead.updated_at.desc()).limit(6)
        ).all()
        activity = self._db.scalars(
            select(AuditEvent)
            .where(AuditEvent.workspace_id == manager.workspace_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(8)
        )
        return DashboardRead(
            metrics=metrics,
            needs_attention=[self._to_summary(*row) for row in attention_rows],
            recent_activity=[AuditEventRead.model_validate(event) for event in activity],
        )

    def _get_authorised_lead(self, actor: User, lead_id: UUID) -> Lead:
        conditions = self._scope_conditions(actor)
        lead = self._db.scalar(select(Lead).where(Lead.id == lead_id, *conditions))
        if lead is None:
            raise LeadNotFoundError
        return lead

    def _scope_conditions(
        self,
        actor: User,
        *,
        lead_status: LeadStatus | None = None,
        qualification_status: QualificationStatus | None = None,
        assignment: AssignmentFilter = "all",
    ) -> list[object]:
        conditions: list[object] = [Lead.workspace_id == actor.workspace_id]
        if actor.role is UserRole.USER or assignment == "mine":
            conditions.append(Lead.assignee_user_id == actor.id)
        elif assignment == "unassigned":
            conditions.append(Lead.assignee_user_id.is_(None))
        if lead_status is not None:
            conditions.append(Lead.lead_status == lead_status)
        if qualification_status is not None:
            conditions.append(Lead.qualification_status == qualification_status)
        return conditions

    def _update_assignee(self, actor: User, lead: Lead, assignee_user_id: UUID | None) -> None:
        if actor.role is not UserRole.MANAGER:
            raise LeadPermissionError("Only Managers can assign a lead")
        if assignee_user_id is not None:
            assignee = self._db.scalar(
                select(User).where(
                    User.id == assignee_user_id,
                    User.workspace_id == actor.workspace_id,
                    User.is_active.is_(True),
                )
            )
            if assignee is None:
                raise LeadValidationError("Choose an active member of this workspace")
        previous_assignee = lead.assignee_user_id
        if previous_assignee != assignee_user_id:
            lead.assignee_user_id = assignee_user_id
            record_audit_event(
                self._db,
                workspace_id=lead.workspace_id,
                actor_user_id=actor.id,
                action="lead.assigned",
                entity_type="lead",
                entity_id=lead.id,
                metadata={
                    "previous_assignee_user_id": str(previous_assignee)
                    if previous_assignee
                    else None,
                    "assignee_user_id": str(assignee_user_id) if assignee_user_id else None,
                },
            )

    def _update_status(self, actor: User, lead: Lead, new_status: LeadStatus) -> None:
        previous_status = lead.lead_status
        if previous_status != new_status:
            lead.lead_status = new_status
            record_audit_event(
                self._db,
                workspace_id=lead.workspace_id,
                actor_user_id=actor.id,
                action="lead.status_changed",
                entity_type="lead",
                entity_id=lead.id,
                metadata={"previous_status": previous_status.value, "lead_status": new_status.value},
            )

    def _summary_statement(self, conditions: list[object]):
        assignee = aliased(User)
        return (
            select(Lead, Contact, Source, assignee)
            .outerjoin(Contact, Contact.id == Lead.contact_id)
            .join(IntakeEvent, IntakeEvent.id == Lead.intake_event_id)
            .join(Source, Source.id == IntakeEvent.source_id)
            .outerjoin(assignee, assignee.id == Lead.assignee_user_id)
            .where(*conditions)
        )

    def _count_leads(self, *conditions: object) -> int:
        return self._db.scalar(select(func.count()).select_from(Lead).where(*conditions)) or 0

    @staticmethod
    def _to_summary(
        lead: Lead, contact: Contact | None, source: Source, assignee: User | None
    ) -> LeadSummaryRead:
        return LeadSummaryRead(
            id=lead.id,
            contact=(
                LeadContactSummary(
                    id=contact.id,
                    full_name=contact.full_name,
                    email=contact.email,
                    phone_e164=contact.phone_e164,
                    company_name=contact.company_name,
                )
                if contact
                else None
            ),
            source=LeadSourceSummary(
                id=source.id, name=source.name, source_type=source.source_type
            ),
            assignee=(
                LeadAssigneeSummary(
                    id=assignee.id,
                    name=assignee.name,
                    email=assignee.email,
                    role=assignee.role,
                )
                if assignee
                else None
            ),
            enquiry_message=lead.enquiry_message,
            lead_status=lead.lead_status,
            qualification_status=lead.qualification_status,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )
