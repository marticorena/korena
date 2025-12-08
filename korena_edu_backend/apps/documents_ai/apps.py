from django.apps import AppConfig


class DocumentsAiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents_ai"

    def ready(self) -> None:
        import apps.documents_ai.signals  # noqa
