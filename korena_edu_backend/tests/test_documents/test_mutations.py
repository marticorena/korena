from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from apps.core.messages import ERROR_MESSAGES
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel
from tests.test_documents.graphql_strings import CREATE_DOCUMENT_MUTATION
from tests.test_documents.helpers import create_document, create_document_type

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_create_document_creates_new_document_for_verified_user(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should create a new document for the verified user."""
    doc_type = create_document_type(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentTypeCode": doc_type.code,
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
    assert document_data["type"]["code"] == doc_type.code
    assert document_data["type"]["level"] == doc_type.level

    document = DocumentModel.objects.get(pk=document_data["id"])

    assert document.owner == verified_user
    assert document.type == doc_type
    assert document.is_archived is False


def test_create_document_uses_type_name_as_default_title(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should use DocumentType name as title when not provided."""
    doc_type = create_document_type(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentTypeCode": doc_type.code,
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

    assert document_data["title"] == doc_type.name

    document = DocumentModel.objects.get(pk=document_data["id"])

    assert document.title == doc_type.name


def test_create_document_fails_when_type_not_found(
    gql_client: Any,
    verified_context,
) -> None:
    """createDocument should fail when the document type code does not exist."""
    variables: Dict[str, Any] = {
        "documentTypeCode": "non-existing-type",
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

    assert error.message == ERROR_MESSAGES["documents.type_not_found"]
    assert result.data is None


def test_create_document_fails_when_document_already_exists_for_user_and_type(
    gql_client: Any,
    verified_user: User,
    verified_context,
) -> None:
    """createDocument should fail when a document already exists for type + user."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    create_document(verified_user, doc_type, title="Ya existe")

    variables: Dict[str, Any] = {
        "documentTypeCode": doc_type.code,
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
    doc_type = create_document_type(DocumentLevel.TEACHER)

    variables: Dict[str, Any] = {
        "documentTypeCode": doc_type.code,
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
