from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import CurrentAuthentication, get_auth_service
from app.core.config import get_settings
from app.schemas.auth import (
    AuthenticatedUserResponse,
    ChangePasswordRequest,
    EmailVerificationResponse,
    LoginRequest,
    MessageResponse,
    PasswordResetRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.services.auth import (
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidSecurityTokenError,
)
from app.services.email_delivery import EmailDeliveryService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
GENERIC_RESET_MESSAGE = "If an active account exists for that email, a reset link has been sent."


def _set_session_cookie(response: Response, raw_token: str) -> None:
    """Write the opaque session as an HTTP-only cookie; PostgreSQL receives only its hash."""
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_lifetime_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Remove the browser copy after the corresponding database session is revoked."""
    response.delete_cookie(key=get_settings().session_cookie_name, path="/")


@router.post(
    "/register", response_model=AuthenticatedUserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest, response: Response, service: AuthServiceDependency
) -> AuthenticatedUserResponse:
    """Create a workspace and its first Manager, then sign that manager in immediately."""
    try:
        user, workspace, created_session, verification_token = service.register(payload)
    except DuplicateEmailError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        ) from error
    EmailDeliveryService(get_settings()).send_email_verification(user.email, verification_token)
    _set_session_cookie(response, created_session.raw_token)
    return AuthenticatedUserResponse(user=user, workspace=workspace)


@router.post("/login", response_model=AuthenticatedUserResponse)
def login(
    payload: LoginRequest, response: Response, service: AuthServiceDependency
) -> AuthenticatedUserResponse:
    """Validate credentials and issue a new browser session without exposing a token in JSON."""
    try:
        user, workspace, created_session = service.login(
            email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from error
    _set_session_cookie(response, created_session.raw_token)
    return AuthenticatedUserResponse(user=user, workspace=workspace)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response, authentication: CurrentAuthentication, service: AuthServiceDependency
) -> MessageResponse:
    """Revoke the active browser session and remove its cookie from this browser."""
    service.logout(authentication.session)
    _clear_session_cookie(response)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=AuthenticatedUserResponse)
def me(authentication: CurrentAuthentication) -> AuthenticatedUserResponse:
    """Return the signed-in user and workspace for frontend startup and protected screens."""
    return AuthenticatedUserResponse(user=authentication.user, workspace=authentication.workspace)


@router.post(
    "/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED
)
def forgot_password(
    payload: PasswordResetRequest, service: AuthServiceDependency
) -> MessageResponse:
    """Request a reset link while returning the same message for known and unknown emails."""
    result = service.request_password_reset(payload.email)
    if result is not None:
        user, raw_token = result
        EmailDeliveryService(get_settings()).send_password_reset(user.email, raw_token)
    return MessageResponse(message=GENERIC_RESET_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest, service: AuthServiceDependency
) -> MessageResponse:
    """Use one reset link once, revoke old browser sessions, and require a fresh login."""
    try:
        service.reset_password(raw_token=payload.token, new_password=payload.new_password)
    except InvalidSecurityTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        ) from error
    return MessageResponse(message="Password reset successful. Please sign in.")


@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email(
    payload: VerifyEmailRequest, service: AuthServiceDependency
) -> EmailVerificationResponse:
    """Verify an email address using its one-use token from the verification link."""
    try:
        verified_at = service.verify_email(payload.token)
    except InvalidSecurityTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        ) from error
    return EmailVerificationResponse(email_verified_at=verified_at)


@router.post(
    "/resend-email-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def resend_email_verification(
    authentication: CurrentAuthentication, service: AuthServiceDependency
) -> MessageResponse:
    """Issue a replacement verification link without exposing a raw token in JSON."""
    raw_token = service.request_email_verification(authentication.user)
    if raw_token:
        EmailDeliveryService(get_settings()).send_email_verification(
            authentication.user.email, raw_token
        )
    return MessageResponse(message="If verification is still needed, a new link has been sent.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    authentication: CurrentAuthentication,
    service: AuthServiceDependency,
) -> MessageResponse:
    """Replace a known password, revoke every older session, and rotate this browser to a new session."""
    try:
        created_session = service.change_password(
            user=authentication.user,
            current_session=authentication.session,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        ) from error
    _set_session_cookie(response, created_session.raw_token)
    return MessageResponse(message="Password changed")
