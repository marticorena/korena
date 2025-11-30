from typing import Callable

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class SimpleJWTAuthenticationMiddleware:
    """Attach authenticated user to request using SimpleJWT.

    This middleware allows non-DRF views (like Strawberry GraphQLView)
    to reuse the SimpleJWT authentication mechanism.
    """

    def __init__(self, get_response: Callable[..., HttpResponse]) -> None:
        """Initialize middleware with the next callable in the chain.

        Args:
            get_response: Next middleware or view callable.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Authenticate the request using SimpleJWT if an Authorization header exists.

        Args:
            request: Incoming HTTP request.

        Returns:
            HTTP response.
        """
        user = getattr(request, "user", None)
        is_anon = isinstance(user, AnonymousUser) or not getattr(
            user,
            "is_authenticated",
            False,
        )

        if is_anon:
            authenticator = JWTAuthentication()
            try:
                auth_result = authenticator.authenticate(request)
            except AuthenticationFailed:
                auth_result = None

            if auth_result is not None:
                auth_user, token = auth_result
                # Attach user and token so Strawberry permissions can use them.
                request.user = auth_user
                request.auth = token

        response = self.get_response(request)

        return response
