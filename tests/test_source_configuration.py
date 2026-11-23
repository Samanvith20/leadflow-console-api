import pytest
from pydantic import ValidationError

from app.schemas.source import SourceCreate


def test_website_form_requires_contact_method_and_message() -> None:
    with pytest.raises(ValidationError):
        SourceCreate(
            name="Website",
            source_type="website_form",
            configuration={
                "field_definitions": [
                    {
                        "key": "name",
                        "label": "Name",
                        "field_type": "string",
                        "required": True,
                        "maps_to": "contact.full_name",
                    }
                ]
            },
        )
