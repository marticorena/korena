import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def create_celery_app() -> Celery:
    """Create and configure the Celery application instance.

    Returns:
        Celery: Configured Celery application.
    """

    app = Celery("config")

    # Load Celery configuration from Django settings with CELERY_ prefix.
    app.config_from_object("django.conf:settings", namespace="CELERY")

    # Autodiscover tasks.py modules in INSTALLED_APPS.
    app.autodiscover_tasks()

    return app


app: Celery = create_celery_app()
