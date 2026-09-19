from typing import Any

from apps.core.endpoints.utils import check_authenticated_user
from apps.core.messages import ERROR_MESSAGES


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
        if not check_authenticated_user(user):
            self.message = ERROR_MESSAGES["auth.not_authenticated"]

            return False

        return True
