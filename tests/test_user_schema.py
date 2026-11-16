import pytest
from pydantic import ValidationError

from app.models.user import UserRole
from app.schemas.user import UserCreate


def test_user_create_normalizes_email_and_uses_defaults() -> None:
    user = UserCreate(
        name="Rahul Kumar",
        email="RAHUL@HYDERABADINTERIORS.COM",
        password="a-long-enough-password",
    )

    assert user.email == "rahul@hyderabadinteriors.com"
    assert user.role is UserRole.USER
    assert user.max_open_leads == 10


def test_user_create_rejects_invalid_capacity() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            name="Rahul Kumar",
            email="rahul@example.com",
            password="a-long-enough-password",
            max_open_leads=-1,
        )
