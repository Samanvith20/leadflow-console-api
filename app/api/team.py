"""Manager-only workspace membership endpoints plus public invitation acceptance."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentAuthentication, DatabaseSession
from app.core.config import get_settings
from app.schemas.auth import MessageResponse
from app.schemas.team import (
    AcceptTeamInvitationRequest,
    InviteTeamMemberRequest,
    TeamMemberRead,
    TeamMemberUpdate,
)
from app.services.email_delivery import EmailDeliveryService
from app.services.team import (
    InvalidInvitationError,
    TeamConflictError,
    TeamMemberNotFoundError,
    TeamPermissionError,
    TeamService,
)

router = APIRouter(prefix="/api/v1/team", tags=["team"])


def service(db: DatabaseSession) -> TeamService:
    """Build a request-scoped Team service with the current token lifetime settings."""
    return TeamService(db, get_settings())


TeamServiceDependency = Annotated[TeamService, Depends(service)]


def _team_error(error: Exception) -> HTTPException:
    if isinstance(error, TeamPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, TeamMemberNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("/members", response_model=list[TeamMemberRead])
def list_members(
    authentication: CurrentAuthentication, team_service: TeamServiceDependency
) -> list[TeamMemberRead]:
    """List the Manager's workspace members, including invitation and activation state."""
    try:
        return team_service.list_members(authentication.user)
    except TeamPermissionError as error:
        raise _team_error(error) from error


@router.post(
    "/invitations",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    payload: InviteTeamMemberRequest,
    authentication: CurrentAuthentication,
    team_service: TeamServiceDependency,
) -> TeamMemberRead:
    """Create a standard User invitation and deliver its one-time acceptance link by email."""
    try:
        invitation = team_service.invite(authentication.user, payload)
    except (TeamPermissionError, TeamConflictError) as error:
        raise _team_error(error) from error
    EmailDeliveryService(get_settings()).send_team_invitation(
        invitation.member.email, invitation.raw_token
    )
    return invitation.member


@router.post("/invitations/accept", response_model=MessageResponse)
def accept_invitation(
    payload: AcceptTeamInvitationRequest, team_service: TeamServiceDependency
) -> MessageResponse:
    """Activate an invited User after they set their own password through a valid one-use link."""
    try:
        team_service.accept_invitation(payload)
    except InvalidInvitationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation is invalid, expired, or has already been used",
        ) from error
    return MessageResponse(message="Invitation accepted. You can now sign in.")


@router.post("/members/{member_id}/resend-invitation", response_model=TeamMemberRead)
def resend_invitation(
    member_id: UUID,
    authentication: CurrentAuthentication,
    team_service: TeamServiceDependency,
) -> TeamMemberRead:
    """Invalidate a pending invite and send a fresh acceptance link."""
    try:
        invitation = team_service.resend_invitation(authentication.user, member_id)
    except (TeamPermissionError, TeamMemberNotFoundError, TeamConflictError) as error:
        raise _team_error(error) from error
    EmailDeliveryService(get_settings()).send_team_invitation(
        invitation.member.email, invitation.raw_token
    )
    return invitation.member


@router.patch("/members/{member_id}", response_model=TeamMemberRead)
def update_member(
    member_id: UUID,
    payload: TeamMemberUpdate,
    authentication: CurrentAuthentication,
    team_service: TeamServiceDependency,
) -> TeamMemberRead:
    """Update a standard member's operational settings without changing their access role."""
    try:
        return team_service.update_member(authentication.user, member_id, payload)
    except (TeamPermissionError, TeamMemberNotFoundError, TeamConflictError) as error:
        raise _team_error(error) from error


@router.post("/members/{member_id}/deactivate", response_model=TeamMemberRead)
def deactivate_member(
    member_id: UUID,
    authentication: CurrentAuthentication,
    team_service: TeamServiceDependency,
) -> TeamMemberRead:
    """Revoke a standard member's sessions and preserve their historical records."""
    try:
        return team_service.deactivate_member(authentication.user, member_id)
    except (TeamPermissionError, TeamMemberNotFoundError, TeamConflictError) as error:
        raise _team_error(error) from error


@router.post("/members/{member_id}/reactivate", response_model=TeamMemberRead)
def reactivate_member(
    member_id: UUID,
    authentication: CurrentAuthentication,
    team_service: TeamServiceDependency,
) -> TeamMemberRead:
    """Restore access for a previously accepted, deactivated standard member."""
    try:
        return team_service.reactivate_member(authentication.user, member_id)
    except (TeamPermissionError, TeamMemberNotFoundError, TeamConflictError) as error:
        raise _team_error(error) from error
