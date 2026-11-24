import logging
from urllib.parse import urlencode

import resend

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailDeliveryService:
    """Deliver account-security links without exposing raw tokens in API responses or logs in production."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_password_reset(self, recipient: str, raw_token: str) -> None:
        """Send a one-use reset link; development logs the link only for local testing."""
        self._send_security_link(
            recipient=recipient,
            path="/reset-password",
            raw_token=raw_token,
            subject="Reset your Leadflow password",
            heading="Reset your password",
            description="Use this link within 30 minutes to choose a new password.",
        )

    def send_email_verification(self, recipient: str, raw_token: str) -> None:
        """Send a one-use email-verification link after registration or a resend request."""
        self._send_security_link(
            recipient=recipient,
            path="/verify-email",
            raw_token=raw_token,
            subject="Verify your Leadflow email",
            heading="Verify your email",
            description="Use this link within 24 hours to verify your Leadflow account.",
        )

    def send_team_invitation(self, recipient: str, raw_token: str) -> None:
        """Send a one-use invitation so a teammate can choose their own Leadflow password."""
        self._send_security_link(
            recipient=recipient,
            path="/accept-invite",
            raw_token=raw_token,
            subject="You are invited to Leadflow",
            heading="Join your Leadflow workspace",
            description="Use this link within 10 minutes to choose your password and activate your account.",
        )

    def _send_security_link(
        self,
        *,
        recipient: str,
        path: str,
        raw_token: str,
        subject: str,
        heading: str,
        description: str,
    ) -> None:
        url = f"{self._settings.frontend_base_url.rstrip('/')}{path}?{urlencode({'token': raw_token})}"
        if not self._settings.resend_api_key or not self._settings.email_from:
            logger.warning("Development auth email for %s: %s", recipient, url)
            return

        resend.api_key = self._settings.resend_api_key
        resend.Emails.send(
            {
                "from": self._settings.email_from,
                "to": [recipient],
                "subject": subject,
                "html": f"<h1>{heading}</h1><p>{description}</p><p><a href='{url}'>Continue</a></p>",
            }
        )
