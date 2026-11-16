from app.services.intake_integrity import hash_raw_payload


def test_payload_hash_is_stable_for_identical_raw_bytes() -> None:
    payload = b'{"event_id":"web_123","fields":{"email":"priya@example.com"}}'

    assert hash_raw_payload(payload) == hash_raw_payload(payload)
    assert len(hash_raw_payload(payload)) == 64


def test_payload_hash_changes_when_raw_payload_changes() -> None:
    first_payload = b'{"event_id":"web_123","fields":{"budget":500000}}'
    changed_payload = b'{"event_id":"web_123","fields":{"budget":800000}}'

    assert hash_raw_payload(first_payload) != hash_raw_payload(changed_payload)
