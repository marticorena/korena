from typing import Any, Dict, List

from apps.core.messages import ERROR_MESSAGES


def build_form_errors(form) -> List[Dict[str, Any]]:
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
