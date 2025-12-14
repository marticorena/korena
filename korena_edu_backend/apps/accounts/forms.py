from typing import Any

from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.validators import email_validator, name_validator, password_validator

User = get_user_model()


class UserDataForm(forms.ModelForm):
    """Base form for user data validation."""

    def clean_first_name(self) -> str:
        """Validate first name field."""
        first_name = self.cleaned_data["first_name"]
        name_validator(first_name)

        return first_name

    def clean_last_name(self) -> str:
        """Validate last name field."""
        last_name = self.cleaned_data["last_name"]
        name_validator(last_name)

        return last_name


class ChangePasswordForm(forms.Form):
    """Form for changing user password."""

    password1 = forms.CharField(required=True, validators=[password_validator])
    password2 = forms.CharField(required=True)

    def clean(self) -> dict[str, Any]:
        """Validate new password fields."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if not p1 or not p2:
            return cleaned_data

        if p1 != p2:
            # Field-level mapping: password2.password_mismatch
            self.add_error(
                "password2",
                forms.ValidationError(
                    message="",
                    code="password_mismatch",
                ),
            )

            return cleaned_data

        return cleaned_data


class RegisterForm(ChangePasswordForm, UserDataForm):
    """Form for user registration."""

    email = forms.CharField(required=True, validators=[email_validator])

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class UpdateUserForm(UserDataForm):
    """Form for updating user profile information."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]
