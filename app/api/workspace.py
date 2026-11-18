from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.schemas.workspace import WorkspaceProfileRead, WorkspaceProfileUpdate
from app.services.workspace_profile import WorkspaceProfileService

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])


def get_workspace_profile_service(db: DatabaseSession) -> WorkspaceProfileService:
    """Create the request-scoped service for manager-controlled workspace profile changes."""
    return WorkspaceProfileService(db)


WorkspaceProfileServiceDependency = Annotated[
    WorkspaceProfileService, Depends(get_workspace_profile_service)
]


@router.get("/profile", response_model=WorkspaceProfileRead)
def get_workspace_profile(
    authentication: CurrentAuthentication,
    service: WorkspaceProfileServiceDependency,
) -> WorkspaceProfileRead:
    """Return the currently saved business profile for Settings."""
    try:
        return service.read(authentication.user, authentication.workspace)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.patch("/profile", response_model=WorkspaceProfileRead)
def update_workspace_profile(
    payload: WorkspaceProfileUpdate,
    authentication: CurrentAuthentication,
    service: WorkspaceProfileServiceDependency,
) -> WorkspaceProfileRead:
    """Update the business profile without requiring the manager to redo onboarding."""
    try:
        return service.update(authentication.user, authentication.workspace, payload)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
