import hashlib
import secrets


def create_session_token() -> str:
    """Create a high-entropy opaque token suitable for a secure browser cookie."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Return the SHA-256 hash stored in PostgreSQL instead of the raw browser token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
