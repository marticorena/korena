from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as DjangoClient
from django.urls import reverse

import pytest

from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import (
    document_versions_uploaded_total,
    documents_by_level_total,
)
from apps.core.utils import get_metric_value
from apps.documents.models import (
    DocumentLevel,
)
from apps.documents.models import (
    DocumentVersionStatus,
)
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from tests.test_documents.graphql_strings import CREATE_DOCUMENT_MUTATION

pytestmark = pytest.mark.django_db

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_document_type(level: str = DocumentLevel.TEACHER) -> DocumentTypeModel:
    """Helper to create a DocumentType for tests.

    Args:
        level: Document level.

    Returns:
        DocumentTypeModel: Created document type.
    """
    doc_type = DocumentTypeModel.objects.create(
        code=f"doc-{level.lower()}",
        name=f"Documento {level}",
        description="Tipo de prueba",
        level=level,
        is_official=False,
    )

    return doc_type


def create_document(
    owner: User,
    doc_type: DocumentTypeModel,
    title: str = "Documento de prueba",
    description: str = "Descripción",
) -> DocumentModel:
    """Helper to create a Document for tests.

    Args:
        owner: Document owner.
        doc_type: Document type instance.
        title: Document title.
        description: Document description.

    Returns:
        DocumentModel: Created document.
    """
    document = DocumentModel.objects.create(
        owner=owner,
        school=None,
        type=doc_type,
        title=title,
        description=description,
        is_archived=False,
    )

    return document


# ---------------------------------------------------------------------------
# GraphQL mutation: createDocument
# ---------------------------------------------------------------------------


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
    gql_client,
    verified_context,
) -> None:
    """createDocument should fail when the document type code does not exist."""
    variables: Dict[str, Any] = {
        "documentTypeCode": "non-existing-type",
        "title": "Mi doc",
        "description": "",
        "schoolId": None,
    }

    result: Dict[str, Any] = gql_client.execute(
        CREATE_DOCUMENT_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["documents.type_not_found"]
    assert result["data"]["createDocument"] is None


def test_create_document_fails_when_document_already_exists_for_user_and_type(
    gql_client,
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

    result: Dict[str, Any] = gql_client.execute(
        CREATE_DOCUMENT_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["documents.already_exists"]
    assert result["data"]["createDocument"] is None


def test_create_document_requires_verified_user(
    gql_client,
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

    result: Dict[str, Any] = gql_client.execute(
        CREATE_DOCUMENT_MUTATION,
        variables=variables,
        context_value=non_verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]
    assert result["data"]["createDocument"] is None


# ---------------------------------------------------------------------------
# REST endpoint: POST /api/documents/<id>/versions/
# ---------------------------------------------------------------------------


def test_rest_upload_document_version_creates_new_version_and_updates_current(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should create a new version and set it as current."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(verified_user, doc_type, title="Documento base")

    client.force_login(verified_user)

    upload_content = b"Dummy PDF content"
    uploaded_file = SimpleUploadedFile(
        "test.pdf",
        upload_content,
        content_type="application/pdf",
    )

    versions_before = DocumentVersionModel.objects.count()
    uploaded_before = get_metric_value(document_versions_uploaded_total)
    by_level_before = get_metric_value(
        documents_by_level_total,
        level=DocumentLevel.TEACHER,
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    response = client.post(
        url,
        data={"file": uploaded_file},
    )

    assert response.status_code == 201

    payload: Dict[str, Any] = response.json()
    version_data = payload["version"]
    document_id = payload["document_id"]

    # Version created.
    assert DocumentVersionModel.objects.count() == versions_before + 1
    version = DocumentVersionModel.objects.get(pk=version_data["id"])
    assert version.document_id == document.id
    assert version.status == DocumentVersionStatus.DRAFT
    assert version.source == "UPLOAD"
    assert version.created_by == verified_user

    # Document current_version updated.
    document.refresh_from_db()
    assert document.current_version_id == version.id
    assert document_id == document.id

    # Metrics updated.
    uploaded_after = get_metric_value(document_versions_uploaded_total)
    assert uploaded_after == uploaded_before + 1

    by_level_after = get_metric_value(
        documents_by_level_total,
        level=DocumentLevel.TEACHER,
    )
    assert by_level_after == by_level_before + 1


def test_rest_upload_document_version_requires_authentication(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should fail for anonymous requests."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(verified_user, doc_type, title="Documento base")

    upload_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    versions_before = DocumentVersionModel.objects.count()

    response = client.post(
        url,
        data={"file": upload_file},
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data

    # No version created.
    assert DocumentVersionModel.objects.count() == versions_before


def test_rest_upload_document_version_requires_verified_user(
    client: DjangoClient,
    non_verified_user: User,
) -> None:
    """REST upload should fail when user is not verified."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(non_verified_user, doc_type, title="Documento base")

    client.force_login(non_verified_user)

    upload_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    response = client.post(
        url,
        data={"file": upload_file},
    )

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == ERROR_MESSAGES["auth.not_verified"]


def test_rest_upload_document_version_fails_when_document_not_found_or_not_owned(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should fail when document does not exist or is not owned."""
    owner2 = User.objects.create_user(
        email="owner2@example.com",
        password="P4ss-w0rd!",
        first_name="Owner2",
        last_name="User2",
    )
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(owner2, doc_type, title="Documento de otro usuario")

    client.force_login(verified_user)

    upload_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    versions_before = DocumentVersionModel.objects.count()

    response = client.post(
        url,
        data={"file": upload_file},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ERROR_MESSAGES["documents.not_found_or_not_owned"]

    # No version created.
    assert DocumentVersionModel.objects.count() == versions_before


def test_rest_upload_document_version_requires_file(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should fail when no file is provided."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(verified_user, doc_type, title="Documento base")

    client.force_login(verified_user)

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    versions_before = DocumentVersionModel.objects.count()

    response = client.post(
        url,
        data={},  # No "file" field.
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ERROR_MESSAGES["upload.no_file"]
    assert DocumentVersionModel.objects.count() == versions_before
