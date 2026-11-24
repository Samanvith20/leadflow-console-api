import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.contact import Contact
from app.models.intake_event import IntakeEvent, IntakeEventStatus
from app.models.lead import Lead
from app.models.source import Source, SourceStatus
from app.models.workspace import Workspace
from app.services.audit import record_audit_event
from app.services.encryption import EncryptionService
from app.services.intake_integrity import hash_raw_payload


class WebhookError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail, self.status_code = detail, status_code


@dataclass(frozen=True)
class WebhookReceipt:
    """The durable event receipt and whether this delivery was already accepted."""

    event: IntakeEvent
    already_received: bool


class WebhookService:
    """Verify signed source deliveries and turn configured fields into one contact and lead."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.crypto = EncryptionService(get_settings().webhook_encryption_key)

    def receive(
        self, public_id: str, raw: bytes, timestamp: str | None, signature: str | None
    ) -> WebhookReceipt:
        source = self.db.scalar(select(Source).where(Source.public_id == public_id))
        if not source or source.status is not SourceStatus.ACTIVE:
            raise WebhookError("Unknown or inactive source", 403)
        if not timestamp or not signature:
            raise WebhookError("Missing webhook signature", 401)
        try:
            age = abs(datetime.now(UTC).timestamp() - int(timestamp))
        except ValueError:
            raise WebhookError("Invalid webhook timestamp", 401)
        if age > 300:
            raise WebhookError("Expired webhook timestamp", 401)
        secret = self.crypto.decrypt(source.webhook_secret_ciphertext or "")
        expected = (
            "v1="
            + hmac.new(secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(expected, signature):
            raise WebhookError("Invalid webhook signature", 401)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise WebhookError("Body must be valid JSON", 422)
        event_id = payload.get("event_id")
        data = payload.get("data")
        if not isinstance(event_id, str) or not event_id or not isinstance(data, dict):
            raise WebhookError("event_id and data are required", 422)
        payload_hash = hash_raw_payload(raw)
        existing_event = self.db.scalar(
            select(IntakeEvent).where(
                IntakeEvent.source_id == source.id, IntakeEvent.source_event_id == event_id
            )
        )
        if existing_event is not None:
            if existing_event.payload_hash != payload_hash:
                raise WebhookError("event_id was already used with different data", 409)
            return WebhookReceipt(event=existing_event, already_received=True)
        fields = {x["key"]: x for x in source.configuration.get("field_definitions", [])}
        unknown = set(data) - set(fields)
        if unknown:
            raise WebhookError("Unknown data fields: " + ", ".join(sorted(unknown)), 422)
        for key, field in fields.items():
            if field.get("required") and (key not in data or data[key] in (None, "")):
                raise WebhookError(f"Missing required field: {key}", 422)
        workspace = self.db.get(Workspace, source.workspace_id)
        retention = workspace.configuration.get("operational", {}).get(
            "lead_data_retention_days", 90
        )
        event = IntakeEvent(
            workspace_id=source.workspace_id,
            source_id=source.id,
            source_event_id=event_id,
            raw_payload_ciphertext=self.crypto.encrypt(raw.decode()),
            payload_hash=payload_hash,
            status=IntakeEventStatus.PROCESSED,
            purge_at=datetime.now(UTC) + timedelta(days=retention),
            processed_at=datetime.now(UTC),
        )
        self.db.add(event)
        self.db.flush()
        mapped = {"custom_fields": {}}
        for key, value in data.items():
            target = fields[key]["maps_to"]
            if target == "lead.custom_fields":
                mapped["custom_fields"][key] = value
            else:
                mapped[target] = value
        email = mapped.get("contact.email")
        contact = (
            self.db.scalar(
                select(Contact).where(
                    Contact.workspace_id == source.workspace_id, Contact.email == email
                )
            )
            if email
            else None
        )
        if not contact:
            identity = {
                k: mapped.get(k)
                for k in (
                    "contact.full_name",
                    "contact.email",
                    "contact.phone_e164",
                    "contact.company_name",
                )
            }
            if any(identity.values()):
                contact = Contact(
                    workspace_id=source.workspace_id,
                    full_name=identity["contact.full_name"],
                    email=identity["contact.email"],
                    phone_e164=identity["contact.phone_e164"],
                    company_name=identity["contact.company_name"],
                )
                self.db.add(contact)
                self.db.flush()
        lead = Lead(
            workspace_id=source.workspace_id,
            contact_id=contact.id if contact else None,
            intake_event_id=event.id,
            enquiry_message=mapped.get("lead.enquiry_message"),
            custom_fields=mapped["custom_fields"],
        )
        self.db.add(lead)
        self.db.flush()
        record_audit_event(
            self.db,
            workspace_id=source.workspace_id,
            action="lead.received",
            entity_type="lead",
            entity_id=lead.id,
            metadata={
                "source_id": str(source.id),
                "source_name": source.name,
                "contact_name": contact.full_name if contact else None,
            },
        )
        try:
            self.db.commit()
        except IntegrityError:
            # Concurrent retries can pass the first lookup at the same time. The
            # database uniqueness constraint is the final idempotency guarantee.
            self.db.rollback()
            existing_event = self.db.scalar(
                select(IntakeEvent).where(
                    IntakeEvent.source_id == source.id,
                    IntakeEvent.source_event_id == event_id,
                )
            )
            if existing_event is not None and existing_event.payload_hash == payload_hash:
                return WebhookReceipt(event=existing_event, already_received=True)
            raise
        return WebhookReceipt(event=event, already_received=False)
