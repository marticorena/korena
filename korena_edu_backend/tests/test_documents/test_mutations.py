from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

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
from tests.test_documents.graphql_strings import UPLOAD_DOCUMENT_VERSION_MUTATION

pytestmark = pytest.mark.django_db

User = get_user_model()


def create_document_type(level: str = DocumentLevel.TEACHER) -> DocumentTypeModel:
    """Helper to create a DocumentType for tests."""
    return DocumentTypeModel.objects.create(
        code=f"doc-{level.lower()}",
        name=f"Documento {level}",
        description="Tipo de prueba",
        level=level,
        is_official=False,
    )


def create_document(
    owner: User,
    doc_type: DocumentTypeModel,
    title: str = "Documento de prueba",
    description: str = "Descripción",
) -> DocumentModel:
    """Helper to create a Document for tests."""
    return DocumentModel.objects.create(
        owner=owner,
        school=None,
        type=doc_type,
        title=title,
        description=description,
        is_archived=False,
    )


def test_upload_document_version_creates_new_version_and_updates_current(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """uploadDocumentVersion should create a new version and set it as current."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(verified_user, doc_type, title="Documento base")

    # Create a small in-memory file for upload.
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

    variables: Dict[str, Any] = {
        "documentId": str(document.id),
        "file": uploaded_file,
    }

    result: Dict[str, Any] = exec_gql(
        UPLOAD_DOCUMENT_VERSION_MUTATION,
        variables=variables,
        context=verified_context,
    )

    payload = result["data"]["uploadDocumentVersion"]
    version_data = payload["documentVersion"]
    document_data = payload["document"]

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
    assert document_data["id"] == str(document.id)
    assert document_data["currentVersion"]["id"] == str(version.id)

    # Metrics updated.
    uploaded_after = get_metric_value(document_versions_uploaded_total)
    assert uploaded_after == uploaded_before + 1

    by_level_after = get_metric_value(
        documents_by_level_total,
        level=DocumentLevel.TEACHER,
    )
    assert by_level_after == by_level_before + 1


def test_upload_document_version_requires_authentication(
    gql_client,
    anon_context,
    verified_user: User,
) -> None:
    """uploadDocumentVersion should fail for anonymous context."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(verified_user, doc_type, title="Documento base")

    uploaded_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    variables: Dict[str, Any] = {
        "documentId": str(document.id),
        "file": uploaded_file,
    }

    result: Dict[str, Any] = gql_client.execute(
        UPLOAD_DOCUMENT_VERSION_MUTATION,
        variables=variables,
        context_value=anon_context,
    )

    assert "errors" in result
    # Message viene de login_required; no dependemos del texto exacto.
    assert result["data"]["uploadDocumentVersion"] is None


def test_upload_document_version_requires_verified_user(
    gql_client,
    non_verified_context,
    non_verified_user: User,
) -> None:
    """uploadDocumentVersion should fail when user is not verified."""
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(non_verified_user, doc_type, title="Documento base")

    uploaded_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    variables: Dict[str, Any] = {
        "documentId": str(document.id),
        "file": uploaded_file,
    }

    result: Dict[str, Any] = gql_client.execute(
        UPLOAD_DOCUMENT_VERSION_MUTATION,
        variables=variables,
        context_value=non_verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]
    assert result["data"]["uploadDocumentVersion"] is None


def test_upload_document_version_fails_when_document_not_found_or_not_owned(
    gql_client,
    verified_user: User,
    verified_context,
) -> None:
    """uploadDocumentVersion should fail when document does not exist or is not owned."""
    # Document belongs to another user.
    owner2 = User.objects.create_user(
        email="owner2@example.com",
        password="P4ss-w0rd!",
        first_name="Owner2",
        last_name="User2",
    )
    doc_type = create_document_type(DocumentLevel.TEACHER)
    document = create_document(owner2, doc_type, title="Documento de otro usuario")

    uploaded_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    variables: Dict[str, Any] = {
        "documentId": str(document.id),
        "file": uploaded_file,
    }

    versions_before = DocumentVersionModel.objects.count()

    result: Dict[str, Any] = gql_client.execute(
        UPLOAD_DOCUMENT_VERSION_MUTATION,
        variables=variables,
        context_value=verified_context,
    )

    assert "errors" in result
    error = result["errors"][0]
    assert error["message"] == ERROR_MESSAGES["documents.not_found_or_not_owned"]
    assert result["data"]["uploadDocumentVersion"] is None

    # No version created.
    assert DocumentVersionModel.objects.count() == versions_before
