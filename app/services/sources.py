from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.source import Source, SourceType
from app.models.user import User, UserRole
from app.schemas.source import SourceCreate, SourceCreated, SourceRead, SourceUpdate
from app.services.encryption import EncryptionService
from app.services.source_identifiers import create_source_public_id, create_webhook_secret


class SourceNotFoundError(Exception):
    """Raised when a source is absent or belongs to a different workspace."""


class SourceService:
    """Manage workspace sources while keeping their raw HMAC secrets server-only."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def create(self, user: User, payload: SourceCreate) -> SourceCreated:
        """Create a source and return its raw secret once; only ciphertext remains afterward."""
        self._require_manager(user)
        uses_webhook = payload.source_type not in {SourceType.CSV_IMPORT, SourceType.MANUAL_ENTRY}
        raw_secret = create_webhook_secret() if uses_webhook else None
        ciphertext = EncryptionService(self._settings.webhook_encryption_key).encrypt(raw_secret) if raw_secret else None
        source = Source(workspace_id=user.workspace_id, name=payload.name, source_type=payload.source_type, public_id=create_source_public_id(), webhook_secret_ciphertext=ciphertext, configuration=payload.configuration.model_dump(mode="json"))
        self._db.add(source)
        self._db.commit()
        self._db.refresh(source)
        public = SourceRead.model_validate(source).model_dump()
        return SourceCreated(**public, webhook_url=f"/api/v1/webhooks/{source.public_id}", webhook_secret=raw_secret)

    def list(self, user: User) -> list[SourceRead]:
        """List only sources owned by the authenticated Manager's workspace."""
        self._require_manager(user)
        records = self._db.scalars(select(Source).where(Source.workspace_id == user.workspace_id).order_by(Source.created_at.desc()))
        return [SourceRead.model_validate(source) for source in records]

    def update(self, user: User, source_id: UUID, payload: SourceUpdate) -> SourceRead:
        """Update safe source settings; secret rotation will be a distinct deliberate action later."""
        self._require_manager(user)
        source = self._db.scalar(select(Source).where(Source.id == source_id, Source.workspace_id == user.workspace_id))
        if source is None:
            raise SourceNotFoundError
        if payload.name is not None: source.name = payload.name
        if payload.status is not None: source.status = payload.status
        if payload.configuration is not None: source.configuration = payload.configuration.model_dump(mode="json")
        self._db.commit(); self._db.refresh(source)
        return SourceRead.model_validate(source)

    def rotate_secret(self, user: User, source_id: UUID) -> str:
        """Replace a potentially exposed secret and reveal its replacement exactly once."""
        self._require_manager(user)
        source = self._db.scalar(select(Source).where(Source.id == source_id, Source.workspace_id == user.workspace_id))
        if source is None: raise SourceNotFoundError
        raw_secret = create_webhook_secret()
        source.webhook_secret_ciphertext = EncryptionService(self._settings.webhook_encryption_key).encrypt(raw_secret)
        self._db.commit()
        return raw_secret

    @staticmethod
    def _require_manager(user: User) -> None:
        if user.role is not UserRole.MANAGER:
            raise PermissionError("Only workspace Managers can manage sources")
