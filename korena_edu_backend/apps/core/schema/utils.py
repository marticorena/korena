from typing import Any, Dict, List


def build_form_errors(form) -> List[Dict[str, Any]]:
    """Convert Django form errors into a structured list for GraphQL.

    Each item contains:
        - field: field name or "non_field_errors"
        - message: user-friendly error message
        - code: validator code if available
    """
    json_errors = form.errors.get_json_data()
    result = []

    for field, errors in json_errors.items():
        for err in errors:
            result.append(
                {
                    "field": field,
                    "message": err.get("message", ""),
                    "code": err.get("code", "invalid"),
                }
            )

    return result
