"""Manager overview endpoint backed by real leads, reply drafts, and audit events."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.schemas.dashboard import DashboardRead
from app.services.leads import DashboardPermissionError, LeadService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def service(db: DatabaseSession) -> LeadService:
    """Use the same workspace-scoped read service as the Leads API."""
    return LeadService(db)


LeadServiceDependency = Annotated[LeadService, Depends(service)]


@router.get("", response_model=DashboardRead)
def get_dashboard(
    authentication: CurrentAuthentication, lead_service: LeadServiceDependency
) -> DashboardRead:
    """Return real operational information only to the workspace Manager."""
    try:
        return lead_service.dashboard(authentication.user)
    except DashboardPermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
