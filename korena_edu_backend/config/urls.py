from apps.core.metrics import metrics_view
from config.schema import schema
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "graphql/",
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True, schema=schema)),
    ),
    path("metrics/", metrics_view),
]
