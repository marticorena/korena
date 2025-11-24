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
