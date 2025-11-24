from django.core.validators import RegexValidator

from apps.core.messages import (
    EMAIL_VALIDATOR_ERROR,
    NAME_VALIDATOR_ERROR,
    PASSWORD_VALIDATOR_ERROR,
)

name_validator = RegexValidator(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,}$", NAME_VALIDATOR_ERROR)
email_validator = RegexValidator(r"^[\w\.\+-]+@[\w\.-]+\.\w+$", EMAIL_VALIDATOR_ERROR)
password_validator = RegexValidator(
    r"^(?=.*\d)(?=.*[!@#$%^&*()_+\-={}[\]:'\";<>?,./]).{8,}$",
    PASSWORD_VALIDATOR_ERROR,
)
