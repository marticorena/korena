from typing import Any

from apps.core.endpoints.utils import check_verified_user
from apps.core.messages import ERROR_MESSAGES


def _is_authenticated_user(user: Any | None) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


class AuthenticatedUserPermissionMixin:
    """Shared logic to require an authenticated user."""

    message = ERROR_MESSAGES["auth.not_authenticated"]

    def _check_authenticated_user(self, user: Any | None) -> bool:
        """Check if given user is authenticated.

        Args:
            user: User-like object (usually request.user) or None.

        Returns:
            True if user is authenticated, False otherwise.
        """
        if not _is_authenticated_user(user):
            self.message = ERROR_MESSAGES["auth.not_authenticated"]

            return False

        return True


class VerifiedUserPermissionMixin:
    """Shared logic to require an authenticated and verified user."""

    message = ERROR_MESSAGES["auth.not_verified"]

    def _check_verified_user(self, user: Any | None) -> bool:
        """Check if given user is authenticated and verified.

        Args:
            user: User-like object (usually request.user) or None.

        Returns:
            True if user is verified, False otherwise.
        """
        if not _is_authenticated_user(user):
            self.message = ERROR_MESSAGES["auth.not_authenticated"]

            return False

        is_valid, error_message = check_verified_user(user)

        if not is_valid:
            self.message = error_message or ERROR_MESSAGES["auth.not_verified"]

            return False

        return True
