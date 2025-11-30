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
from apps.documents.models import DocumentLevel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from apps.documents.models import DocumentVersionStatus
from tests.helpers import auth_headers_for
from tests.test_documents.helpers import (
    helper_test_create_document,
    helper_test_create_document_category,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_rest_upload_document_version_creates_new_version_and_updates_current(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should create a new version and set it as current."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    document = helper_test_create_document(
        verified_user, doc_category, title="Documento base"
    )

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

    headers = auth_headers_for(verified_user)
    response = client.post(
        url,
        data={"file": uploaded_file},
        **headers,
    )

    assert response.status_code == 201

    payload: Dict[str, Any] = response.json()
    version_data = payload["version"]
    document_id = payload["document_id"]

    assert DocumentVersionModel.objects.count() == versions_before + 1
    version = DocumentVersionModel.objects.get(pk=version_data["id"])

    assert version.document_id == document.id
    assert version.status == DocumentVersionStatus.DRAFT
    assert version.source == "UPLOAD"
    assert version.created_by == verified_user

    document.refresh_from_db()
    assert document.current_version_id == version.id
    assert document_id == document.id

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
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    document = helper_test_create_document(
        verified_user, doc_category, title="Documento base"
    )

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
    body = response.json()

    assert body["data"] is None
    assert "errors" in body
    assert len(body["errors"]) == 1

    error = body["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_authenticated"]
    assert error["path"] == ["documentVersionUpload"]

    assert DocumentVersionModel.objects.count() == versions_before


def test_rest_upload_document_version_requires_verified_user(
    client: DjangoClient,
    non_verified_user: User,
) -> None:
    """REST upload should fail when user is not verified."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    document = helper_test_create_document(
        non_verified_user, doc_category, title="Documento base"
    )

    upload_file = SimpleUploadedFile(
        "test.pdf",
        b"Dummy",
        content_type="application/pdf",
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    headers = auth_headers_for(non_verified_user)
    response = client.post(
        url,
        data={"file": upload_file},
        **headers,
    )

    assert response.status_code == 403
    body = response.json()

    assert body["data"] is None
    assert "errors" in body
    assert len(body["errors"]) == 1

    error = body["errors"][0]
    assert error["message"] == ERROR_MESSAGES["auth.not_verified"]
    assert error["path"] == ["documentVersionUpload"]


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
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    document = helper_test_create_document(
        owner2, doc_category, title="Documento de otro usuario"
    )

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
    headers = auth_headers_for(verified_user)

    response = client.post(
        url,
        data={"file": upload_file},
        **headers,
    )

    assert response.status_code == 404
    body = response.json()

    assert body["data"] is None
    assert "errors" in body
    assert len(body["errors"]) == 1

    error = body["errors"][0]
    assert error["message"] == ERROR_MESSAGES["documents.not_found_or_not_owned"]
    assert error["path"] == ["documentVersionUpload"]

    assert DocumentVersionModel.objects.count() == versions_before


def test_rest_upload_document_version_requires_file(
    client: DjangoClient,
    verified_user: User,
) -> None:
    """REST upload should fail when no file is provided."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    document = helper_test_create_document(
        verified_user, doc_category, title="Documento base"
    )

    url = reverse(
        "document-version-upload",
        kwargs={"document_id": document.id},
    )

    versions_before = DocumentVersionModel.objects.count()
    headers = auth_headers_for(verified_user)

    response = client.post(
        url,
        data={},
        **headers,
    )

    assert response.status_code == 400
    body = response.json()

    assert body["data"] is None
    assert "errors" in body
    assert len(body["errors"]) == 1

    error = body["errors"][0]
    assert error["message"] == ERROR_MESSAGES["upload.no_file"]
    assert error["path"] == ["documentVersionUpload"]

    assert DocumentVersionModel.objects.count() == versions_before
