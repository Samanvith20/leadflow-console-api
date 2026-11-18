from app.services.passwords import hash_password, password_needs_rehash, verify_password


def test_passwords_are_hashed_and_verified_with_argon2() -> None:
    password = "a-long-enough-password"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2")
    assert verify_password(password_hash, password)
    assert not password_needs_rehash(password_hash)


def test_password_verification_rejects_the_wrong_password_and_invalid_hash() -> None:
    password_hash = hash_password("a-long-enough-password")

    assert not verify_password(password_hash, "wrong-password")
    assert not verify_password("not-a-valid-password-hash", "a-long-enough-password")
