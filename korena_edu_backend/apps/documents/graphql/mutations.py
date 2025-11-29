from typing import Optional

import strawberry
from strawberry.types import Info

from apps.core.graphql.extensions import GraphQLOperationMetricsExtension
from apps.core.graphql.permissions import IsAuthenticated, IsVerified
from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import documents_created_total
from apps.documents.graphql.types import DocumentType
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.schools.models import School as SchoolModel


@strawberry.type
class DocumentMutations:
    """Root mutation group for document-related operations.

    File uploads are handled via REST:
    - POST /api/documents/<id>/versions/  (multipart/form-data)
    """

    @strawberry.mutation(
        permission_classes=[IsAuthenticated, IsVerified],
        extensions=[GraphQLOperationMetricsExtension("create_document")],
    )
    def create_document(
        self,
        info: Info,
        document_type_code: str,
        title: Optional[str] = None,
        description: Optional[str] = "",
        school_id: Optional[strawberry.ID] = None,
    ) -> DocumentType:
        user = info.context.user

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

        document = DocumentModel.objects.create(
            owner=user,
            school=school,
            type=document_type,
            title=resolved_title,
            description=description or "",
        )

        documents_created_total.inc()

        return document
