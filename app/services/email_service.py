
import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:

    def _send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from_email
        message["To"] = recipient_email
        message.set_content(body)

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=10,
        ) as smtp:
            smtp.starttls()
            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )
            smtp.send_message(message)

    def send_verification_email(
        self,
        recipient_email: str,
        verification_token: str,
    ) -> None:
        verification_link = (
            "http://127.0.0.1:8000/api/v1/auth/verify-email"
            f"?token={verification_token}"
        )

        body = f"""
Hello,

Thank you for registering with ZFP.

Please verify your email by opening this link:

{verification_link}

If you did not create this account, you can ignore this email.

Regards,
ZFP Team
"""

        self._send_email(
            recipient_email=recipient_email,
            subject="Verify your ZFP account",
            body=body,
        )

    def send_password_reset_email(
        self,
        recipient_email: str,
        reset_token: str,
    ) -> None:
        reset_link = (
            "http://127.0.0.1:8000/api/v1/auth/reset-password"
            f"?token={reset_token}"
        )

        body = f"""
Hello,

We received a request to reset your ZFP account password.

Use this link to reset your password:

{reset_link}

This link will expire after 30 minutes.

If you did not request a password reset, you can ignore this email.

Regards,
ZFP Team
"""

        self._send_email(
            recipient_email=recipient_email,
            subject="Reset your ZFP password",
            body=body,
        )
