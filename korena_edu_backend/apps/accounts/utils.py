from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.template.loader import render_to_string

from premailer import transform

from apps.notifications.models import EmailLog

signer = TimestampSigner()
User = get_user_model()


def generate_verification_token(email: str) -> str:
    """Generate a signed token for email verification.

    Args:
        email: The email address to sign.

    Returns:
        str: A signed token containing the email.
    """

    return signer.sign(email)


def generate_token_and_email(user: Any) -> tuple[str, EmailLog]:
    """Generate a verification token, build verification email content, and persist email log.

    Args:
        user: The user instance for whom the verification token is generated.

    Returns:
        tuple[str, EmailLog]: A tuple containing:
            - str: The raw verification token before encoding.
            - EmailLog: The saved email log entry containing HTML and plain message versions.
    """
    token = generate_verification_token(user.email)
    encoded_token = quote(token, safe="")

    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={encoded_token}"

    html_message = render_to_string(
        "users/email_verification.html",
        {"user": user, "verify_url": verify_url},
    )
    html_message = transform(html_message)
    plain_message = f"Hola {user.first_name}, verifica tu cuenta aquí: {verify_url}"

    subject = "Korena - Verifica tu cuenta"

    email_log = EmailLog.objects.create(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=user.email,
        user=user,
        subject=subject,
        plain_message=plain_message,
        html_message=html_message,
    )

    return token, email_log


def verify_token(token: str, max_age: int = 60 * 60 * 24) -> str | None:
    """Verify a token and extract the email.

    Args:
        token: The token to verify.
        max_age: Maximum age of the token in seconds. Defaults to 24 hours.

    Returns:
        str | None: The email address if the token is valid, otherwise None.
    """
    try:
        email = signer.unsign(token, max_age=max_age)

        return email
    except (BadSignature, SignatureExpired):
        return None
