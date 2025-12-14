import strawberry
from strawberry.types import Info

from apps.accounts.graphql.types import UserType
from apps.core.endpoints.permissions import IsAuthenticatedGraphql


@strawberry.type
class AccountsQuery:
    """Root queries for account/user operations."""

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql])
    def me(self, info: Info) -> UserType:
        """Return the authenticated and active user."""

        return info.context.request.user
