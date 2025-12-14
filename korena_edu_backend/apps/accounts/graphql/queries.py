import strawberry
from strawberry.types import Info

from apps.accounts.graphql.types import UserType
from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql


@strawberry.type
class AccountsQuery:
    """Root queries for account/user operations."""

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql])
    def me(self, info: Info) -> UserType:
        """Return the authenticated and verified user."""

        return info.context.request.user
