from app.services.auth_tokens import create_auth_token, hash_auth_token


def test_auth_token_is_high_entropy_and_only_its_hash_is_persistable() -> None:
    token = create_auth_token()

    assert len(token) >= 64
    assert len(hash_auth_token(token)) == 64
    assert hash_auth_token(token) == hash_auth_token(token)


def test_different_auth_tokens_have_different_hashes() -> None:
    assert hash_auth_token(create_auth_token()) != hash_auth_token(create_auth_token())
