from typing import List

import strawberry
from strawberry.types import Info

from apps.core.graphql.permissions import IsAuthenticated, IsVerified
from apps.planning.graphql.types import PlanningSheetType
from apps.planning.models import PlanningSheet


@strawberry.type
class PlanningQuery:
    """Planning sheet queries."""

    @strawberry.field(permission_classes=[IsAuthenticated, IsVerified])
    def my_planning_sheets(
        self,
        info: Info,
    ) -> List[PlanningSheetType]:
        user = info.context.request.user

        return list(PlanningSheet.objects.filter(owner=user))
