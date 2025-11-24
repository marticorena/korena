from typing import Optional

import graphene
from apps.accounts.models import User
from apps.accounts.schema.types import UserType
from graphql import GraphQLResolveInfo


class Query(graphene.ObjectType):
    """Root query class for user-related GraphQL operations."""

    me = graphene.Field(UserType)

    def resolve_me(self, info: GraphQLResolveInfo, **kwargs) -> Optional[User]:
        """Return the authenticated user.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver information.
            **kwargs: Additional arguments passed by Graphene.

        Returns:
            Optional[User]: Returns the current user or None if anonymous.
        """
        user: User = info.context.user

        # Anonymous users do not have associated User instances
        if user.is_anonymous:
            return None

        return user
