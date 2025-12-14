"""
Centralized error and user-facing messages.

This module defines structured dictionaries for different error domains
and then exposes a single merged ERROR_MESSAGES mapping for global use.
"""

from typing import Dict

FORM_CODE_ERROR_MESSAGES: Dict[str, str] = {
    "required": "Este campo es obligatorio.",
    "unique": "Este valor ya está en uso.",
    "invalid": "Formato inválido.",
    "max_length": "Valor demasiado largo.",
    "min_length": "Valor demasiado corto.",
}

FORM_FIELD_ERROR_MESSAGES: Dict[str, str] = {
    "email.unique": "Este correo electrónico ya está registrado.",
    "email.invalid": "Correo inválido.",
    "password1.invalid": "Al menos 8 caracteres, con número y símbolo.",
    "password2.password_mismatch": "Las contraseñas no coinciden.",
    "first_name.invalid": "Nombre inválido.",
    "last_name.invalid": "Apellido inválido.",
}

AUTH_ERROR_MESSAGES: Dict[str, str] = {
    "auth.invalid_credentials": "Credenciales inválidas.",
    "auth.not_authenticated": "No autenticado.",
    "auth.not_verified": "Cuenta no verificada.",
    "auth.invalid_current_password": "La contraseña actual es incorrecta.",
    "auth.user_not_found": "Usuario no encontrado.",
    "auth.token_invalid": "Token inválido o expirado.",
}

GENERIC_ERROR_MESSAGES: Dict[str, str] = {
    "validation.error": "Errores de validación.",
}

ERROR_MESSAGES: Dict[str, str] = {
    **FORM_FIELD_ERROR_MESSAGES,
    **FORM_CODE_ERROR_MESSAGES,
    **AUTH_ERROR_MESSAGES,
    **GENERIC_ERROR_MESSAGES,
}
