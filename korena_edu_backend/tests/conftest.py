from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client as DjangoClient

from graphene.test import Client as GrapheneClient
import pytest

from config.schema import schema

User = get_user_model()


@pytest.fixture
def gql_client() -> GrapheneClient:
    """Return a Graphene test client bound to the project schema.

    Returns:
        GrapheneClient: Graphene test client.
    """
    client = GrapheneClient(schema)

    return client


@pytest.fixture
def non_verified_user(db) -> User:
    """Create and return a regular, inactive-but-usable user.

    Args:
        db: Django database fixture.

    Returns:
        User: A user instance.
    """
    u = User.objects.create_user(
        email="non-verified@example.com",
        password="P4ss-w0rd!",
        first_name="Non",
        last_name="Verified",
    )

    return u


@pytest.fixture
def verified_user(db) -> User:
    """Create and return a verified/active user for login_required flows.

    Args:
        db: Django database fixture.

    Returns:
        User: A verified/active user instance.
    """
    u = User.objects.create_user(
        email="verified@example.com",
        password="P4ss-w0rd!",
        first_name="Yes",
        last_name="Verified",
    )
    u.is_active = True
    u.is_verified = True
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


@pytest.fixture
def anon_context() -> SimpleNamespace:
    """Return a GraphQL context with an anonymous user.

    Returns:
        SimpleNamespace: Context with AnonymousUser.
    """
    ctx = SimpleNamespace(user=AnonymousUser())

    return ctx


@pytest.fixture
def non_verified_context(non_verified_user: User) -> SimpleNamespace:
    """Return a GraphQL context with an authenticated user.

    Args:
        user: A Django user.

    Returns:
        SimpleNamespace: Context with the provided user.
    """
    ctx = SimpleNamespace(user=non_verified_user)

    return ctx


@pytest.fixture
def verified_context(verified_user: User) -> SimpleNamespace:
    """Return a GraphQL context with an authenticated, verified user.

    Args:
        verified_user: A verified Django user.

    Returns:
        SimpleNamespace: Context with the verified user.
    """
    ctx = SimpleNamespace(user=verified_user)

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
    gql_client: GrapheneClient,
) -> Callable[[str, Optional[Dict[str, Any]], Optional[Any]], Dict[str, Any]]:
    """Return a helper to execute GraphQL with variables and context.

    Args:
        gql_client: The Graphene client.

    Returns:
        Callable: Function(query: str, variables: dict | None, context: Any | None) -> dict.
    """

    def _exec(
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL operation via Graphene test client.

        Args:
            query: GraphQL query or mutation string.
            variables: Optional variables map.
            context: Optional context; if None, an anonymous context is used.

        Returns:
            Dict[str, Any]: Execution result as a dict with "data" and optional "errors".
        """
        if context is None:
            context = SimpleNamespace(user=AnonymousUser())

        result = gql_client.execute(
            query,
            variables=variables or {},
            context_value=context,
        )

        if result and result.get("errors"):
            messages = [getattr(e, "message", str(e)) for e in result["errors"]]

            raise AssertionError(f"GraphQL errors: {messages}")

        return result

    return _exec
