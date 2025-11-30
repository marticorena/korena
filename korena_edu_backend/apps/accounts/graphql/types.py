from typing import Optional

import strawberry.django

from apps.accounts.models import User


@strawberry.type
class TokenPair:
    """Pair of access and refresh JWT tokens returned after authentication.

    This type is used in authentication-related mutations.
    """

    access: str
    refresh: str


@strawberry.django.type(User)
class UserType:
    """GraphQL type representing a safe view of the User model.

    Only exposes non-sensitive fields that are safe to share with clients.
    """

    id: strawberry.ID
    email: str
    first_name: str
    last_name: str
    role: str
    is_verified: bool
    avatar_url: Optional[str]


@strawberry.type
class RegisterUserPayload:
    """Payload for registerUser mutation."""

    token: str


@strawberry.type
class EmailPayload:
    """Generic payload that returns an email string."""

    email: str
