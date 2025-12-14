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
    "auth.not_verified": "Cuenta no verificada.",
    "auth.invalid_current_password": "La contraseña actual es incorrecta.",
    "auth.user_not_found": "Usuario no encontrado.",
    "auth.token_invalid": "Token inválido o expirado.",
}

# Upload / files domain errors: "upload.code" → text
UPLOAD_ERROR_MESSAGES: Dict[str, str] = {
    "upload.no_file": "El archivo no se recibió correctamente.",
    "upload.invalid_format": "Formato no permitido. Solo JPG, PNG o PDF.",
    "upload.invalid_document_format": "Formato no permitido. Solo PDF o DOCX.",
    "upload.file_too_large": "El archivo es demasiado grande. Máximo {max_size} MB.",
}

# Documents domain errors: "documents.code" → text
DOCUMENT_ERROR_MESSAGES: Dict[str, str] = {
    "documents.invalid_level": "El nivel de documento proporcionado no es válido.",
    "documents.not_found_or_not_owned": "Documento no encontrado o no te pertenece.",
    "documents.already_exists": "Ya existe un documento de este tipo para tu cuenta.",
    "documents.category_not_found": "El tipo de documento solicitado no existe.",
    "documents.category_code_already_exists": "Ya existe un tipo de documento con ese código.",
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
    **DOCUMENT_ERROR_MESSAGES,
    **GENERIC_ERROR_MESSAGES,
}
