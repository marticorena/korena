from typing import Callable

from django.http import HttpRequest, HttpResponse

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.core.endpoints.utils import check_authenticated_user


class SimpleJWTAuthenticationMiddleware:
    """Attach authenticated user to request using SimpleJWT.

    This middleware allows non-DRF views (like Strawberry GraphQLView)
    to reuse the SimpleJWT authentication mechanism.
    """

    def __init__(self, get_response: Callable[..., HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if auth_header and auth_header.startswith("Bearer "):
            is_auth, _ = check_authenticated_user(getattr(request, "user", None))

            if not is_auth:
                authenticator = JWTAuthentication()

                try:
                    auth_result = authenticator.authenticate(request)
                except AuthenticationFailed:
                    auth_result = None

                if auth_result is not None:
                    auth_user, token = auth_result
                    request.user = auth_user
                    request.auth = token

        response = self.get_response(request)

        return response
