"""Constants for error and user messages.

This module contains constants for error messages and user-facing messages
used throughout the application. Centralizing these messages makes it easier
to maintain consistency and support internationalization.
"""

FORM_FIELD_ERROR_MESSAGES = {
    "email.unique": "Este correo electrónico ya está registrado.",
    "email.invalid": "Correo inválido.",
    "password1.invalid": "La contraseña no cumple con los requisitos.",
    "password2.password_mismatch": "Las contraseñas no coinciden.",
    "first_name.invalid": "Nombre inválido.",
    "last_name.invalid": "Apellido inválido.",
}

FORM_CODE_ERROR_MESSAGES = {
    "required": "Este campo es obligatorio.",
    "unique": "Este valor ya está en uso.",
    "invalid": "Formato inválido.",
    "max_length": "Valor demasiado largo.",
    "min_length": "Valor demasiado corto.",
}


# File upload errors
FILE_UPLOAD_ERROR = "El archivo no se recibió correctamente."
FILE_FORMAT_ERROR = "Formato no permitido. Solo JPG, PNG o PDF."
FILE_SIZE_ERROR = "El archivo es demasiado grande. Máximo {max_size} MB."

# Authentication errors
INVALID_CREDENTIALS = "Credenciales inválidas."
NOT_AUTHENTICATED = "No autenticado"
EMAIL_ALREADY_REGISTERED = "Este correo electrónico ya está registrado."
DOCUMENT_ALREADY_REGISTERED = "Este número de documento ya está registrado."
PASSWORDS_DONT_MATCH = "Las contraseñas no coinciden."
CURRENT_PASSWORD_INCORRECT = "La contraseña actual es incorrecta."
USER_NOT_FOUND = "Usuario no encontrado."
VERIFICATION_TOKEN_INVALID_OR_EXPIRED = "Token inválido o expirado."

# Order errors
INSUFFICIENT_STOCK = "Stock insuficiente para el producto {product_name}."
INVALID_RECEIPT_TYPE = "Tipo de comprobante inválido."
ORDER_NOT_FOUND = "Pedido no encontrado."
NO_PERMISSION = "No tienes permiso para ver este pedido."

# Address errors
ADDRESS_NOT_FOUND = "Dirección no encontrada."
DISTRICT_NOT_VALID = "Distrito no válido."

# Validator errors
VALIDATION_ERROR = "Errores de validación."
NAME_VALIDATOR_ERROR = "Debe tener al menos 2 letras."
EMAIL_VALIDATOR_ERROR = "Correo inválido."
PASSWORD_VALIDATOR_ERROR = "Al menos 8 caracteres, con número y símbolo."
PHONE_VALIDATOR_ERROR = "Ej: 987654321 o +51987654321"
DOCUMENT_VALIDATOR_ERROR = "Exactamente 8 dígitos."
ADDRESS_VALIDATOR_ERROR = "Al menos 5 caracteres."

# Success messages
EMAIL_VERIFIED = "Email verificado correctamente."
PASSWORD_UPDATED = "Contraseña actualizada correctamente."
USER_DATA_UPDATED = "Datos actualizados correctamente."
ADDRESS_ADDED = "Dirección agregada correctamente."
ADDRESS_UPDATED = "Dirección actualizada."
ADDRESS_DELETED = "Dirección eliminada."
DEFAULT_ADDRESS_UPDATED = "Dirección predeterminada actualizada."
