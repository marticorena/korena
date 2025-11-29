from strawberry.permission import BasePermission
from strawberry.types import Info

from apps.accounts.auth_utils import (
    check_authenticated_user,
    check_verified_user,
)
from apps.core.messages import ERROR_MESSAGES


class IsAuthenticated(BasePermission):
    """Require user to be authenticated."""

    message = ERROR_MESSAGES["auth.not_authenticated"]

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        """Check if user is authenticated."""
        user = info.context.request.user
        is_valid, error_message = check_authenticated_user(user)

        if not is_valid:
            self.message = error_message or self.message

            return False

        return True


class IsVerified(BasePermission):
    """Require user to be authenticated AND verified."""

    message = ERROR_MESSAGES["auth.not_verified"]

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        """Check if user is authenticated and verified."""
        user = info.context.request.user
        is_valid, error_message = check_verified_user(user)

        if not is_valid:
            self.message = error_message or self.message

            return False

        return True
