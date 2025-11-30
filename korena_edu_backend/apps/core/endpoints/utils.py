from typing import Any, Dict, List, Tuple

from rest_framework.response import Response

from apps.core.messages import ERROR_MESSAGES


def check_authenticated_user(user: Any) -> Tuple[bool, str | None]:
    """Validate that a user is authenticated.

    Args:
        user: User-like object, typically request.user or info.context.request.user.

    Returns:
        Tuple[bool, str | None]: (is_valid, error_message).
    """
    if user is None or getattr(user, "is_anonymous", True):
        error_message = ERROR_MESSAGES["auth.not_authenticated"]

        return False, error_message

    return True, None


def check_verified_user(user: Any) -> Tuple[bool, str | None]:
    """Validate that a user is authenticated and verified.

    Args:
        user: User-like object, typically request.user or info.context.request.user.

    Returns:
        Tuple[bool, str | None]: (is_valid, error_message).
    """
    is_auth, auth_error = check_authenticated_user(user)

    if not is_auth:
        return False, auth_error

    if not getattr(user, "is_verified", False):
        error_message = ERROR_MESSAGES["auth.not_verified"]

        return False, error_message

    return True, None


def graphql_style_error_response(
    message: str,
    status_code: int,
    path: List[str] | None = None,
    code: str = "INTERNAL_SERVER_ERROR",
) -> Response:
    """Return an error payload that mimics GraphQL execution errors."""
    error_path = path or []
    payload: Dict[str, Any] = {
        "data": None,
        "errors": [
            {
                "message": message,
                "locations": [],
                "path": error_path,
                "extensions": {
                    "code": code,
                },
            },
        ],
    }

    return Response(payload, status=status_code)
