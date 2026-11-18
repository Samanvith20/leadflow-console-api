from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_password_hasher = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=2)


def hash_password(password: str) -> str:
    """Return an Argon2id password hash; plaintext passwords must never reach PostgreSQL."""
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Safely compare a candidate password with its stored Argon2id hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Tell callers when a successful login should upgrade an old Argon2 hash."""
    return _password_hasher.check_needs_rehash(password_hash)
