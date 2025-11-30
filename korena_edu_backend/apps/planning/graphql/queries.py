from typing import List

import strawberry
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql
from apps.planning.graphql.types import PlanningSheetType
from apps.planning.models import PlanningSheet


@strawberry.type
class PlanningQuery:
    """Planning sheet queries."""

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql])
    def my_planning_sheets(
        self,
        info: Info,
    ) -> List[PlanningSheetType]:
        user = info.context.request.user

        return list(PlanningSheet.objects.filter(owner=user))
