from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.auth_token import AuthTokenPurpose
from app.models.user import UserRole
from app.schemas.team import InviteTeamMemberRequest, TeamMemberUpdate
from app.services.team import TeamService


def test_invitation_email_is_normalized() -> None:
    request = InviteTeamMemberRequest(name="Asha", email="ASHA@EXAMPLE.COM")

    assert request.email == "asha@example.com"
    assert AuthTokenPurpose.TEAM_INVITATION.value == "team_invitation"


def test_member_update_requires_a_change() -> None:
    with pytest.raises(ValidationError):
        TeamMemberUpdate()


@pytest.mark.parametrize(
    ("is_active", "deactivated", "expected_status"),
    [(False, False, "invited"), (True, False, "active"), (False, True, "deactivated")],
)
def test_team_member_status_represents_invitation_lifecycle(
    is_active: bool, deactivated: bool, expected_status: str
) -> None:
    now = datetime.now(UTC)
    member = SimpleNamespace(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Asha",
        email="asha@example.com",
        role=UserRole.USER,
        is_active=is_active,
        is_available=True,
        max_open_leads=10,
        invited_at=now,
        invitation_accepted_at=now if is_active else None,
        deactivated_at=now if deactivated else None,
        created_at=now,
        updated_at=now,
    )

    assert TeamService._to_read(member).status == expected_status
