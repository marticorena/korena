from typing import Any

import graphene
from apps.planning.models import PlanningSheet
from apps.planning.schema.types import PlanningSheetType
from graphql import GraphQLResolveInfo


class PlanningQuery(graphene.ObjectType):
    """GraphQL queries related to planning sheets."""

    my_planning_sheets = graphene.List(
        PlanningSheetType,
        description="Return all planning sheets created by the authenticated user.",
    )

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
            list[PlanningSheet]: User-owned planning sheets or an empty list.
        """
        user = info.context.user

        if user.is_anonymous:
            return []

        queryset = PlanningSheet.objects.filter(owner=user)

        return list(queryset)
