from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client as DjangoClient

import pytest

from config.schema import schema

User = get_user_model()


@pytest.fixture
def gql_client() -> Any:
    """Return the project GraphQL schema for direct execution.

    Returns:
        Any: Strawberry schema instance.
    """

    return schema


@pytest.fixture
def active_user(db) -> User:
    """Create and return an active user for login_required flows.

    Args:
        db: Django database fixture.

    Returns:
        User: An active user instance.
    """
    u = User.objects.create_user(
        email="active@example.com",
        password="P4ss-w0rd!",
        first_name="Yes",
        last_name="Active",
    )
    u.is_active = True
    u.save()

    return u


@pytest.fixture
def superuser(db) -> User:
    """Create and return a superuser for admin flows.

    Args:
        db: Django database fixture.

    Returns:
        User: A superuser instance.
    """
    u = User.objects.create_superuser(
        email="admin@example.com",
        password="Admin#12345",
        first_name="Admin",
        last_name="User",
    )

    return u


def _make_request_context(user: Any) -> SimpleNamespace:
    """Build a Strawberry-like context with request.user.

    This matches the shape expected by permissions that
    access `info.context.request.user`.

    Args:
        user: User or AnonymousUser instance.

    Returns:
        SimpleNamespace: Context with `request.user`.
    """

    return SimpleNamespace(request=SimpleNamespace(user=user))


@pytest.fixture
def anon_context() -> SimpleNamespace:
    """Return a GraphQL context with an anonymous user.

    Returns:
        SimpleNamespace: Context with AnonymousUser under request.user.
    """
    ctx = _make_request_context(AnonymousUser())

    return ctx


@pytest.fixture
def active_context(active_user: User) -> SimpleNamespace:
    """Return a GraphQL context with an authenticated, active user.

    Args:
        active_user: An active Django user instance.

    Returns:
        SimpleNamespace: Context with the active user under request.user.
    """
    ctx = _make_request_context(active_user)

    return ctx


@pytest.fixture
def admin_client_logged(client: DjangoClient, superuser: User) -> DjangoClient:
    """Return a Django test client authenticated as superuser.

    Args:
        client: Django test client.
        superuser: Superuser instance.

    Returns:
        DjangoClient: Authenticated client.
    """
    client.force_login(superuser)

    return client


@pytest.fixture
def exec_gql(
    gql_client: Any,
) -> Callable[[str, Optional[Dict[str, Any]], Optional[Any]], Dict[str, Any]]:
    """Return a helper to execute GraphQL with variables and context.

    This uses the Strawberry schema's `execute_sync` method.

    Args:
        gql_client: The Strawberry schema instance.

    Returns:
        Callable: Function(query: str, variables: dict | None, context: Any | None) -> dict.
    """

    def _exec(
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL operation via the Strawberry schema.

        Args:
            query: GraphQL query or mutation string.
            variables: Optional variables map.
            context: Optional context; if None, an anonymous context is used.

        Returns:
            Dict[str, Any]: Execution result as a dict with "data" and no "errors".
        """
        if context is None:
            context = _make_request_context(AnonymousUser())

        result = gql_client.execute_sync(
            query,
            variable_values=variables or {},
            context_value=context,
        )

        if result.errors:
            messages = [getattr(e, "message", str(e)) for e in result.errors]

            raise AssertionError(f"GraphQL errors: {messages}")

        # Normalize to dict for backwards-compatible usage in tests.
        data: Dict[str, Any] = {
            "data": result.data,
        }

        return data

    return _exec
