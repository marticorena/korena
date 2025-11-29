from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

from apps.accounts.auth_utils import check_verified_user


class IsVerifiedUser(BasePermission):
    """Allow access only to authenticated and verified users."""

    message = "Tu cuenta debe estar verificada para realizar esta acción."

    def has_permission(self, request: Request, view: View) -> bool:
        """Check if the user is authenticated and verified.

        Args:
            request: Incoming HTTP request.
            view: DRF view.

        Returns:
            True if the user is allowed, False otherwise.
        """
        user = request.user
        is_valid, error_message = check_verified_user(user)

        if not is_valid:
            if error_message:
                self.message = error_message

            return False

        return True
