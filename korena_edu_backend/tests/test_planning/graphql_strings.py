"""GraphQL operation strings for planning-related tests."""

MY_PLANNING_SHEETS_QUERY = """
query MyPlanningSheets {
  myPlanningSheets {
    id
    title
    description
    sheetType
    grade
    area
    schoolYear
    level
    columnsSchema
    createdAt
    updatedAt
    rows {
      id
      index
      data
      createdAt
      updatedAt
    }
  }
}
"""

__all__ = [
    "MY_PLANNING_SHEETS_QUERY",
]
