from types import SimpleNamespace
from typing import Any

from django.contrib.auth import get_user_model

import pytest
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.utils import verify_token
from apps.core.graphql.utils import assert_field_error
from apps.core.messages import ERROR_MESSAGES
from apps.notifications.models import EmailLog
from tests.test_accounts.graphql_strings import (
    LOGIN_USER_MUTATION,
    REFRESH_TOKEN_MUTATION,
    REGISTER_USER_MUTATION,
    VERIFY_EMAIL_MUTATION,
    VERIFY_TOKEN_MUTATION,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_login_user_returns_tokens_for_valid_credentials(
    exec_gql,
    verified_user: User,
) -> None:
    """loginUser should return access and refresh tokens for valid credentials."""
    variables = {
        "email": verified_user.email,
        "password": "P4ss-w0rd!",
    }

    result = exec_gql(LOGIN_USER_MUTATION, variables=variables)

    data = result["data"]["loginUser"]

    assert isinstance(data["access"], str) and data["access"]

    assert isinstance(data["refresh"], str) and data["refresh"]


def test_login_user_raises_error_for_invalid_credentials(
    gql_client: Any,
    anon_context: SimpleNamespace,
) -> None:
    """loginUser should surface an error when credentials are invalid."""
    variables = {
        "email": "unknown@example.com",
        "password": "wrong-password",
    }

    result = gql_client.execute_sync(
        LOGIN_USER_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None
    message = result.errors[0].message

    assert message == ERROR_MESSAGES["auth.invalid_credentials"]

    assert result.data is None


def test_login_user_raises_error_for_unverified_user(
    gql_client: Any,
    anon_context: SimpleNamespace,
    non_verified_user: User,
) -> None:
    """loginUser should fail if the user is not verified."""
    variables = {
        "email": non_verified_user.email,
        "password": "P4ss-w0rd!",
    }

    result = gql_client.execute_sync(
        LOGIN_USER_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]

    assert result.data is None


@pytest.mark.django_db
def test_refresh_token_returns_new_access(exec_gql, verified_user):
    """refreshToken should issue a new access token."""
    refresh = str(RefreshToken.for_user(verified_user))

    result = exec_gql(
        REFRESH_TOKEN_MUTATION,
        variables={"refresh": refresh},
    )

    data = result["data"]["refreshToken"]

    assert "access" in data
    assert data["refresh"] == refresh
    assert isinstance(data["access"], str)
    assert len(data["access"]) > 10


@pytest.mark.django_db
def test_refresh_token_invalid_returns_error(gql_client, anon_context):
    """refreshToken should fail for invalid refresh token."""
    result = gql_client.execute_sync(
        REFRESH_TOKEN_MUTATION,
        variable_values={"refresh": "invalid-refresh-token"},
        context_value=anon_context,
    )

    assert result.errors is not None
    assert result.errors[0].message == ERROR_MESSAGES["auth.token_invalid"]
    assert result.data is None


@pytest.mark.django_db
def test_verify_token_valid_returns_true(exec_gql, verified_user):
    """verifyToken should return True for a valid access token."""
    token = str(AccessToken.for_user(verified_user))

    result = exec_gql(
        VERIFY_TOKEN_MUTATION,
        variables={"token": token},
    )

    assert result["data"]["verifyToken"] is True


@pytest.mark.django_db
def test_verify_token_invalid_returns_error(gql_client, anon_context):
    """verifyToken should fail for invalid/expired tokens."""
    result = gql_client.execute_sync(
        VERIFY_TOKEN_MUTATION,
        variable_values={"token": "invalid-token"},
        context_value=anon_context,
    )

    assert result.errors is not None
    assert result.errors[0].message == ERROR_MESSAGES["auth.token_invalid"]
    assert result.data is None


def test_register_user_creates_inactive_user_and_returns_token(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """registerUser should create a new inactive user, log email and return a token."""
    sent = SimpleNamespace(called=False, email_id=None)

    # Fake only the Celery async dispatch, not the email generation.
    def fake_delay(email_log_id: int) -> None:
        sent.called = True
        sent.email_id = email_log_id

    monkeypatch.setattr(
        "apps.accounts.graphql.mutations.send_email_task.delay",
        fake_delay,
    )

    email = "new.user@example.com"
    variables = {
        "email": email,
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!",
        "firstName": "New",
        "lastName": "User",
    }

    result = exec_gql(REGISTER_USER_MUTATION, variables=variables)

    data = result["data"]["registerUser"]
    token = data["token"]

    # Token should be a non-empty string and decodable to the user's email.
    assert isinstance(token, str) and token

    decoded_email = verify_token(token)

    assert decoded_email == email

    user = User.objects.get(email=email)
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.is_active is False
    assert user.is_verified is False

    # Celery task should have been scheduled once with a valid EmailLog id.
    assert sent.called is True
    assert sent.email_id is not None

    email_log = EmailLog.objects.get(pk=sent.email_id)

    assert email_log.user == user
    assert email_log.to_email == email


def test_register_user_invalid_data_returns_field_errors(
    gql_client: Any,
    anon_context: SimpleNamespace,
) -> None:
    """registerUser should return validation details for invalid payload."""
    variables = {
        "email": "invalid-email",
        "password1": "short",
        "password2": "different",
        "firstName": "N",
        "lastName": "1nvalid",
    }

    result = gql_client.execute_sync(
        REGISTER_USER_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["validation.error"]

    fields = error.extensions["fields"]

    assert_field_error(fields, "first_name", "invalid")
    assert_field_error(fields, "last_name", "invalid")
    assert_field_error(fields, "email", "invalid")
    assert_field_error(fields, "password1", "invalid")

    assert User.objects.count() == 0


def test_verify_email_activates_user_and_marks_verified(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifyEmail should activate the account when token is valid."""
    user = User.objects.create_user(
        email="pending@example.com",
        password="P4ss-w0rd!",
        first_name="Pending",
        last_name="User",
        is_active=False,
    )

    assert user.is_active is False
    assert user.is_verified is False

    def fake_verify_token(token: str, max_age: int = 60 * 60 * 24) -> str:
        return user.email

    monkeypatch.setattr(
        "apps.accounts.graphql.mutations.verify_token",
        fake_verify_token,
    )

    variables = {
        "token": "any-token-value",
    }

    result = exec_gql(VERIFY_EMAIL_MUTATION, variables=variables)

    data = result["data"]["verifyEmail"]

    assert data["email"] == user.email

    user.refresh_from_db()

    assert user.is_active is True
    assert user.is_verified is True


def test_verify_email_invalid_token_returns_error(
    gql_client: Any,
    anon_context: SimpleNamespace,
) -> None:
    """verifyEmail should surface an error when token is invalid."""
    variables = {
        "token": "invalid-token",
    }

    result = gql_client.execute_sync(
        VERIFY_EMAIL_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.token_invalid"]

    assert result.data is None
