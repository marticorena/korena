"""
Centralized error and user-facing messages.

This module defines structured dictionaries for different error domains
and then exposes a single merged ERROR_MESSAGES mapping for global use.
"""

from typing import Dict

# Form field-specific messages: "field.code" → text
FORM_FIELD_ERROR_MESSAGES: Dict[str, str] = {
    "email.unique": "Este correo electrónico ya está registrado.",
    "email.invalid": "Correo inválido.",
    "password1.invalid": "Al menos 8 caracteres, con número y símbolo.",
    "password2.password_mismatch": "Las contraseñas no coinciden.",
    "first_name.invalid": "Nombre inválido.",
    "last_name.invalid": "Apellido inválido.",
}

# Generic form validator messages: "code" → text
FORM_CODE_ERROR_MESSAGES: Dict[str, str] = {
    "required": "Este campo es obligatorio.",
    "unique": "Este valor ya está en uso.",
    "invalid": "Formato inválido.",
    "max_length": "Valor demasiado largo.",
    "min_length": "Valor demasiado corto.",
}

# Authentication / account domain errors: "auth.code" → text
AUTH_ERROR_MESSAGES: Dict[str, str] = {
    "auth.invalid_credentials": "Credenciales inválidas.",
    "auth.not_authenticated": "No autenticado.",
    "auth.invalid_current_password": "La contraseña actual es incorrecta.",
    "auth.user_not_found": "Usuario no encontrado.",
    "auth.token_invalid": "Token inválido o expirado.",
    "auth.password_mismatch": "Las contraseñas no coinciden.",
}

# Upload / files domain errors: "upload.code" → text
UPLOAD_ERROR_MESSAGES: Dict[str, str] = {
    "upload.no_file": "El archivo no se recibió correctamente.",
    "upload.invalid_format": "Formato no permitido. Solo JPG, PNG o PDF.",
    "upload.file_too_large": "El archivo es demasiado grande. Máximo {max_size} MB.",
}

# Generic / shared messages: "domain.code" → text
GENERIC_ERROR_MESSAGES: Dict[str, str] = {
    "validation.error": "Errores de validación.",
}

# Single merged mapping for external use
ERROR_MESSAGES: Dict[str, str] = {
    **FORM_FIELD_ERROR_MESSAGES,
    **FORM_CODE_ERROR_MESSAGES,
    **AUTH_ERROR_MESSAGES,
    **UPLOAD_ERROR_MESSAGES,
    **GENERIC_ERROR_MESSAGES,
}
