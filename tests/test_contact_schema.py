import pytest
from pydantic import ValidationError

from app.schemas.contact import ContactCreate


def test_contact_allows_name_only_and_normalizes_email() -> None:
    name_only_contact = ContactCreate(full_name="Priya Sharma")
    email_contact = ContactCreate(email="PRIYA@EXAMPLE.COM")

    assert name_only_contact.full_name == "Priya Sharma"
    assert email_contact.email == "priya@example.com"


def test_contact_rejects_missing_identity() -> None:
    with pytest.raises(ValidationError):
        ContactCreate()


def test_contact_rejects_non_e164_phone_number() -> None:
    with pytest.raises(ValidationError):
        ContactCreate(full_name="Priya Sharma", phone_e164="98765 43210")
