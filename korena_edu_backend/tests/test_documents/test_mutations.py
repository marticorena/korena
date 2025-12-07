from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from apps.core.messages import ERROR_MESSAGES
from apps.documents.models.documents import Document, DocumentCategory, DocumentLevel
from tests.test_documents.graphql_strings import (
    CREATE_DOCUMENT_CATEGORY_MUTATION,
    CREATE_DOCUMENT_MUTATION,
)
from tests.test_documents.helpers import (
    helper_test_create_document,
    helper_test_create_document_category,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_create_document_creates_new_document_for_verified_user(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should create a new document for the verified user."""
    category = helper_test_create_document_category(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentCategoryCode": category.code,
        "title": "Mi documento docente",
        "description": "Descripción de prueba",
        "schoolId": None,
    }

    result: Dict[str, Any] = exec_gql(
        CREATE_DOCUMENT_MUTATION,
        variables=variables,
        context=verified_context,
    )

    payload = result["data"]["createDocument"]
    document_data = payload["document"]

    assert document_data["title"] == "Mi documento docente"
    assert document_data["description"] == "Descripción de prueba"
    assert document_data["category"]["code"] == category.code
    assert document_data["category"]["level"] == category.level

    document = Document.objects.get(pk=document_data["id"])

    assert document.owner == verified_user
    assert document.category == category
    assert document.is_archived is False


def test_create_document_uses_category_name_as_default_title(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should use category name as title when not provided."""
    category = helper_test_create_document_category(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentCategoryCode": category.code,
        "title": None,
        "description": "",
        "schoolId": None,
    }

    result: Dict[str, Any] = exec_gql(
        CREATE_DOCUMENT_MUTATION,
        variables=variables,
        context=verified_context,
    )

    payload = result["data"]["createDocument"]
    document_data = payload["document"]

    assert document_data["title"] == category.name

    document = Document.objects.get(pk=document_data["id"])

    assert document.title == category.name


def test_create_document_fails_when_category_not_found(
    gql_client: Any,
    verified_context,
) -> None:
    """createDocument should fail when the document category code does not exist."""
    variables: Dict[str, Any] = {
        "documentCategoryCode": "non-existing-category",
        "title": "Mi doc",
        "description": "",
        "schoolId": None,
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.category_not_found"]
    assert result.data is None


def test_create_document_fails_when_document_already_exists_for_user_and_category(
    gql_client: Any,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should fail when a document already exists for category + user."""
    category = helper_test_create_document_category(DocumentLevel.TEACHER)
    helper_test_create_document(verified_user, category, title="Ya existe")

    variables: Dict[str, Any] = {
        "documentCategoryCode": category.code,
        "title": "Nuevo intento",
        "description": "",
        "schoolId": None,
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.already_exists"]
    assert result.data is None


def test_create_document_requires_verified_user(
    gql_client: Any,
    non_verified_context,
    non_verified_user: User,
) -> None:
    """createDocument should fail when user is authenticated but not verified."""
    category = helper_test_create_document_category(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentCategoryCode": category.code,
        "title": "Doc no verificado",
        "description": "",
        "schoolId": None,
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_MUTATION,
        variable_values=variables,
        context_value=non_verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]
    assert result.data is None


def test_create_document_category_creates_new_category_for_verified_user(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """createDocumentCategory should create a new category for a verified user."""
    variables: Dict[str, Any] = {
        "code": "programacion-anual",
        "name": "Programación Anual",
        "level": DocumentLevel.TEACHER,
        "description": "Tipo de documento docente",
        "isOfficial": False,
        "mineduReference": "PA-Docente",
    }

    result: Dict[str, Any] = exec_gql(
        CREATE_DOCUMENT_CATEGORY_MUTATION,
        variables=variables,
        context=verified_context,
    )

    payload = result["data"]["createDocumentCategory"]
    doc_category_data = payload["documentCategory"]

    assert doc_category_data["code"] == "programacion-anual"
    assert doc_category_data["name"] == "Programación Anual"
    assert doc_category_data["level"] == DocumentLevel.TEACHER
    assert doc_category_data["isOfficial"] is False
    assert doc_category_data["mineduReference"] == "PA-Docente"

    category = DocumentCategory.objects.get(code="programacion-anual")

    assert category.name == "Programación Anual"
    assert category.level == DocumentLevel.TEACHER
    assert category.is_official is False


def test_create_document_type_fails_when_code_already_exists(
    gql_client: Any,
    verified_context,
) -> None:
    """createDocumentCategory should fail when the code already exists."""
    existing = DocumentCategory.objects.create(
        code="pei",
        name="Proyecto Educativo Institucional",
        description="PEI existente",
        level=DocumentLevel.SCHOOL,
    )

    variables: Dict[str, Any] = {
        "code": existing.code,
        "name": "Otro PEI",
        "level": existing.level,
        "description": "Intento duplicado",
        "isOfficial": False,
        "mineduReference": "",
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_CATEGORY_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.category_code_already_exists"]
    assert result.data is None


def test_create_document_type_requires_verified_user(
    gql_client: Any,
    non_verified_context,
) -> None:
    """createDocumentCategory should fail when user is not verified."""
    variables: Dict[str, Any] = {
        "code": "doc-no-verificado",
        "name": "Tipo no verificado",
        "level": DocumentLevel.TEACHER,
        "description": "No debería crearse",
        "isOfficial": False,
        "mineduReference": "",
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_CATEGORY_MUTATION,
        variable_values=variables,
        context_value=non_verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]
    assert result.data is None


def test_create_document_type_forbids_non_admin_official_flag(
    gql_client: Any,
    verified_context,
) -> None:
    """createDocumentCategory should reject non-admin users marking isOfficial=True."""
    variables: Dict[str, Any] = {
        "code": "norma-oficial-usuario",
        "name": "Norma oficial por usuario",
        "level": DocumentLevel.STATE,
        "description": "Intento de marcar oficial desde usuario regular",
        "isOfficial": True,
        "mineduReference": "RVM-TEST",
    }

    result = gql_client.execute_sync(
        CREATE_DOCUMENT_CATEGORY_MUTATION,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.category_official_forbidden"]
    assert result.data is None
