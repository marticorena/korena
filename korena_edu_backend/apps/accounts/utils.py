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


def generate_activation_token(email: str) -> str:
    """Generate a signed token for account activation.

    Args:
        email: The email address to sign.

    Returns:
        str: A signed token containing the email.
    """

    return signer.sign(email)


def generate_token_and_email(user: Any) -> tuple[str, EmailLog]:
    """Generate an activation token, build account activation email content, and persist email log.

    Args:
        user: The user instance for whom the activation token is generated.

    Returns:
        tuple[str, EmailLog]: A tuple containing:
            - str: The raw activation token before encoding.
            - EmailLog: The saved email log entry containing HTML and plain message versions.
    """
    token = generate_activation_token(user.email)
    encoded_token = quote(token, safe="")

    activation_url = f"{settings.FRONTEND_URL}/activate-account?token={encoded_token}"

    html_message = render_to_string(
        "users/account_activation.html",
        {"user": user, "activation_url": activation_url},
    )
    html_message = transform(html_message)
    plain_message = f"Hola {user.first_name}, activa tu cuenta aquí: {activation_url}"

    subject = "Korena - Activa tu cuenta"

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
