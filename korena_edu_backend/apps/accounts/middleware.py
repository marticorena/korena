from typing import Any, Callable

from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class SimpleJWTAuthenticationMiddleware:
    """Attach authenticated user to request using SimpleJWT.

    This middleware allows non-DRF views (like GraphQLView) to reuse the
    SimpleJWT authentication mechanism.
    """

    def __init__(self, get_response: Callable[..., Any]) -> None:
        """Initialize middleware with the next callable in the chain.

        Args:
            get_response: Next middleware or view callable.
        """
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        """Authenticate the request using SimpleJWT if an Authorization header exists.

        Args:
            request: Incoming HTTP request.

        Returns:
            HTTP response.
        """
        if not hasattr(request, "user") or isinstance(request.user, AnonymousUser):
            authenticator = JWTAuthentication()
            try:
                auth_result = authenticator.authenticate(request)
            except AuthenticationFailed:
                auth_result = None

            if auth_result is not None:
                user, token = auth_result
                request.user = user
                request.auth = token

        response = self.get_response(request)

        return response
