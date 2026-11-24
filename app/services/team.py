"""Manager-controlled workspace membership and one-use invitation handling."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.auth_token import AuthToken, AuthTokenPurpose
from app.models.session import Session as LoginSession
from app.models.user import User, UserRole
from app.schemas.team import (
    AcceptTeamInvitationRequest,
    InviteTeamMemberRequest,
    TeamMemberRead,
    TeamMemberUpdate,
)
from app.services.audit import record_audit_event
from app.services.auth_tokens import create_auth_token, hash_auth_token
from app.services.passwords import hash_password


class TeamPermissionError(Exception):
    """Raised when a non-Manager attempts to manage workspace membership."""


class TeamMemberNotFoundError(Exception):
    """Raised when a member is missing or belongs to another workspace."""


class TeamConflictError(Exception):
    """Raised when a membership action would create an invalid lifecycle state."""


class InvalidInvitationError(Exception):
    """Raised for expired, consumed, cancelled, or unknown invitation tokens."""


@dataclass(frozen=True)
class TeamInvitation:
    """A new or reissued member record with its raw token for immediate email delivery."""

    member: TeamMemberRead
    raw_token: str


class TeamService:
    """Manage standard Users while preserving lead history and security-token lifecycle."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def list_members(self, manager: User) -> list[TeamMemberRead]:
        """Return every member in the Manager's workspace, including the Manager."""
        self._require_manager(manager)
        members = self._db.scalars(
            select(User).where(User.workspace_id == manager.workspace_id).order_by(User.created_at)
        )
        return [self._to_read(member) for member in members]

    def invite(self, manager: User, payload: InviteTeamMemberRequest) -> TeamInvitation:
        """Create an inactive User and one-use invitation token, or revive a cancelled invite."""
        self._require_manager(manager)
        existing = self._db.scalar(select(User).where(User.email == payload.email))
        now = self._now()

        if existing is not None:
            if existing.workspace_id != manager.workspace_id:
                raise TeamConflictError("That email already belongs to another Leadflow workspace")
            if existing.is_active or existing.invitation_accepted_at is not None:
                raise TeamConflictError("That person is already an active workspace member")
            if existing.deactivated_at is None:
                raise TeamConflictError("An invitation is already pending for that email")
            # A Manager may invite again after cancelling an unaccepted invitation.
            existing.name = payload.name
            existing.is_available = payload.is_available
            existing.max_open_leads = payload.max_open_leads
            existing.deactivated_at = None
            existing.invited_at = now
            raw_token = self._create_invitation_token(existing.id)
            record_audit_event(
                self._db,
                workspace_id=manager.workspace_id,
                actor_user_id=manager.id,
                action="team.invitation_reissued",
                entity_type="user",
                entity_id=existing.id,
            )
            self._db.commit()
            self._db.refresh(existing)
            return TeamInvitation(member=self._to_read(existing), raw_token=raw_token)

        member = User(
            workspace_id=manager.workspace_id,
            name=payload.name,
            email=payload.email,
            # The invite recipient cannot use this random password. They choose one only
            # after proving possession of the invitation link.
            password_hash=hash_password(create_auth_token()),
            role=UserRole.USER,
            is_active=False,
            is_available=payload.is_available,
            max_open_leads=payload.max_open_leads,
            invited_at=now,
        )
        self._db.add(member)
        self._db.flush()
        raw_token = self._create_invitation_token(member.id)
        record_audit_event(
            self._db,
            workspace_id=manager.workspace_id,
            actor_user_id=manager.id,
            action="team.member_invited",
            entity_type="user",
            entity_id=member.id,
        )
        try:
            self._db.commit()
        except IntegrityError as error:
            self._db.rollback()
            raise TeamConflictError("That email is already in use") from error
        self._db.refresh(member)
        return TeamInvitation(member=self._to_read(member), raw_token=raw_token)

    def resend_invitation(self, manager: User, member_id: UUID) -> TeamInvitation:
        """Invalidate a pending invitation and issue a fresh one for the same member."""
        self._require_manager(manager)
        member = self._get_member(manager, member_id)
        if member.is_active or member.invitation_accepted_at is not None or member.deactivated_at:
            raise TeamConflictError("Only an invited team member can receive another invitation")
        member.invited_at = self._now()
        raw_token = self._create_invitation_token(member.id)
        record_audit_event(
            self._db,
            workspace_id=manager.workspace_id,
            actor_user_id=manager.id,
            action="team.invitation_resent",
            entity_type="user",
            entity_id=member.id,
        )
        self._db.commit()
        self._db.refresh(member)
        return TeamInvitation(member=self._to_read(member), raw_token=raw_token)

    def accept_invitation(self, payload: AcceptTeamInvitationRequest) -> TeamMemberRead:
        """Activate an invited User once, set their chosen password, and verify their email."""
        token = self._get_valid_invitation(payload.token)
        member = self._db.get(User, token.user_id)
        if (
            member is None
            or member.is_active
            or member.deactivated_at is not None
            or member.invitation_accepted_at is not None
        ):
            raise InvalidInvitationError
        now = self._now()
        member.password_hash = hash_password(payload.password)
        member.is_active = True
        member.email_verified_at = now
        member.invitation_accepted_at = now
        token.consumed_at = now
        self._invalidate_other_invitations(member.id)
        record_audit_event(
            self._db,
            workspace_id=member.workspace_id,
            actor_user_id=member.id,
            action="team.invitation_accepted",
            entity_type="user",
            entity_id=member.id,
        )
        self._db.commit()
        self._db.refresh(member)
        return self._to_read(member)

    def update_member(
        self, manager: User, member_id: UUID, payload: TeamMemberUpdate
    ) -> TeamMemberRead:
        """Change a standard member's display name, availability, or lead capacity."""
        self._require_manager(manager)
        member = self._get_standard_member(manager, member_id)
        if payload.name is not None:
            member.name = payload.name
        if payload.is_available is not None:
            member.is_available = payload.is_available
        if payload.max_open_leads is not None:
            member.max_open_leads = payload.max_open_leads
        record_audit_event(
            self._db,
            workspace_id=manager.workspace_id,
            actor_user_id=manager.id,
            action="team.member_updated",
            entity_type="user",
            entity_id=member.id,
        )
        self._db.commit()
        self._db.refresh(member)
        return self._to_read(member)

    def deactivate_member(self, manager: User, member_id: UUID) -> TeamMemberRead:
        """Disable a standard member without deleting their lead ownership or audit history."""
        self._require_manager(manager)
        member = self._get_standard_member(manager, member_id)
        if member.deactivated_at is not None:
            return self._to_read(member)
        now = self._now()
        member.is_active = False
        member.is_available = False
        member.deactivated_at = now
        self._invalidate_other_invitations(member.id)
        self._revoke_all_sessions(member.id)
        record_audit_event(
            self._db,
            workspace_id=manager.workspace_id,
            actor_user_id=manager.id,
            action="team.member_deactivated",
            entity_type="user",
            entity_id=member.id,
        )
        self._db.commit()
        self._db.refresh(member)
        return self._to_read(member)

    def reactivate_member(self, manager: User, member_id: UUID) -> TeamMemberRead:
        """Restore a previously accepted member's access without changing their password."""
        self._require_manager(manager)
        member = self._get_standard_member(manager, member_id)
        if member.deactivated_at is None:
            raise TeamConflictError("This member is not deactivated")
        if member.invitation_accepted_at is None:
            raise TeamConflictError("Send this person a new invitation instead")
        member.is_active = True
        member.deactivated_at = None
        record_audit_event(
            self._db,
            workspace_id=manager.workspace_id,
            actor_user_id=manager.id,
            action="team.member_reactivated",
            entity_type="user",
            entity_id=member.id,
        )
        self._db.commit()
        self._db.refresh(member)
        return self._to_read(member)

    def _create_invitation_token(self, user_id: UUID) -> str:
        self._invalidate_other_invitations(user_id)
        raw_token = create_auth_token()
        self._db.add(
            AuthToken(
                user_id=user_id,
                purpose=AuthTokenPurpose.TEAM_INVITATION,
                token_hash=hash_auth_token(raw_token),
                expires_at=self._now()
                + timedelta(minutes=self._settings.team_invitation_lifetime_minutes),
            )
        )
        return raw_token

    def _get_valid_invitation(self, raw_token: str) -> AuthToken:
        token = self._db.scalar(
            select(AuthToken)
            .where(
                AuthToken.token_hash == hash_auth_token(raw_token),
                AuthToken.purpose == AuthTokenPurpose.TEAM_INVITATION,
                AuthToken.expires_at > self._now(),
                AuthToken.consumed_at.is_(None),
                AuthToken.invalidated_at.is_(None),
            )
            .with_for_update()
        )
        if token is None:
            raise InvalidInvitationError
        return token

    def _invalidate_other_invitations(self, user_id: UUID) -> None:
        self._db.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == AuthTokenPurpose.TEAM_INVITATION,
                AuthToken.consumed_at.is_(None),
                AuthToken.invalidated_at.is_(None),
            )
            .values(invalidated_at=self._now())
        )

    def _revoke_all_sessions(self, user_id: UUID) -> None:
        self._db.execute(
            update(LoginSession)
            .where(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None))
            .values(revoked_at=self._now())
        )

    @staticmethod
    def _require_manager(user: User) -> None:
        if user.role is not UserRole.MANAGER:
            raise TeamPermissionError("Only workspace Managers can manage the team")

    @staticmethod
    def _to_read(member: User) -> TeamMemberRead:
        status = (
            "deactivated"
            if member.deactivated_at is not None
            else "invited"
            if not member.is_active
            else "active"
        )
        return TeamMemberRead(
            id=member.id,
            workspace_id=member.workspace_id,
            name=member.name,
            email=member.email,
            role=member.role,
            status=status,
            is_available=member.is_available,
            max_open_leads=member.max_open_leads,
            invited_at=member.invited_at,
            invitation_accepted_at=member.invitation_accepted_at,
            deactivated_at=member.deactivated_at,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    def _get_member(self, manager: User, member_id: UUID) -> User:
        member = self._db.scalar(
            select(User).where(User.id == member_id, User.workspace_id == manager.workspace_id)
        )
        if member is None:
            raise TeamMemberNotFoundError
        return member

    def _get_standard_member(self, manager: User, member_id: UUID) -> User:
        member = self._get_member(manager, member_id)
        if member.role is UserRole.MANAGER:
            raise TeamConflictError("Managers cannot be changed from the Team page")
        return member

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
