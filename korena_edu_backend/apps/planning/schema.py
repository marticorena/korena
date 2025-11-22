import graphene
from graphene_django import DjangoObjectType

from apps.planning.models import PlanningSheet, PlanningRow


class PlanningRowType(DjangoObjectType):
    class Meta:
        model = PlanningRow
        fields = ("id", "index", "data")


class PlanningSheetType(DjangoObjectType):
    rows = graphene.List(PlanningRowType)

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
            "rows",
        )

    def resolve_rows(self, info):
        return self.rows.all()


class PlanningQuery(graphene.ObjectType):
    my_planning_sheets = graphene.List(PlanningSheetType)

    def resolve_my_planning_sheets(self, info):
        user = info.context.user
        if user.is_anonymous:
            return PlanningSheet.objects.none()
        return PlanningSheet.objects.filter(owner=user)
