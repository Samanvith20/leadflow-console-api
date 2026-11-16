import hashlib


def hash_raw_payload(raw_payload: bytes) -> str:
    """Hash the untouched request body for idempotency conflict detection."""
    return hashlib.sha256(raw_payload).hexdigest()
