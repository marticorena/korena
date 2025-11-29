from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from apps.core.messages import ERROR_MESSAGES
from apps.planning.models import PlanningRow, PlanningSheet
from tests.test_planning.graphql_strings import MY_PLANNING_SHEETS_QUERY

pytestmark = pytest.mark.django_db

User = get_user_model()


def create_planning_sheet(
    owner: User,
    title: str = "Mi planificación",
    level: str = "TEACHER",
    sheet_type: str = "ANNUAL",
    grade: str = "",
    area: str = "",
    school_year: int = 2025,
    columns_schema: list[dict[str, Any]] | None = None,
) -> PlanningSheet:
    """Helper to create a PlanningSheet for tests."""
    if columns_schema is None:
        columns_schema = [
            {"field": "col1", "headerName": "Columna 1"},
            {"field": "col2", "headerName": "Columna 2"},
        ]

    sheet = PlanningSheet.objects.create(
        owner=owner,
        level=level,
        title=title,
        description="Descripción de prueba",
        sheet_type=sheet_type,
        grade=grade,
        area=area,
        school_year=school_year,
        columns_schema=columns_schema,
    )

    return sheet


def create_planning_row(
    sheet: PlanningSheet,
    index: int,
    data: Dict[str, Any] | None = None,
) -> PlanningRow:
    """Helper to create a PlanningRow for tests."""
    if data is None:
        data = {"col1": f"valor-{index}", "col2": index}

    row = PlanningRow.objects.create(
        sheet=sheet,
        index=index,
        data=data,
    )

    return row


def test_my_planning_sheets_returns_only_owned_sheets_for_verified_user(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """myPlanningSheets should return only sheets owned by the verified user."""
    # Sheets for verified user.
    sheet1 = create_planning_sheet(verified_user, title="Planificación 1")
    sheet2 = create_planning_sheet(verified_user, title="Planificación 2")

    # Sheet for another user.
    other_user = User.objects.create_user(
        email="other-planning@example.com",
        password="P4ss-w0rd!",
        first_name="Other",
        last_name="Planning",
    )
    create_planning_sheet(other_user, title="Planificación de otro usuario")

    result: Dict[str, Any] = exec_gql(
        MY_PLANNING_SHEETS_QUERY,
        context=verified_context,
    )

    nodes = result["data"]["myPlanningSheets"]
    titles = {n["title"] for n in nodes}

    assert len(nodes) == 2
    assert titles == {sheet1.title, sheet2.title}


def test_my_planning_sheets_includes_rows_for_each_sheet(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """myPlanningSheets should include rows associated to each sheet."""
    sheet = create_planning_sheet(verified_user, title="Planificación con filas")
    create_planning_row(sheet, index=1, data={"col1": "A", "col2": 1})
    create_planning_row(sheet, index=2, data={"col1": "B", "col2": 2})

    result: Dict[str, Any] = exec_gql(
        MY_PLANNING_SHEETS_QUERY,
        context=verified_context,
    )

    nodes = result["data"]["myPlanningSheets"]
    assert len(nodes) == 1

    rows = nodes[0]["rows"]
    assert len(rows) == 2

    indices = [row["index"] for row in rows]
    assert indices == [1, 2]


def test_my_planning_sheets_requires_verified_user(
    gql_client,
    non_verified_context,
    non_verified_user: User,
) -> None:
    """myPlanningSheets should fail when user is authenticated but not verified."""
    create_planning_sheet(non_verified_user, title="Planificación no verificada")

    result: Dict[str, Any] = gql_client.execute(
        MY_PLANNING_SHEETS_QUERY,
        context_value=non_verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]
    assert result["data"]["myPlanningSheets"] is None


def test_my_planning_sheets_requires_authentication(
    gql_client,
    anon_context,
) -> None:
    """myPlanningSheets should fail for anonymous users."""
    result: Dict[str, Any] = gql_client.execute(
        MY_PLANNING_SHEETS_QUERY,
        context_value=anon_context,
    )

    assert "errors" in result
    assert result["data"]["myPlanningSheets"] is None
