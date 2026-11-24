"""Authenticated lead list, detail, assignment, and status endpoints."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.schemas.lead import (
    LeadDetailRead,
    LeadListResponse,
    LeadUpdate,
)
from app.services.leads import (
    LeadNotFoundError,
    LeadPermissionError,
    LeadService,
    LeadValidationError,
)

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


def service(db: DatabaseSession) -> LeadService:
    """Build a request-scoped service that always applies workspace and role scope."""
    return LeadService(db)


LeadServiceDependency = Annotated[LeadService, Depends(service)]
AssignmentFilter = Literal["all", "mine", "unassigned"]


def _lead_error(error: Exception) -> HTTPException:
    if isinstance(error, LeadNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if isinstance(error, LeadPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


@router.get("", response_model=LeadListResponse)
def list_leads(
    authentication: CurrentAuthentication,
    lead_service: LeadServiceDependency,
    lead_status: str | None = None,
    qualification_status: str | None = None,
    assignment: AssignmentFilter = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeadListResponse:
    """List leads; standard Users are always scoped to their own assignments."""
    from app.models.lead import LeadStatus, QualificationStatus

    try:
        parsed_lead_status = LeadStatus(lead_status) if lead_status else None
        parsed_qualification = QualificationStatus(qualification_status) if qualification_status else None
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid lead or qualification status filter",
        ) from error
    return lead_service.list_leads(
        authentication.user,
        lead_status=parsed_lead_status,
        qualification_status=parsed_qualification,
        assignment=assignment,
        limit=limit,
        offset=offset,
    )


@router.get("/{lead_id}", response_model=LeadDetailRead)
def get_lead(
    lead_id: UUID, authentication: CurrentAuthentication, lead_service: LeadServiceDependency
) -> LeadDetailRead:
    """Return one lead only if it belongs to the caller's permitted workspace scope."""
    try:
        return lead_service.get(authentication.user, lead_id)
    except LeadNotFoundError as error:
        raise _lead_error(error) from error


@router.patch("/{lead_id}", response_model=LeadDetailRead)
def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    authentication: CurrentAuthentication,
    lead_service: LeadServiceDependency,
) -> LeadDetailRead:
    """Allow Managers to assign and all authorised owners to move a lead through its status."""
    try:
        return lead_service.update(authentication.user, lead_id, payload)
    except (LeadNotFoundError, LeadPermissionError, LeadValidationError) as error:
        raise _lead_error(error) from error
