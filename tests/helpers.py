from typing import Dict

from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def auth_headers_for(user: User) -> Dict[str, str]:
    """Build Authorization headers for a given user using JWT access token."""
    token = AccessToken.for_user(user)

    return {
        "HTTP_AUTHORIZATION": f"Bearer {token}",
    }
