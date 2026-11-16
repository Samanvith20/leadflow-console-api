from app.services.session_tokens import create_session_token, hash_session_token


def test_session_token_hash_is_sha256_hex() -> None:
    token = create_session_token()
    token_hash = hash_session_token(token)

    assert token != token_hash
    assert len(token_hash) == 64
    assert token_hash == hash_session_token(token)


def test_session_tokens_are_unique() -> None:
    assert create_session_token() != create_session_token()
