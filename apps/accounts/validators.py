from django.core.validators import RegexValidator

# Name must have at least 2 letters and only allowed characters.
name_validator = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,}$",
)

# Basic email format validator.
email_validator = RegexValidator(
    regex=r"^[\w\.\+-]+@[\w\.-]+\.\w+$",
)

# Password must have at least 8 chars, one digit and one symbol.
password_validator = RegexValidator(
    regex=r"^(?=.*\d)(?=.*[!@#$%^&*()_+\-={}[\]:'\";<>?,./]).{8,}$",
)
