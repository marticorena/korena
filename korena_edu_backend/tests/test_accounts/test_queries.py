from types import SimpleNamespace
from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from tests.test_accounts.graphql_strings import ME_QUERY

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_me_requires_authentication(
    gql_client: Any,
    anon_context: SimpleNamespace,
) -> None:
    """The 'me' query should fail for anonymous contexts."""
    result = gql_client.execute_sync(
        ME_QUERY,
        variable_values={},
        context_value=anon_context,
    )

    assert result.errors is not None
    assert result.data is None


def test_me_requires_verified_user(
    gql_client: Any,
    non_verified_context: SimpleNamespace,
) -> None:
    """The 'me' query should fail if the user is not verified."""
    result = gql_client.execute_sync(
        ME_QUERY,
        variable_values={},
        context_value=non_verified_context,
    )

    assert result.errors is not None
    assert result.data is None


def test_me_returns_verified_user(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """The 'me' query should return the verified authenticated user."""
    result: Dict[str, Any] = exec_gql(
        ME_QUERY,
        context=verified_context,
    )

    data = result["data"]["me"]

    assert data is not None
    assert data["email"] == verified_user.email
    assert data["firstName"] == verified_user.first_name
    assert data["lastName"] == verified_user.last_name
    assert data["role"] == verified_user.role
    assert data["isVerified"] is True
