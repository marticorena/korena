from typing import Any

from rest_framework.permissions import BasePermission as DRFBasePermission
from rest_framework.request import Request
from strawberry.permission import BasePermission as GraphQLBasePermission
from strawberry.types import Info

from apps.core.endpoints.mixins import (
    AuthenticatedUserPermissionMixin,
)


def _get_graphql_user(info: Info) -> Any:
    # Strawberry context usually provides Django request in info.context.request
    return info.context.request.user


class IsAuthenticatedRest(AuthenticatedUserPermissionMixin, DRFBasePermission):
    """REST permission: require authenticated user."""

    def has_permission(self, request: Request, view: Any) -> bool:
        return self._check_authenticated_user(request.user)


class IsAuthenticatedGraphql(AuthenticatedUserPermissionMixin, GraphQLBasePermission):
    """GraphQL permission: require authenticated user."""

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return self._check_authenticated_user(_get_graphql_user(info))
