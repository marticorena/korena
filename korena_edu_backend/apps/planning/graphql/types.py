from datetime import datetime
from typing import List

import strawberry

from apps.planning.models import PlanningRow, PlanningSheet


@strawberry.django.type(PlanningRow)
class PlanningRowType:
    """Single row inside a planning sheet."""

    id: strawberry.ID
    index: int
    data: strawberry.scalars.JSON
    created_at: datetime
    updated_at: datetime


@strawberry.django.type(PlanningSheet)
class PlanningSheetType:
    """Planning sheet with associated rows."""

    id: strawberry.ID
    title: str
    description: str
    sheet_type: str
    grade: str
    area: str
    school_year: str
    level: str
    columns_schema: strawberry.scalars.JSON
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def rows(self) -> List[PlanningRowType]:
        return list(self.rows.all())
