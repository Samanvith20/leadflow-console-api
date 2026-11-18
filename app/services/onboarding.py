from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source, SourceStatus
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.schemas.onboarding import (
    OnboardingCompleteResponse,
    OnboardingRead,
    OnboardingUpdate,
    QualificationConfiguration,
)
from app.schemas.workspace import AiGuidanceConfiguration, OrganizationConfiguration
from app.services.audit import record_audit_event


class OnboardingIncompleteError(Exception):
    """Raised when a workspace tries to finish setup without its minimum business guidance."""


class OnboardingService:
    """Persist resumable workspace setup data without relying on one browser's local storage."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def read(self, user: User, workspace: Workspace) -> OnboardingRead:
        """Return the current server-saved setup state for the authenticated Manager."""
        self._require_manager(user)
        return self._serialize(workspace)

    def update(self, user: User, workspace: Workspace, payload: OnboardingUpdate) -> OnboardingRead:
        """Merge a wizard step into workspace configuration and record the resume location."""
        self._require_manager(user)
        configuration = dict(workspace.configuration)
        for section in ("organization", "qualification", "ai_guidance"):
            value = getattr(payload, section)
            if value is not None:
                configuration[section] = value.model_dump(mode="json")
        onboarding = dict(configuration.get("onboarding", {}))
        if payload.current_step is not None:
            onboarding["current_step"] = payload.current_step
        onboarding["last_saved_at"] = datetime.now(UTC).isoformat()
        configuration["onboarding"] = onboarding
        workspace.configuration = configuration
        self._db.commit()
        self._db.refresh(workspace)
        return self._serialize(workspace)

    def complete(self, user: User, workspace: Workspace) -> OnboardingCompleteResponse:
        """Mark setup complete after confirming enough business context exists for qualification."""
        self._require_manager(user)
        state = self._serialize(workspace)
        if (
            not state.organization.industry
            or not state.organization.business_description
            or not state.organization.services
            or not state.organization.service_areas
        ):
            raise OnboardingIncompleteError(
                "Add your industry, business description, at least one service, and a service area"
            )
        if not state.qualification.ideal_lead_description:
            raise OnboardingIncompleteError("Describe your ideal lead before completing setup")
        if not state.ai_guidance.brand_tone or not state.ai_guidance.reply_goal:
            raise OnboardingIncompleteError("Choose a reply tone and goal before completing setup")
        if not self._db.scalar(select(Source.id).where(Source.workspace_id == workspace.id, Source.status == SourceStatus.ACTIVE)):
            raise OnboardingIncompleteError("Add at least one active source before completing setup")
        completed_at = datetime.now(UTC)
        workspace.onboarding_completed_at = completed_at
        configuration = dict(workspace.configuration)
        configuration["onboarding"] = {**dict(configuration.get("onboarding", {})), "current_step": "connect_source"}
        workspace.configuration = configuration
        record_audit_event(self._db, workspace_id=workspace.id, actor_user_id=user.id, action="onboarding.completed", entity_type="workspace", entity_id=workspace.id)
        self._db.commit()
        return OnboardingCompleteResponse(completed_at=completed_at)

    @staticmethod
    def _require_manager(user: User) -> None:
        if user.role is not UserRole.MANAGER:
            raise PermissionError("Only workspace Managers can edit onboarding")

    @staticmethod
    def _serialize(workspace: Workspace) -> OnboardingRead:
        configuration = workspace.configuration or {}
        onboarding = configuration.get("onboarding", {})
        step = onboarding.get("current_step", "business_profile")
        return OnboardingRead(
            current_step=step if step in {"business_profile", "qualification", "ai_guidance", "connect_source"} else "business_profile",
            completed_at=workspace.onboarding_completed_at,
            organization=OrganizationConfiguration.model_validate(configuration.get("organization", {})),
            qualification=QualificationConfiguration.model_validate(configuration.get("qualification", {})),
            ai_guidance=AiGuidanceConfiguration.model_validate(configuration.get("ai_guidance", {})),
        )
