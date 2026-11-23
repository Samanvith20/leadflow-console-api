from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.auth import (
    AuthenticatedSession,
    AuthService,
    InactiveAccountError,
    InvalidCredentialsError,
)

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_auth_service(db: DatabaseSession) -> AuthService:
    """Create an auth service bound to the database transaction for the current request."""
    return AuthService(db, get_settings())


def get_current_authentication(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedSession:
    """Require a valid, non-revoked browser session for protected API routes."""
    session_token = request.cookies.get(get_settings().session_cookie_name)
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return service.get_authenticated_session(session_token)
    except InactiveAccountError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is unavailable"
        ) from error
    except InvalidCredentialsError as error:
        # Never reveal whether a cookie value maps to a real session.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        ) from error


CurrentAuthentication = Annotated[AuthenticatedSession, Depends(get_current_authentication)]
