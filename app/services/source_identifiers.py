import secrets


def create_source_public_id() -> str:
    """Create a non-guessable identifier safe to expose in a webhook URL."""
    return f"src_{secrets.token_urlsafe(18)}"


def create_webhook_secret() -> str:
    """Create a high-entropy per-source HMAC secret shown to a Manager only once."""
    return secrets.token_urlsafe(48)
