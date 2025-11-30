from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from strawberry.django.views import GraphQLView

from apps.core.metrics import metrics_view
from apps.documents.api.views import DocumentVersionUploadView
from config.schema import schema

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "graphql/",
        csrf_exempt(
            GraphQLView.as_view(
                schema=schema,
                graphql_ide=True,
            )
        ),
        name="graphql",
    ),
    path(
        "api/documents/<int:document_id>/versions/",
        csrf_exempt(DocumentVersionUploadView.as_view()),
        name="document-version-upload",
    ),
    path("metrics/", metrics_view, name="metrics"),
]
