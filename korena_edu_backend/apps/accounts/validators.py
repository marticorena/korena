from django.core.validators import RegexValidator

from apps.core.messages import ERROR_MESSAGES

# Name must have at least 2 letters and only allowed characters.
name_validator = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,}$",
    message=ERROR_MESSAGES["invalid"],  # fallback generic message
    code="invalid",
)


# Basic email format validator.
email_validator = RegexValidator(
    regex=r"^[\w\.\+-]+@[\w\.-]+\.\w+$",
    message=ERROR_MESSAGES["invalid"],  # fallback generic message
    code="invalid",
)


# Password must have at least 8 chars, one digit and one symbol.
password_validator = RegexValidator(
    regex=r"^(?=.*\d)(?=.*[!@#$%^&*()_+\-={}[\]:'\";<>?,./]).{8,}$",
    message=ERROR_MESSAGES["invalid"],  # fallback generic message
    code="invalid",
)
