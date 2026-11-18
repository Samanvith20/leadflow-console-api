from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.core.config import get_settings
from app.schemas.source import SourceCreate, SourceCreated, SourceRead, SourceUpdate
from app.services.encryption import EncryptionConfigurationError
from app.services.sources import SourceNotFoundError, SourceService

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


def service(db: DatabaseSession) -> SourceService:
    """Build a request-scoped source service using the configured encryption key."""
    return SourceService(db, get_settings())


SourceServiceDependency = Annotated[SourceService, Depends(service)]


@router.post("", response_model=SourceCreated, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, authentication: CurrentAuthentication, source_service: SourceServiceDependency) -> SourceCreated:
    """Create a source and reveal its secret only in this creation response."""
    try: return source_service.create(authentication.user, payload)
    except PermissionError as error: raise HTTPException(403, str(error)) from error
    except EncryptionConfigurationError as error: raise HTTPException(503, str(error)) from error


@router.get("", response_model=list[SourceRead])
def list_sources(authentication: CurrentAuthentication, source_service: SourceServiceDependency) -> list[SourceRead]:
    """Return safe source metadata without any webhook secret."""
    try: return source_service.list(authentication.user)
    except PermissionError as error: raise HTTPException(403, str(error)) from error


@router.patch("/{source_id}", response_model=SourceRead)
def update_source(source_id: str, payload: SourceUpdate, authentication: CurrentAuthentication, source_service: SourceServiceDependency) -> SourceRead:
    """Update one workspace-owned source."""
    from uuid import UUID
    try: return source_service.update(authentication.user, UUID(source_id), payload)
    except ValueError as error: raise HTTPException(422, "Invalid source ID") from error
    except SourceNotFoundError as error: raise HTTPException(404, "Source not found") from error
    except PermissionError as error: raise HTTPException(403, str(error)) from error


@router.post("/{source_id}/rotate-secret", response_model=dict)
def rotate_secret(source_id: str, authentication: CurrentAuthentication, source_service: SourceServiceDependency) -> dict:
    """Generate a replacement source secret; show it once and invalidate the previous secret."""
    from uuid import UUID
    try: return {"webhook_secret": source_service.rotate_secret(authentication.user, UUID(source_id))}
    except ValueError as error: raise HTTPException(422, "Invalid source ID") from error
    except SourceNotFoundError as error: raise HTTPException(404, "Source not found") from error
    except PermissionError as error: raise HTTPException(403, str(error)) from error
