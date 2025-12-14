from typing import Any, Dict

from django.contrib.auth import get_user_model

import pytest

from apps.core.messages import ERROR_MESSAGES
from apps.documents.models import DocumentLevel
from tests.test_documents.graphql_strings import DOCUMENT_QUERY, MY_DOCUMENTS_QUERY
from tests.test_documents.helpers import (
    helper_test_create_document,
    helper_test_create_document_category,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_my_documents_returns_only_owned_documents_for_verified_user(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """myDocuments should return only documents owned by the verified user."""
    teacher_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    other_category = helper_test_create_document_category(DocumentLevel.SCHOOL)

    helper_test_create_document(verified_user, teacher_category, title="Doc 1")
    helper_test_create_document(verified_user, other_category, title="Doc 2")

    other_user = User.objects.create_user(
        email="other@example.com",
        password="P4ss-w0rd!",
        first_name="Other",
        last_name="User",
    )
    helper_test_create_document(other_user, teacher_category, title="Doc other")

    result: Dict[str, Any] = exec_gql(
        MY_DOCUMENTS_QUERY,
        variables={"level": None},
        context=verified_context,
    )

    nodes = result["data"]["myDocuments"]
    titles = {d["title"] for d in nodes}

    assert len(nodes) == 2
    assert titles == {"Doc 1", "Doc 2"}

    for node in nodes:
        assert node["isArchived"] is False


def test_my_documents_filters_by_level(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """myDocuments should filter documents by DocumentLevel when provided."""
    teacher_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    school_category = helper_test_create_document_category(DocumentLevel.SCHOOL)

    helper_test_create_document(verified_user, teacher_category, title="Doc Teacher 1")
    helper_test_create_document(verified_user, school_category, title="Doc School 1")

    result: Dict[str, Any] = exec_gql(
        MY_DOCUMENTS_QUERY,
        variables={"level": DocumentLevel.TEACHER},
        context=verified_context,
    )

    nodes = result["data"]["myDocuments"]

    assert len(nodes) == 1
    assert nodes[0]["title"] == "Doc Teacher 1"
    assert nodes[0]["category"]["level"] == DocumentLevel.TEACHER


def test_my_documents_invalid_level_returns_error(
    gql_client: Any,
    verified_context,
) -> None:
    """myDocuments should return an error when level is invalid."""
    variables = {"level": "INVALID_LEVEL"}

    result = gql_client.execute_sync(
        MY_DOCUMENTS_QUERY,
        variable_values=variables,
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.invalid_level"]
    assert result.data is None


def test_my_documents_requires_verified_user(
    gql_client: Any,
    non_verified_context,
) -> None:
    """myDocuments should fail when user is authenticated but not verified."""
    result = gql_client.execute_sync(
        MY_DOCUMENTS_QUERY,
        variable_values={"level": None},
        context_value=non_verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]
    assert result.data is None


def test_document_returns_single_document_for_verified_owner(
    exec_gql,
    verified_user: User,
    verified_context,
) -> None:
    """document should return the requested document if owned by the verified user."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    doc = helper_test_create_document(verified_user, doc_category, title="Mi documento")

    result: Dict[str, Any] = exec_gql(
        DOCUMENT_QUERY,
        variables={"id": str(doc.id)},
        context=verified_context,
    )

    node = result["data"]["document"]

    assert node is not None
    assert node["id"] == str(doc.id)
    assert node["title"] == "Mi documento"
    assert node["category"]["level"] == DocumentLevel.TEACHER


def test_document_raises_error_when_not_found_or_not_owned(
    gql_client: Any,
    verified_context,
    verified_user: User,
) -> None:
    """document should raise error when document does not exist or is not owned."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    other_user = User.objects.create_user(
        email="owner2@example.com",
        password="P4ss-w0rd!",
        first_name="Owner2",
        last_name="User2",
    )
    doc = helper_test_create_document(other_user, doc_category, title="Other doc")

    result = gql_client.execute_sync(
        DOCUMENT_QUERY,
        variable_values={"id": str(doc.id)},
        context_value=verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["documents.not_found_or_not_owned"]
    assert result.data is None


def test_document_requires_verified_user(
    gql_client: Any,
    non_verified_context,
    non_verified_user: User,
) -> None:
    """document should fail when user is not verified."""
    doc_category = helper_test_create_document_category(DocumentLevel.TEACHER)
    doc = helper_test_create_document(
        non_verified_user, doc_category, title="Doc verificado"
    )

    result = gql_client.execute_sync(
        DOCUMENT_QUERY,
        variable_values={"id": str(doc.id)},
        context_value=non_verified_context,
    )

    assert result.errors is not None
    error = result.errors[0]

    assert error.message == ERROR_MESSAGES["auth.not_verified"]
    assert result.data is None
