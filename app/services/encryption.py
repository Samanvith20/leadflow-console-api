from cryptography.fernet import Fernet, InvalidToken


class EncryptionConfigurationError(RuntimeError):
    """Raised when encrypted storage is requested without a valid configured key."""


class EncryptionService:
    """Encrypt small sensitive values before they are written to PostgreSQL."""

    def __init__(self, key: str | None) -> None:
        if not key:
            raise EncryptionConfigurationError("WEBHOOK_ENCRYPTION_KEY is not configured")
        try:
            self._fernet = Fernet(key.encode())
        except (TypeError, ValueError) as error:
            raise EncryptionConfigurationError("WEBHOOK_ENCRYPTION_KEY is invalid") from error

    def encrypt(self, plaintext: str) -> str:
        """Return encrypted text suitable for a ciphertext database column."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Return plaintext only inside trusted server-side HMAC verification code."""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as error:
            raise EncryptionConfigurationError("Stored ciphertext cannot be decrypted") from error
