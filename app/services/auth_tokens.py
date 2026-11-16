import hashlib
import secrets


def create_auth_token() -> str:
    """Create a high-entropy raw token for a reset or verification link."""
    return secrets.token_urlsafe(48)


def hash_auth_token(token: str) -> str:
    """Hash a raw auth token before its only persisted representation is stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
