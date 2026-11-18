from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.schemas.onboarding import OnboardingCompleteResponse, OnboardingRead, OnboardingUpdate
from app.services.onboarding import OnboardingIncompleteError, OnboardingService

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingRead)
def get_onboarding(authentication: CurrentAuthentication, db: DatabaseSession) -> OnboardingRead:
    """Read server-saved setup progress so a Manager can resume from any device."""
    try:
        return OnboardingService(db).read(authentication.user, authentication.workspace)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.patch("", response_model=OnboardingRead)
def update_onboarding(
    payload: OnboardingUpdate, authentication: CurrentAuthentication, db: DatabaseSession
) -> OnboardingRead:
    """Autosave one onboarding step and its resume position."""
    try:
        return OnboardingService(db).update(authentication.user, authentication.workspace, payload)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.post("/complete", response_model=OnboardingCompleteResponse)
def complete_onboarding(
    authentication: CurrentAuthentication, db: DatabaseSession
) -> OnboardingCompleteResponse:
    """Finish setup after the minimum business profile and qualification guidance are present."""
    try:
        return OnboardingService(db).complete(authentication.user, authentication.workspace)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except OnboardingIncompleteError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
