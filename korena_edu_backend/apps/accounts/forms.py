from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from apps.core.messages import (
    EMAIL_VALIDATOR_ERROR,
    NAME_VALIDATOR_ERROR,
    PASSWORD_VALIDATOR_ERROR,
    PASSWORDS_DONT_MATCH,
)

# Validators
name_validator = RegexValidator(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,}$", NAME_VALIDATOR_ERROR)
email_validator = RegexValidator(r"^[\w\.\+-]+@[\w\.-]+\.\w+$", EMAIL_VALIDATOR_ERROR)
password_validator = RegexValidator(
    r"^(?=.*\d)(?=.*[!@#$%^&*()_+\-={}[\]:'\";<>?,./]).{8,}$",
    PASSWORD_VALIDATOR_ERROR,
)

User = get_user_model()


class UserDataForm(forms.ModelForm):
    """Base form for user data validation."""

    def clean_first_name(self) -> str:
        """Validate first name field.

        Returns:
            str: The validated first name.
        """
        name = self.cleaned_data["first_name"]
        name_validator(name)

        return name

    def clean_last_name(self) -> str:
        """Validate last name field.

        Returns:
            str: The validated last name.
        """
        name = self.cleaned_data["last_name"]
        name_validator(name)

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
            "phone",
            "document_type",
            "document_number",
            "email",
        ]

    def clean_email(self) -> str:
        """Validate email field.

        Returns:
            str: The validated email.
        """
        email = self.cleaned_data["email"]
        email_validator(email)

        return email

    def clean(self) -> dict:
        """Validate the form as a whole.

        Returns:
            dict: The cleaned form data.

        Raises:
            ValidationError: If passwords don't match.
        """
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError(PASSWORDS_DONT_MATCH)
            password_validator(p1)

        return cleaned_data
