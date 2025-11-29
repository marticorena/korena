# apps/accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.validators import email_validator, name_validator, password_validator

User = get_user_model()


class UserDataForm(forms.ModelForm):
    """Base form for user data validation."""

    def clean_first_name(self) -> str:
        """Validate first name field."""
        name = self.cleaned_data["first_name"]
        name_validator(name)

        return name

    def clean_last_name(self) -> str:
        """Validate last name field."""
        name = self.cleaned_data["last_name"]
        name_validator(name)

        return name


class ChangePasswordForm(forms.Form):
    """Form for changing user password."""

    password1 = forms.CharField(required=True, validators=[password_validator])
    password2 = forms.CharField(required=True)

    def clean(self) -> dict:
        """Validate new password fields."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2:
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

            try:
                password_validator(p1)
            except forms.ValidationError as e:
                # Keep validator code (e.code, usually 'invalid') so mapping works (password1.invalid)
                self.add_error("password1", e)

        return cleaned_data


class RegisterForm(ChangePasswordForm, UserDataForm):
    """Form for user registration."""

    email = forms.CharField(required=True, validators=[email_validator])

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def clean_email(self) -> str:
        """Validate email field."""
        email = self.cleaned_data["email"]
        email_validator(email)

        return email


class UpdateUserForm(UserDataForm):
    """Form for updating user profile information."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
        ]

    def clean(self) -> dict:
        """Validate the form as a whole."""
        cleaned_data = super().clean()

        return cleaned_data
