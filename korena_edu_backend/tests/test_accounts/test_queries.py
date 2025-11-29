from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from tests.test_accounts.graphql_strings import ME_QUERY

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_me_returns_none_for_anonymous(exec_gql) -> None:
    """The 'me' query should return null for anonymous users."""
    result: Dict[str, Any] = exec_gql(ME_QUERY)

    assert result["data"]["me"] is None


def test_me_returns_user_for_authenticated(
    exec_gql,
    non_verified_context,
    non_verified_user: User,
) -> None:
    """The 'me' query should return the authenticated user."""
    result: Dict[str, Any] = exec_gql(
        ME_QUERY,
        context=non_verified_context,
    )

    data = result["data"]["me"]
    assert data is not None
    assert data["email"] == non_verified_user.email
    assert data["firstName"] == non_verified_user.first_name
    assert data["lastName"] == non_verified_user.last_name
    assert data["role"] == non_verified_user.role


def test_me_returns_verified_user(
    exec_gql,
    verified_context,
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
