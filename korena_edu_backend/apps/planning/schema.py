from typing import Any

import graphene
from apps.planning.models import PlanningRow, PlanningSheet
from graphene_django import DjangoObjectType
from graphql import GraphQLResolveInfo


class PlanningRowType(DjangoObjectType):
    """GraphQL type representing a single row inside a planning sheet."""

    class Meta:
        model = PlanningRow
        fields = ("id", "index", "data", "created_at", "updated_at")


class PlanningSheetType(DjangoObjectType):
    """GraphQL type representing a planning sheet with its associated rows."""

    rows = graphene.List(
        lambda: PlanningRowType,
        description="List of rows contained in this planning sheet.",
    )

    class Meta:
        model = PlanningSheet
        fields = (
            "id",
            "title",
            "description",
            "sheet_type",
            "grade",
            "area",
            "school_year",
            "level",
            "columns_schema",
            "created_at",
            "updated_at",
            "rows",
        )

    def resolve_rows(
        self,
        info: GraphQLResolveInfo,
        **kwargs: Any,
    ) -> list[PlanningRow]:
        """Return all rows belonging to this sheet.

        Args:
            info (GraphQLResolveInfo): Resolver context information.
            **kwargs: Additional arguments (unused).

        Returns:
            list[PlanningRow]: Ordered list of rows.
        """
        return list(self.rows.all())


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
