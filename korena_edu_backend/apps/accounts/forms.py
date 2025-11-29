from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.validators import email_validator, name_validator, password_validator

User = get_user_model()


class UserDataForm(forms.ModelForm):
    """Base form for user data validation."""

    def clean_first_name(self) -> str:
        """Validate first name field."""
        name = self.cleaned_data["first_name"]
        name_validator(name)  # produces code="invalid"
        return name

    def clean_last_name(self) -> str:
        """Validate last name field."""
        name = self.cleaned_data["last_name"]
        name_validator(name)  # produces code="invalid"
        return name


class RegisterForm(UserDataForm):
    """Form for user registration."""

    email = forms.CharField(required=True, validators=[email_validator])

    password1 = forms.CharField(required=False, validators=[password_validator])
    password2 = forms.CharField(required=False)

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
        email_validator(email)  # produces code="invalid"
        return email

    def clean(self) -> dict:
        """Validate the form as a whole."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        # Only validate if one was provided
        if p1 or p2:

            # Password mismatch
            if p1 != p2:
                # Attach with code so mapping can show the right translation:
                # FORM_FIELD_ERROR_MESSAGES["password2.password_mismatch"]
                self.add_error(
                    "password2",
                    forms.ValidationError(
                        message="",  # message irrelevant, mapping handles translation
                        code="password_mismatch",
                    ),
                )
                return cleaned_data

            # Validate password via validator (returns code="invalid")
            try:
                password_validator(p1)
            except forms.ValidationError as e:
                # keep the validator's own code ("invalid")
                self.add_error("password1", e)

        return cleaned_data


class UpdateUserForm(UserDataForm):
    """Form for updating user profile information."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
        ]

    def clean(self) -> dict:
        """Validate form."""
        cleaned_data = super().clean()
        return cleaned_data
