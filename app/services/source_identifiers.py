import secrets


def create_source_public_id() -> str:
    """Create a non-guessable identifier safe to expose in a webhook URL."""
    return f"src_{secrets.token_urlsafe(18)}"
