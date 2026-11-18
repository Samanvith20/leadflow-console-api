import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.auth_token import AuthToken, AuthTokenPurpose
from app.models.session import Session as LoginSession
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceStatus
from app.schemas.auth import RegisterRequest
from app.services.audit import record_audit_event
from app.services.auth_tokens import create_auth_token, hash_auth_token
from app.services.passwords import hash_password, password_needs_rehash, verify_password
from app.services.session_tokens import create_session_token, hash_session_token


class AuthError(Exception):
    """Base exception for expected auth failures that routes convert into safe HTTP responses."""


class DuplicateEmailError(AuthError):
    """Raised when a registration email is already attached to an account."""


class InvalidCredentialsError(AuthError):
    """Raised without revealing whether an email address exists or a password was wrong."""


class InvalidSecurityTokenError(AuthError):
    """Raised for expired, used, cancelled, or unknown reset and verification tokens."""


class InactiveAccountError(AuthError):
    """Raised when an account or workspace cannot currently access Leadflow."""


@dataclass(frozen=True)
class AuthenticatedSession:
    """The authenticated records needed by protected routes without exposing a raw cookie token."""

    session: LoginSession
    user: User
    workspace: Workspace


@dataclass(frozen=True)
class SessionCreation:
    """A persisted session plus its raw value, which is returned once for an HTTP-only cookie."""

    session: LoginSession
    raw_token: str


class AuthService:
    """Own account registration, passwords, secure sessions, and one-time security tokens."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def register(self, request: RegisterRequest) -> tuple[User, Workspace, SessionCreation, str]:
        """Create the first Manager, its workspace, session, and verification token atomically."""
        if self._find_user_by_email(request.email):
            raise DuplicateEmailError

        workspace = Workspace(name=request.workspace_name, timezone=request.timezone)
        self._db.add(workspace)
        self._db.flush()

        user = User(
            workspace_id=workspace.id,
            name=request.name,
            email=request.email,
            password_hash=hash_password(request.password),
            role=UserRole.MANAGER,
        )
        self._db.add(user)
        self._db.flush()
        created_session = self._create_session(user.id)
        verification_token = self._create_security_token(
            user.id,
            AuthTokenPurpose.EMAIL_VERIFICATION,
            timedelta(hours=self._settings.email_verification_lifetime_hours),
        )
        record_audit_event(
            self._db,
            workspace_id=workspace.id,
            actor_user_id=user.id,
            action="auth.registered",
            entity_type="user",
            entity_id=user.id,
        )
        try:
            self._db.commit()
        except IntegrityError as error:
            self._db.rollback()
            raise DuplicateEmailError from error
        self._db.refresh(user)
        self._db.refresh(workspace)
        self._db.refresh(created_session.session)
        return user, workspace, created_session, verification_token

    def login(self, *, email: str, password: str) -> tuple[User, Workspace, SessionCreation]:
        """Authenticate an active account and issue a fresh opaque browser session."""
        user = self._find_user_by_email(email)
        if user is None or not verify_password(user.password_hash, password):
            raise InvalidCredentialsError
        workspace = self._get_workspace(user.workspace_id)
        self._ensure_account_is_active(user, workspace)
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        created_session = self._create_session(user.id)
        self._db.commit()
        self._db.refresh(created_session.session)
        return user, workspace, created_session

    def logout(self, login_session: LoginSession) -> None:
        """Revoke only the browser session presented with the logout request."""
        if login_session.revoked_at is None:
            login_session.revoked_at = self._now()
            self._db.commit()

    def request_password_reset(self, email: str) -> tuple[User, str] | None:
        """Create a reset token for an active account, without exposing account existence to callers."""
        user = self._find_user_by_email(email)
        if user is None:
            return None
        workspace = self._get_workspace(user.workspace_id)
        if not user.is_active or workspace.status is not WorkspaceStatus.ACTIVE:
            return None
        raw_token = self._create_security_token(
            user.id,
            AuthTokenPurpose.PASSWORD_RESET,
            timedelta(minutes=self._settings.password_reset_lifetime_minutes),
        )
        self._db.commit()
        return user, raw_token

    def reset_password(self, *, raw_token: str, new_password: str) -> None:
        """Use one valid reset token once, change the password, and revoke every old login session."""
        token = self._get_valid_security_token(raw_token, AuthTokenPurpose.PASSWORD_RESET)
        user = self._db.get(User, token.user_id)
        if user is None:
            raise InvalidSecurityTokenError
        user.password_hash = hash_password(new_password)
        token.consumed_at = self._now()
        self._invalidate_other_security_tokens(user.id, AuthTokenPurpose.PASSWORD_RESET)
        self._revoke_all_sessions(user.id)
        record_audit_event(
            self._db,
            workspace_id=user.workspace_id,
            actor_user_id=user.id,
            action="auth.password_reset",
            entity_type="user",
            entity_id=user.id,
        )
        self._db.commit()

    def verify_email(self, raw_token: str) -> datetime:
        """Consume one email-verification token and persist the verified timestamp for its user."""
        token = self._get_valid_security_token(raw_token, AuthTokenPurpose.EMAIL_VERIFICATION)
        user = self._db.get(User, token.user_id)
        if user is None:
            raise InvalidSecurityTokenError
        verified_at = self._now()
        user.email_verified_at = verified_at
        token.consumed_at = verified_at
        self._invalidate_other_security_tokens(user.id, AuthTokenPurpose.EMAIL_VERIFICATION)
        record_audit_event(
            self._db,
            workspace_id=user.workspace_id,
            actor_user_id=user.id,
            action="auth.email_verified",
            entity_type="user",
            entity_id=user.id,
        )
        self._db.commit()
        return verified_at

    def request_email_verification(self, user: User) -> str | None:
        """Replace any old verification link for an unverified signed-in user."""
        if user.email_verified_at is not None:
            return None
        raw_token = self._create_security_token(
            user.id,
            AuthTokenPurpose.EMAIL_VERIFICATION,
            timedelta(hours=self._settings.email_verification_lifetime_hours),
        )
        self._db.commit()
        return raw_token

    def change_password(
        self, *, user: User, current_session: LoginSession, current_password: str, new_password: str
    ) -> SessionCreation:
        """Require the current password, revoke every old session, and rotate to one fresh session."""
        if not verify_password(user.password_hash, current_password):
            raise InvalidCredentialsError
        user.password_hash = hash_password(new_password)
        self._revoke_all_sessions(user.id)
        created_session = self._create_session(user.id)
        record_audit_event(
            self._db,
            workspace_id=user.workspace_id,
            actor_user_id=user.id,
            action="auth.password_changed",
            entity_type="user",
            entity_id=user.id,
            metadata={"previous_session_id": str(current_session.id)},
        )
        self._db.commit()
        self._db.refresh(created_session.session)
        return created_session

    def get_authenticated_session(self, raw_session_token: str) -> AuthenticatedSession:
        """Load an active session and its active user/workspace, updating only its last-seen timestamp."""
        now = self._now()
        session = self._db.scalar(
            self._active_session_statement(hash_session_token(raw_session_token), now)
        )
        if session is None:
            raise InvalidCredentialsError
        user = self._db.get(User, session.user_id)
        if user is None:
            raise InvalidCredentialsError
        workspace = self._get_workspace(user.workspace_id)
        self._ensure_account_is_active(user, workspace)
        session.last_seen_at = now
        self._db.commit()
        return AuthenticatedSession(session=session, user=user, workspace=workspace)

    def _find_user_by_email(self, email: str) -> User | None:
        """Find one normalized email address; schemas normalize public request values first."""
        return self._db.scalar(select(User).where(User.email == email))

    def _get_workspace(self, workspace_id: uuid.UUID) -> Workspace:
        workspace = self._db.get(Workspace, workspace_id)
        if workspace is None:
            raise InactiveAccountError
        return workspace

    def _ensure_account_is_active(self, user: User, workspace: Workspace) -> None:
        if not user.is_active or workspace.status is not WorkspaceStatus.ACTIVE:
            raise InactiveAccountError

    def _create_session(self, user_id: uuid.UUID) -> SessionCreation:
        raw_token = create_session_token()
        login_session = LoginSession(
            user_id=user_id,
            token_hash=hash_session_token(raw_token),
            expires_at=self._now() + timedelta(days=self._settings.session_lifetime_days),
        )
        self._db.add(login_session)
        self._db.flush()
        return SessionCreation(session=login_session, raw_token=raw_token)

    def _create_security_token(
        self, user_id: uuid.UUID, purpose: AuthTokenPurpose, lifetime: timedelta
    ) -> str:
        self._invalidate_other_security_tokens(user_id, purpose)
        raw_token = create_auth_token()
        self._db.add(
            AuthToken(
                user_id=user_id,
                purpose=purpose,
                token_hash=hash_auth_token(raw_token),
                expires_at=self._now() + lifetime,
            )
        )
        return raw_token

    def _get_valid_security_token(self, raw_token: str, purpose: AuthTokenPurpose) -> AuthToken:
        """Lock a valid token row so two simultaneous requests cannot both consume it."""
        token = self._db.scalar(
            select(AuthToken)
            .where(
                AuthToken.token_hash == hash_auth_token(raw_token),
                AuthToken.purpose == purpose,
                AuthToken.expires_at > self._now(),
                AuthToken.consumed_at.is_(None),
                AuthToken.invalidated_at.is_(None),
            )
            .with_for_update()
        )
        if token is None:
            raise InvalidSecurityTokenError
        return token

    def _invalidate_other_security_tokens(self, user_id: uuid.UUID, purpose: AuthTokenPurpose) -> None:
        self._db.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == purpose,
                AuthToken.consumed_at.is_(None),
                AuthToken.invalidated_at.is_(None),
            )
            .values(invalidated_at=self._now())
        )

    def _revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        self._db.execute(
            update(LoginSession)
            .where(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None))
            .values(revoked_at=self._now())
        )

    @staticmethod
    def _active_session_statement(token_hash: str, now: datetime) -> Select[tuple[LoginSession]]:
        return select(LoginSession).where(
            LoginSession.token_hash == token_hash,
            LoginSession.revoked_at.is_(None),
            LoginSession.expires_at > now,
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
