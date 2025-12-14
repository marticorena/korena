import strawberry.django

from apps.accounts.models import User


@strawberry.type
class TokenPair:
    """Pair of access and refresh JWT tokens returned after authentication."""

    access: str
    refresh: str


@strawberry.django.type(User)
class UserType:
    """GraphQL type representing a safe view of the User model."""

    id: strawberry.ID
    email: str
    first_name: str
    last_name: str
    role: str
    is_verified: bool


@strawberry.type
class RegisterUserPayload:
    """Payload for registerUser mutation."""

    token: str


@strawberry.type
class EmailPayload:
    """Generic payload that returns an email string."""

    email: str
