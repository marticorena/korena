from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from django.conf import settings

# Set default Django settings module for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def create_celery_app() -> Celery:
    """
    Create and configure the Celery application instance.
    """

    # Create Celery app
    app = Celery("config")

    # Load Django settings as Celery config
    app.config_from_object("django.conf:settings", namespace="CELERY")

    # Autodiscover tasks across Django apps
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

    return app


app = create_celery_app()


@app.task(bind=True)
def debug_task(self):
    """
    Simple debug task to verify Celery functionality.
    """
    print(f"Request: {self.request!r}")
