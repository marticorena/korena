from types import SimpleNamespace
from typing import Any

from django.contrib.auth import get_user_model

import pytest

from apps.core.graphql.utils import assert_field_error
from apps.core.messages import ERROR_MESSAGES
from tests.test_accounts.graphql_strings import (
    CHANGE_PASSWORD_MUTATION,
    DELETE_ACCOUNT_MUTATION,
    UPDATE_USER_MUTATION,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_update_user_changes_first_and_last_name_for_verified_user(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """updateUser should modify basic profile fields for a verified user."""
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
    gql_client: Any,
    anon_context: SimpleNamespace,
) -> None:
    """updateUser should fail for anonymous contexts."""
    variables = {
        "firstName": "Anyone",
        "lastName": "Anonymous",
    }

    result = gql_client.execute_sync(
        UPDATE_USER_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None

    assert result.data is None


def test_update_user_requires_verified_user(
    gql_client: Any,
    non_verified_context: SimpleNamespace,
) -> None:
    """updateUser should fail if the user is not verified."""
    variables = {
        "firstName": "New",
        "lastName": "Name",
    }

    result = gql_client.execute_sync(
        UPDATE_USER_MUTATION,
        variable_values=variables,
        context_value=non_verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]

    assert result.data is None


def test_update_user_invalid_data_returns_errors_for_verified_user(
    gql_client: Any,
    verified_context: SimpleNamespace,
) -> None:
    """updateUser should return validation info when payload is invalid."""
    variables = {
        "firstName": "1",
        "lastName": "2",
    }

    result = gql_client.execute_sync(
        UPDATE_USER_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["validation.error"]

    fields = error.extensions["fields"]

    assert_field_error(fields, "first_name", "invalid")
    assert_field_error(fields, "last_name", "invalid")


def test_change_password_updates_password_when_data_is_valid(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """changePassword should update the password when data is valid."""
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
    gql_client: Any,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """changePassword should fail when the current password is incorrect."""
    variables = {
        "currentPassword": "Wrong-Password",
        "password1": "Another-P4ss!",
        "password2": "Another-P4ss!",
    }

    result = gql_client.execute_sync(
        CHANGE_PASSWORD_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.invalid_current_password"]

    assert result.data is None

    verified_user.refresh_from_db()

    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_invalid_new_password_returns_errors(
    gql_client: Any,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """changePassword should return validation info for invalid new password."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "short",
        "password2": "different",
    }

    result = gql_client.execute_sync(
        CHANGE_PASSWORD_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["validation.error"]

    fields = error.extensions["fields"]

    assert_field_error(fields, "password1", "invalid")

    verified_user.refresh_from_db()

    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_password_mismatch_returns_errors(
    gql_client: Any,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """changePassword should return validation info when passwords differ."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!!!",
    }

    result = gql_client.execute_sync(
        CHANGE_PASSWORD_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["validation.error"]

    fields = error.extensions["fields"]

    assert_field_error(fields, "password2", "password_mismatch")

    verified_user.refresh_from_db()

    assert verified_user.check_password("P4ss-w0rd!") is True


def test_change_password_requires_authentication(
    gql_client: Any,
    anon_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """changePassword should fail for anonymous contexts."""
    variables = {
        "currentPassword": "P4ss-w0rd!",
        "password1": "N3w-P4ssword!",
        "password2": "N3w-P4ssword!",
    }

    result = gql_client.execute_sync(
        CHANGE_PASSWORD_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None

    assert result.data is None

    verified_user.refresh_from_db()

    assert verified_user.check_password("P4ss-w0rd!") is True


def test_delete_account_removes_user_when_password_is_correct(
    exec_gql,
    verified_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """deleteAccount should remove the user when password is correct."""
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
    gql_client: Any,
    verified_context: SimpleNamespace,
    non_verified_user: User,
) -> None:
    """deleteAccount should surface an error when password is incorrect."""
    user_id = non_verified_user.id
    variables = {
        "currentPassword": "Wrong-Password",
    }

    result = gql_client.execute_sync(
        DELETE_ACCOUNT_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.invalid_current_password"]

    assert result.data is None

    assert User.objects.filter(id=user_id).exists()


def test_delete_account_requires_authentication(
    gql_client: Any,
    anon_context: SimpleNamespace,
    verified_user: User,
) -> None:
    """deleteAccount should fail for anonymous contexts."""
    user_id = verified_user.id
    variables = {
        "currentPassword": "P4ss-w0rd!",
    }

    result = gql_client.execute_sync(
        DELETE_ACCOUNT_MUTATION,
        variable_values=variables,
        context_value=anon_context,
    )

    assert result.errors is not None

    assert result.data is None

    assert User.objects.filter(id=user_id).exists()
