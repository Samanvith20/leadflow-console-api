from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.schemas.workspace import (
    AiGuidanceConfiguration,
    OrganizationConfiguration,
    QualificationConfiguration,
    WorkspaceProfileRead,
    WorkspaceProfileUpdate,
)
from app.services.audit import record_audit_event


class WorkspaceProfileService:
    """Read and update the business profile that guides Leadflow's lead operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def read(self, user: User, workspace: Workspace) -> WorkspaceProfileRead:
        """Return the authenticated Manager's workspace business profile."""
        self._require_manager(user)
        return self._serialize(workspace)

    def update(
        self, user: User, workspace: Workspace, payload: WorkspaceProfileUpdate
    ) -> WorkspaceProfileRead:
        """Persist a manager-approved profile change and record it in the audit timeline."""
        self._require_manager(user)
        if payload.name is not None:
            workspace.name = payload.name
        if payload.timezone is not None:
            workspace.timezone = payload.timezone
        if payload.organization is not None:
            configuration = dict(workspace.configuration)
            configuration["organization"] = payload.organization.model_dump(mode="json")
            workspace.configuration = configuration
        if payload.qualification is not None:
            configuration = dict(workspace.configuration)
            configuration["qualification"] = payload.qualification.model_dump(mode="json")
            workspace.configuration = configuration
        if payload.ai_guidance is not None:
            configuration = dict(workspace.configuration)
            configuration["ai_guidance"] = payload.ai_guidance.model_dump(mode="json")
            workspace.configuration = configuration

        record_audit_event(
            self._db,
            workspace_id=workspace.id,
            actor_user_id=user.id,
            action="workspace.profile_updated",
            entity_type="workspace",
            entity_id=workspace.id,
        )
        self._db.commit()
        self._db.refresh(workspace)
        return self._serialize(workspace)

    @staticmethod
    def _require_manager(user: User) -> None:
        if user.role is not UserRole.MANAGER:
            raise PermissionError("Only workspace Managers can edit the business profile")

    @staticmethod
    def _serialize(workspace: Workspace) -> WorkspaceProfileRead:
        configuration = workspace.configuration or {}
        return WorkspaceProfileRead(
            id=workspace.id,
            name=workspace.name,
            timezone=workspace.timezone,
            organization=OrganizationConfiguration.model_validate(
                configuration.get("organization", {})
            ),
            qualification=QualificationConfiguration.model_validate(
                configuration.get("qualification", {})
            ),
            ai_guidance=AiGuidanceConfiguration.model_validate(
                configuration.get("ai_guidance", {})
            ),
        )
