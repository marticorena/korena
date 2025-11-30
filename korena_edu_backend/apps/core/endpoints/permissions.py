from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser

from rest_framework.permissions import BasePermission as DRFBasePermission
from rest_framework.request import Request
from strawberry.permission import BasePermission as GraphQLBasePermission
from strawberry.types import Info

from apps.core.endpoints.mixins import (
    AuthenticatedUserPermissionMixin,
    VerifiedUserPermissionMixin,
)

UserLike = AbstractBaseUser | AnonymousUser


class IsAuthenticatedRest(AuthenticatedUserPermissionMixin, DRFBasePermission):
    """REST permission: require authenticated user."""

    def has_permission(self, request: Request, view: Any) -> bool:
        return self._check_authenticated_user(request.user)


class IsVerifiedRest(VerifiedUserPermissionMixin, DRFBasePermission):
    """REST permission: require authenticated + verified user."""

    def has_permission(self, request: Request, view: Any) -> bool:
        return self._check_verified_user(request.user)


class IsAuthenticatedGraphql(
    AuthenticatedUserPermissionMixin,
    GraphQLBasePermission,
):
    """GraphQL permission: require authenticated user."""

    def has_permission(
        self,
        source: Any,
        info: Info,
        **kwargs: Any,
    ) -> bool:
        user = info.context.request.user
        return self._check_authenticated_user(user)


class IsVerifiedGraphql(
    VerifiedUserPermissionMixin,
    GraphQLBasePermission,
):
    """GraphQL permission: require authenticated + verified user."""

    def has_permission(
        self,
        source: Any,
        info: Info,
        **kwargs: Any,
    ) -> bool:
        user = info.context.request.user
        return self._check_verified_user(user)
