from cryptography.fernet import Fernet

from app.services.encryption import EncryptionService


def test_encryption_round_trip_keeps_plaintext_out_of_ciphertext() -> None:
    secret = "secret-value"
    service = EncryptionService(Fernet.generate_key().decode())
    ciphertext = service.encrypt(secret)
    assert ciphertext != secret
    assert service.decrypt(ciphertext) == secret
