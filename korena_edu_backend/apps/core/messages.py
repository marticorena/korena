"""
Centralized error and user-facing messages.

This module defines user-facing messages indexed by:
- form field + code (e.g. "email.unique")
- generic validation codes (e.g. "required", "invalid")
- domain-specific codes (e.g. "auth.not_authenticated", "documents.category_not_found")

All messages are merged into ERROR_MESSAGES for global use.
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

DOCUMENTS_ERROR_MESSAGES: Dict[str, str] = {
    "documents.category_not_found": "La categoría solicitada no existe.",
    "documents.already_exists": "Ya existe un documento de esta categoría para tu cuenta.",
    "documents.category_code_already_exists": "Ya existe una categoría con ese código.",
    "documents.invalid_level": "El nivel de documento proporcionado no es válido.",
    "documents.not_found_or_not_owned": "Documento no encontrado o no te pertenece.",
}

UPLOAD_ERROR_MESSAGES: Dict[str, str] = {
    "upload.no_file": "El archivo no se recibió correctamente.",
    "upload.invalid_format": "Formato no permitido. Solo JPG, PNG o PDF.",
}

GENERIC_ERROR_MESSAGES: Dict[str, str] = {
    "validation.error": "Errores de validación.",
}

ERROR_MESSAGES: Dict[str, str] = {
    **FORM_FIELD_ERROR_MESSAGES,
    **FORM_CODE_ERROR_MESSAGES,
    **AUTH_ERROR_MESSAGES,
    **DOCUMENTS_ERROR_MESSAGES,
    **GENERIC_ERROR_MESSAGES,
}
