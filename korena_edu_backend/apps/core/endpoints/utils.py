from typing import Any, Dict, List, Mapping, Optional, Tuple, Type

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


MESSAGE_CODE_MAP: Mapping[str, str] = {
    # Auth domain
    ERROR_MESSAGES["auth.not_authenticated"]: "UNAUTHENTICATED",
    ERROR_MESSAGES["auth.not_verified"]: "FORBIDDEN",
    ERROR_MESSAGES["auth.invalid_credentials"]: "BAD_USER_INPUT",
    ERROR_MESSAGES["auth.invalid_current_password"]: "BAD_USER_INPUT",
    ERROR_MESSAGES["auth.user_not_found"]: "BAD_USER_INPUT",
    ERROR_MESSAGES["auth.token_invalid"]: "BAD_USER_INPUT",
    # Generic validation
    ERROR_MESSAGES["validation.error"]: "BAD_USER_INPUT",
}

EXCEPTION_CODE_MAP: Mapping[Type[BaseException], str] = {
    PermissionError: "FORBIDDEN",
    ValueError: "BAD_USER_INPUT",
}


def resolve_error_code(
    message: str,
    original_error: Optional[BaseException] = None,
    code: Optional[str] = None,
) -> str:
    """Resolve an Apollo-compatible error code.

    Priority:
        1. Explicit code (if provided).
        2. Mapping by error message.
        3. Mapping by original exception type.
        4. "INTERNAL_SERVER_ERROR" as final fallback.

    Args:
        message: Error message to inspect.
        original_error: Original exception, if any.
        code: Explicit code that should win if present.

    Returns:
        str: Apollo-style error code.
    """
    if code is not None:
        return code

    mapped_by_message = MESSAGE_CODE_MAP.get(message)
    if mapped_by_message is not None:
        return mapped_by_message

    if original_error is not None:
        for exc_type, exc_code in EXCEPTION_CODE_MAP.items():
            if isinstance(original_error, exc_type):
                return exc_code

    return "INTERNAL_SERVER_ERROR"


def graphql_style_error_response(
    message: str,
    status_code: int,
    path: Optional[List[str]] = None,
    code: Optional[str] = None,
) -> Response:
    """Return an error payload that mimics GraphQL execution errors.

    This is intended for REST endpoints that must respond in a
    GraphQL-like structure so the frontend can treat them uniformly.

    Args:
        message: User-facing error message.
        status_code: HTTP status code for the response.
        path: Optional GraphQL path for the error.
        code: Optional Apollo-style error code override.

    Returns:
        Response: DRF Response with a GraphQL-like error payload.
    """
    error_path = path or []
    resolved_code = resolve_error_code(message=message, original_error=None, code=code)

    payload: Dict[str, Any] = {
        "data": None,
        "errors": [
            {
                "message": message,
                "locations": [],
                "path": error_path,
                "extensions": {
                    "code": resolved_code,
                },
            },
        ],
    }

    return Response(payload, status=status_code)
