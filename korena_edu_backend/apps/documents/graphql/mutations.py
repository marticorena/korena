from typing import Optional

import strawberry
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql
from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import documents_created_total
from apps.documents.graphql.types import DocumentType
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.schools.models import School as SchoolModel
from config.graphql.extensions import GraphQLOperationMetricsExtension


@strawberry.type
class DocumentMutations:
    """Root mutation group for document-related operations.

    File uploads are handled via REST:
    - POST /api/documents/<id>/versions/  (multipart/form-data)
    """

    @strawberry.mutation(
        permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql],
        extensions=[GraphQLOperationMetricsExtension("create_document")],
        name="createDocument",
    )
    def create_document(
        self,
        info: Info,
        document_type_code: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        school_id: Optional[strawberry.ID] = None,
    ) -> DocumentType:
        """Create a document shell for the authenticated user.

        This mutation creates the base document record (metadata). File
        uploads are handled separately via the REST endpoint.

        Args:
            info: Strawberry execution context.
            document_type_code: Unique code for the document type
                (for example, "PEI", "PAT", "PCI", "PA", "UA").
            title: Optional custom title for the document. If omitted, the
                document type name will be used.
            description: Optional description for the document.
            school_id: Optional school ID. If provided, the document will be
                associated with that school. If omitted, the document will be
                personal (no school).

        Returns:
            DocumentType: The created document instance exposed as a GraphQL type.

        Raises:
            ValueError: If the document type does not exist, if the school does
                not exist, or if a document of this type already exists for the
                given user and school combination.
        """
        user = info.context.request.user

        try:
            document_type = DocumentTypeModel.objects.get(code=document_type_code)
        except DocumentTypeModel.DoesNotExist as exc:
            raise ValueError(
                ERROR_MESSAGES["documents.type_not_found"],
            ) from exc

        school: Optional[SchoolModel] = None
        if school_id is not None:
            try:
                school = SchoolModel.objects.get(pk=school_id)
            except SchoolModel.DoesNotExist as exc:
                raise ValueError(
                    ERROR_MESSAGES["validation.error"],
                ) from exc

        existing_qs = DocumentModel.objects.filter(
            owner=user,
            type=document_type,
        )
        if school is None:
            existing_qs = existing_qs.filter(school__isnull=True)
        else:
            existing_qs = existing_qs.filter(school=school)

        if existing_qs.exists():
            raise ValueError(ERROR_MESSAGES["documents.already_exists"])

        resolved_title = title or document_type.name
        resolved_description = description or ""

        document = DocumentModel.objects.create(
            owner=user,
            school=school,
            type=document_type,
            title=resolved_title,
            description=resolved_description,
        )

        documents_created_total.inc()

        return document
