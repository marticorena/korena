from typing import Optional

import strawberry
from strawberry.types import Info

from apps.accounts.graphql.types import UserType
from apps.accounts.models import User


@strawberry.type
class AccountsQuery:
    """Root queries for account/user operations."""

    @strawberry.field
    def me(self, info: Info) -> Optional[UserType]:
        """Return the authenticated user.

        Args:
            info: Strawberry resolver info containing context with request.

        Returns:
            Optional[UserType]: The authenticated user or None if anonymous.
        """
        user: User = info.context.request.user

        if user.is_anonymous:
            return None

        return user
