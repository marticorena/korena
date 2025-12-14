from typing import TypedDict

from django.forms import Form

from strawberry.exceptions import StrawberryGraphQLError

from apps.core.messages import ERROR_MESSAGES


class FieldError(TypedDict):
    field: str
    message: str
    code: str


def build_form_errors(form: Form) -> list[FieldError]:
    """Convert Django form errors into a structured list for GraphQL."""
    json_errors = form.errors.get_json_data()
    result: list[FieldError] = []

    for field, errors in json_errors.items():
        for err in errors:
            code = str(err.get("code") or "invalid")
            default_message = str(err.get("message") or "")

            field_code_key = f"{field}.{code}"
            message = ERROR_MESSAGES.get(field_code_key, default_message)

            result.append(
                {
                    "field": field,
                    "message": message,
                    "code": code,
                }
            )

    return result


def assert_field_error(fields: list[FieldError], field: str, code: str) -> None:
    """Assert that a field error with the given code exists.

    Args:
        fields: List of field error dicts.
        field: Expected field name.
        code: Expected error code.
    """
    assert any(
        item["field"] == field and item["code"] == code for item in fields
    ), f"Expected error for field '{field}' with code '{code}' not found. Got: {fields}"


def raise_form_error(fields: list[FieldError]) -> None:
    """Raise a GraphQL validation error using centralized messages."""
    raise StrawberryGraphQLError(
        message=ERROR_MESSAGES["validation.error"],
        extensions={
            "code": "BAD_USER_INPUT",
            "fields": fields,
        },
    )
