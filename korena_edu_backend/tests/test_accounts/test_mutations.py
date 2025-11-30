from types import SimpleNamespace
from typing import Any, Dict

from django.contrib.auth import get_user_model

from graphene.test import Client as GrapheneClient
import pytest

from apps.accounts.utils import verify_token
from apps.core.messages import ERROR_MESSAGES
from apps.core.schema.utils import assert_field_error
from apps.notifications.models import EmailLog
from tests.test_accounts.graphql_strings import (
    CHANGE_PASSWORD_MUTATION,
    DELETE_ACCOUNT_MUTATION,
    GET_TOKEN_MUTATION,
    REGISTER_USER_MUTATION,
    UPDATE_USER_MUTATION,
    VERIFY_EMAIL_MUTATION,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_get_token_returns_tokens_for_valid_credentials(
    exec_gql,
    verified_user: User,
) -> None:
    """GetToken should return token and refreshToken for valid credentials."""
    variables = {
        "email": verified_user.email,
        "password": "P4ss-w0rd!",
    }

    result = exec_gql(GET_TOKEN_MUTATION, variables=variables)

    data = result["data"]["getToken"]
    assert isinstance(data["token"], str) and data["token"]

    assert isinstance(data["refreshToken"], str) and data["refreshToken"]


def test_get_token_raises_error_for_invalid_credentials(
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
) -> None:
    """GetToken should raise a GraphQL error when credentials are invalid."""
    variables = {
        "email": "unknown@example.com",
        "password": "wrong-password",
    }

    result: Dict[str, Any] = gql_client.execute(
        GET_TOKEN_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    message = result["errors"][0]["message"]
    assert message == ERROR_MESSAGES["auth.invalid_credentials"]

    assert result["data"]["getToken"] is None


def test_get_token_raises_error_for_unverified_user(
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
    non_verified_user: User,
) -> None:
    """GetToken should raise an error if user is not verified."""
    variables = {
        "email": non_verified_user.email,
        "password": "P4ss-w0rd!",
    }

    result: Dict[str, Any] = gql_client.execute(
        GET_TOKEN_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]

    assert result["data"]["getToken"] is None


def test_register_user_creates_inactive_user_and_returns_token(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RegisterUser should create a new user, persist EmailLog and return a valid token."""
    sent = SimpleNamespace(called=False, email_id=None)

    # Fake only the Celery async dispatch, not the email generation.
    def fake_delay(email_log_id: int) -> None:
        sent.called = True
        sent.email_id = email_log_id

    monkeypatch.setattr(
        "apps.accounts.schema.mutations.send_email_task.delay",
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
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
) -> None:
    """RegisterUser should return validation errors for invalid payload."""
    variables = {
        "email": "invalid-email",
        "password1": "short",
        "password2": "different",
        "firstName": "N",
        "lastName": "1nvalid",
    }

    result: Dict[str, Any] = gql_client.execute(
        REGISTER_USER_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["validation.error"]

    fields = error["extensions"]["fields"]

    assert_field_error(fields, "first_name", "invalid")
    assert_field_error(fields, "last_name", "invalid")
    assert_field_error(fields, "email", "invalid")
    assert_field_error(fields, "password1", "invalid")

    assert User.objects.count() == 0


def test_verify_email_activates_user_and_marks_verified(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VerifyEmail should activate user and mark as verified when token is valid."""
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
        "apps.accounts.schema.mutations.verify_token",
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
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
) -> None:
    """VerifyEmail should return an error when token is invalid."""
    variables = {
        "token": "invalid-token",
    }

    result: Dict[str, Any] = gql_client.execute(
        VERIFY_EMAIL_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.token_invalid"]
    assert result["data"]["verifyEmail"] is None


def test_update_user_changes_first_and_last_name_for_verified_user(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """UpdateUser should modify the verified user's name fields."""
    variables = {
        "firstName": "Updated",
        "lastName": "Name",
    }

    result = exec_gql(
        UPDATE_USER_MUTATION,
        variables=variables,
        context=verified_context,
    )

    data = result["data"]["updateUser"]
    assert data["email"] == verified_user.email

    verified_user.refresh_from_db()
    assert verified_user.first_name == "Updated"
    assert verified_user.last_name == "Name"


def test_update_user_requires_authentication(
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
) -> None:
    """UpdateUser should fail for anonymous context."""
    variables = {
        "firstName": "Anyone",
        "lastName": "Anonymous",
    }

    result: Dict[str, Any] = gql_client.execute(
        UPDATE_USER_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    assert result["data"]["updateUser"] is None


def test_update_user_requires_verified_user(
    gql_client: GrapheneClient,
    non_verified_context: SimpleNamespace,
) -> None:
    """UpdateUser should fail if user is authenticated but not verified."""
    variables = {
        "firstName": "New",
        "lastName": "Name",
    }

    result: Dict[str, Any] = gql_client.execute(
        UPDATE_USER_MUTATION,
        variables=variables,
        context_value=non_verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]
    assert result["data"]["updateUser"] is None


def test_update_user_invalid_data_returns_errors_for_verified_user(
    gql_client: GrapheneClient,
    verified_context: SimpleNamespace,
) -> None:
    """UpdateUser should return validation errors when payload is invalid for verified user."""
    variables = {
        "firstName": "1",
        "lastName": "2",
    }

    result: Dict[str, Any] = gql_client.execute(
        UPDATE_USER_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["validation.error"]

    fields = error["extensions"]["fields"]

    assert_field_error(fields, "first_name", "invalid")
    assert_field_error(fields, "last_name", "invalid")


def test_change_password_updates_password_when_data_is_valid(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """ChangePassword should update user password when data is valid."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!",
    }

    result = exec_gql(
        CHANGE_PASSWORD_MUTATION,
        variables=variables,
        context=verified_context,
    )

    data = result["data"]["changePassword"]
    assert data["email"] == verified_user.email

    verified_user.refresh_from_db()
    assert verified_user.check_password("N3w-P4ssword!") is True


def test_change_password_fails_when_current_password_is_wrong(
    gql_client: GrapheneClient,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """ChangePassword should fail when current password is incorrect."""
    variables = {
        "currentPassword": "Wrong-Password",
        "password1": "Another-P4ss!",
        "password2": "Another-P4ss!",
    }

    result: Dict[str, Any] = gql_client.execute(
        CHANGE_PASSWORD_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.invalid_current_password"]
    assert result["data"]["changePassword"] is None

    verified_user.refresh_from_db()
    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_invalid_new_password_returns_errors(
    gql_client: GrapheneClient,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """ChangePassword should return validation errors for invalid new password."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "short",
        "password2": "different",
    }

    result: Dict[str, Any] = gql_client.execute(
        CHANGE_PASSWORD_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["validation.error"]

    fields = error["extensions"]["fields"]

    assert_field_error(fields, "password1", "invalid")

    verified_user.refresh_from_db()
    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_password_mismatch_returns_errors(
    gql_client: GrapheneClient,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """ChangePassword should return validation errors for invalid new password."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!!!",
    }

    result: Dict[str, Any] = gql_client.execute(
        CHANGE_PASSWORD_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["validation.error"]

    fields = error["extensions"]["fields"]

    assert_field_error(fields, "password2", "password_mismatch")

    verified_user.refresh_from_db()
    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_requires_authentication(
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """ChangePassword should fail for anonymous context."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!",
    }

    result: Dict[str, Any] = gql_client.execute(
        CHANGE_PASSWORD_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    assert result["data"]["changePassword"] is None

    verified_user.refresh_from_db()
    assert verified_user.check_password("P4ss-w0rd!") is True


def test_delete_account_removes_user_when_password_is_correct(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """DeleteAccount should remove the authenticated user when password is correct."""
    user_id = verified_user.id
    variables = {
        "currentPassword": "P4ss-w0rd!",
    }

    result = exec_gql(
        DELETE_ACCOUNT_MUTATION,
        variables=variables,
        context=verified_context,
    )

    data = result["data"]["deleteAccount"]
    assert data["email"] == verified_user.email

    assert not User.objects.filter(id=user_id).exists()


def test_delete_account_fails_with_wrong_password(
    gql_client: GrapheneClient,
    verified_context: SimpleNamespace,
    non_verified_user: User,
) -> None:
    """DeleteAccount should return an error when password is incorrect."""
    user_id = non_verified_user.id
    variables = {
        "currentPassword": "Wrong-Password",
    }

    result: Dict[str, Any] = gql_client.execute(
        DELETE_ACCOUNT_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.invalid_current_password"]
    assert result["data"]["deleteAccount"] is None

    assert User.objects.filter(id=user_id).exists()


def test_delete_account_requires_authentication(
    gql_client: GrapheneClient,
    anon_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """DeleteAccount should fail for anonymous context."""
    user_id = verified_user.id
    variables = {
        "currentPassword": "P4ss-w0rd!",
    }

    result: Dict[str, Any] = gql_client.execute(
        DELETE_ACCOUNT_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    assert result["data"]["deleteAccount"] is None

    assert User.objects.filter(id=user_id).exists()
