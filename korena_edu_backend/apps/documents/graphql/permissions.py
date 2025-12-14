from typing import Any

from strawberry.exceptions import GraphQLError

from apps.core.messages import ERROR_MESSAGES
from apps.documents.models.choices import DocumentLevel
from apps.documents.models.documents import DocumentVersion


def require_document_version_access(
    *,
    user: Any,
    version: DocumentVersion,
) -> None:
    """Ensure user can access a given DocumentVersion.

    Rules:
        - STATE level documents → any authenticated & verified user
        - Other levels → only owner
    """
    category = version.document.category

    if category.level == DocumentLevel.STATE:
        return

    if version.document.owner_id != getattr(user, "id", None):
        raise GraphQLError(ERROR_MESSAGES["documents.access_denied"])
