from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

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


def verify_token(token: str, max_age=60 * 60 * 24) -> str:  # 24 hours
    """Verify a token and extract the email.

    Args:
        token: The token to verify.
        max_age: Maximum age of the token in seconds. Defaults to 24 hours.

    Returns:
        str: The email address if the token is valid, None otherwise.
    """
    try:
        email = signer.unsign(token, max_age=max_age)

        return email
    except (BadSignature, SignatureExpired):

        return None


def update_user_from_form(form) -> User:
    """Update a user based on a validated form.

    Args:
        form: A validated form containing user data.

    Returns:
        User: The updated user instance.

    Note:
        Assumes the form is already validated.
    """
    user = form.instance
    for field in [
        "first_name",
        "last_name",
    ]:
        setattr(user, field, form.cleaned_data[field])
    user.save()

    return user
