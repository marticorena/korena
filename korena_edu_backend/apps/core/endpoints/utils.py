from typing import Any, Optional, Type

from rest_framework.response import Response

from apps.core.messages import ERROR_MESSAGES


def check_authenticated_user(user: Any) -> tuple[bool, str | None]:
    if user is None or getattr(user, "is_anonymous", True):

        return False, ERROR_MESSAGES["auth.not_authenticated"]

    return True, None


def check_verified_user(user: Any) -> tuple[bool, str | None]:
    is_auth, auth_error = check_authenticated_user(user)

    if not is_auth:
        return False, auth_error

    if not getattr(user, "is_verified", False):

        return False, ERROR_MESSAGES["auth.not_verified"]

    return True, None


KEY_CODE_MAP: dict[str, str] = {
    "auth.not_authenticated": "UNAUTHENTICATED",
    "auth.not_verified": "FORBIDDEN",
    "auth.invalid_credentials": "BAD_USER_INPUT",
    "auth.invalid_current_password": "BAD_USER_INPUT",
    "auth.user_not_found": "BAD_USER_INPUT",
    "auth.token_invalid": "BAD_USER_INPUT",
    "validation.error": "BAD_USER_INPUT",
}

EXCEPTION_CODE_MAP: dict[Type[BaseException], str] = {
    PermissionError: "FORBIDDEN",
    ValueError: "BAD_USER_INPUT",
}


def resolve_error_code(
    message: str,
    message_key: str | None = None,
    original_error: Optional[BaseException] = None,
    code: str | None = None,
) -> str:
    if code is not None:

        return code

    if message_key is not None:
        mapped_by_key = KEY_CODE_MAP.get(message_key)
        if mapped_by_key is not None:

            return mapped_by_key

    if original_error is not None:
        for exc_type, exc_code in EXCEPTION_CODE_MAP.items():
            if isinstance(original_error, exc_type):

                return exc_code

    return "INTERNAL_SERVER_ERROR"


def graphql_style_error_response(
    message: str,
    status_code: int,
    path: list[str] | None = None,
    code: str | None = None,
    message_key: str | None = None,
) -> Response:
    error_path = path or []
    resolved_code = resolve_error_code(
        message=message,
        message_key=message_key,
        original_error=None,
        code=code,
    )

    payload: dict[str, Any] = {
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
