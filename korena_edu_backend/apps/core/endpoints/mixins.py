from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser

from apps.core.endpoints.utils import check_verified_user
from apps.core.messages import ERROR_MESSAGES

UserLike = AbstractBaseUser | AnonymousUser


class AuthenticatedUserPermissionMixin:
    """Shared logic to require an authenticated user."""

    message = ERROR_MESSAGES["auth.not_authenticated"]

    def _check_authenticated_user(self, user: UserLike | None) -> bool:
        """Check if given user is authenticated.

        Args:
            user: User instance or anonymous/None.

        Returns:
            True if user is authenticated, False otherwise.
        """
        is_authenticated = bool(
            user
            and not isinstance(user, AnonymousUser)
            and getattr(user, "is_authenticated", False),
        )

        if not is_authenticated:
            self.message = ERROR_MESSAGES["auth.not_authenticated"]

            return False

        return True


class VerifiedUserPermissionMixin:
    """Shared logic to require an authenticated and verified user."""

    message = ERROR_MESSAGES["auth.not_verified"]

    def _check_verified_user(self, user: UserLike | None) -> bool:
        """Check if given user is authenticated and verified.

        Args:
            user: User instance or anonymous/None.

        Returns:
            True if user is verified, False otherwise.
        """
        # First, ensure user is authenticated.
        is_authenticated = bool(
            user
            and not isinstance(user, AnonymousUser)
            and getattr(user, "is_authenticated", False),
        )

        if not is_authenticated:
            self.message = ERROR_MESSAGES["auth.not_authenticated"]

            return False

        # Then, delegate to your domain verification logic.
        is_valid, error_message = check_verified_user(user)

        if not is_valid:
            self.message = error_message or self.message

            return False

        return True
