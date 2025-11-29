from django.contrib.auth import get_user_model

import pytest

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_create_user_without_email_raises_value_error() -> None:
    """create_user should raise ValueError if email is missing."""

    with pytest.raises(ValueError, match="Users must have an email address."):
        User.objects.create_user(email="", password="P4ss-w0rd!")


def test_create_superuser_sets_required_flags() -> None:
    """create_superuser should set is_staff and is_superuser to True."""

    user = User.objects.create_superuser(
        email="admin@example.com",
        password="Admin-P4ss!",
    )

    assert user.is_staff is True
    assert user.is_superuser is True


def test_create_superuser_with_is_staff_false_raises_value_error() -> None:
    """create_superuser should fail if is_staff is not True."""

    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        User.objects.create_superuser(
            email="admin-no-staff@example.com",
            password="Admin-P4ss!",
            is_staff=False,
        )


def test_create_superuser_with_is_superuser_false_raises_value_error() -> None:
    """create_superuser should fail if is_superuser is not True."""

    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        User.objects.create_superuser(
            email="admin-no-super@example.com",
            password="Admin-P4ss!",
            is_superuser=False,
        )


def test_user_str_returns_email() -> None:
    """__str__ should return the user's email."""

    user = User.objects.create_user(
        email="str-user@example.com",
        password="P4ss-w0rd!",
        first_name="Str",
        last_name="User",
    )

    assert str(user) == user.email
