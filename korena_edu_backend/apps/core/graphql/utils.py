from typing import Any, Dict, List

from django.forms import Form

from strawberry.exceptions import StrawberryGraphQLError

from apps.core.messages import ERROR_MESSAGES


def build_form_errors(form: Form) -> List[Dict[str, Any]]:
    """Convert Django form errors into a structured list for GraphQL."""
    json_errors = form.errors.get_json_data()
    result = []

    for field, errors in json_errors.items():
        for err in errors:
            code = err.get("code", "invalid")
            default_message = err.get("message", "")

            field_code_key = f"{field}.{code}"
            if field_code_key in ERROR_MESSAGES:
                message = ERROR_MESSAGES[field_code_key]

            # Fallback
            else:
                message = default_message

            result.append(
                {
                    "field": field,
                    "message": message,
                    "code": code,
                }
            )

    return result


def assert_field_error(fields: List[Dict[str, Any]], field: str, code: str) -> None:
    """Assert that a field error with the given code exists.

    Args:
        fields: List of field error dicts.
        field: Expected field name.
        code: Expected error code.
    """
    assert any(
        item.get("field") == field and item.get("code") == code for item in fields
    ), f"Expected error for field '{field}' with code '{code}' not found. Got: {fields}"


def raise_form_error(fields):
    """Raise a GraphQL validation error using centralized messages."""
    raise StrawberryGraphQLError(
        message=ERROR_MESSAGES["validation.error"],
        extensions={
            "code": "BAD_USER_INPUT",
            "fields": fields,
        },
    )
