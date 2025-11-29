from typing import Any

import graphene
from graphql import GraphQLResolveInfo
from graphql_jwt.decorators import login_required

from apps.accounts.schema.decorators import verified_required
from apps.planning.models import PlanningSheet
from apps.planning.schema.types import PlanningSheetType


class PlanningQuery(graphene.ObjectType):
    """GraphQL queries related to planning sheets."""

    my_planning_sheets = graphene.List(
        PlanningSheetType,
        description="Return all planning sheets created by the authenticated user.",
    )

    @login_required
    @verified_required
    def resolve_my_planning_sheets(
        self,
        info: GraphQLResolveInfo,
        **kwargs: Any,
    ) -> list[PlanningSheet]:
        """Return planning sheets owned by the authenticated user.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver information.
            **kwargs: Additional arguments (unused).

        Returns:
            list[PlanningSheet]: User-owned planning sheets.
        """
        user = info.context.user

        queryset = PlanningSheet.objects.filter(owner=user)

        return list(queryset)
