import logging
from typing import Any

from django.core import mail

import pytest

from apps.core.metrics import emails_sent_total
from apps.core.utils import get_metric_value
from apps.notifications.models import EmailLog, EmailStatus
from apps.notifications.tasks import send_email_task

MONKEYPATCH_FILE = "apps.notifications.tasks"


@pytest.mark.django_db
def test_send_email_task_success(settings: Any, verified_user: Any) -> None:
    """Email is sent using locmem backend, log updated, metrics incremented."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "system@example.com"

    email_log = EmailLog.objects.create(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=verified_user.email,
        user=verified_user,
        subject="Test Subject",
        plain_message="Plain text content",
        html_message="<p>HTML content</p>",
    )

    sent_before = get_metric_value(emails_sent_total, status="sent")

    send_email_task.run(email_log.id)

    email_log.refresh_from_db()

    # EmailLog updated
    assert email_log.status == EmailStatus.SENT
    assert email_log.retries == 0
    assert email_log.sent_at is not None
    assert email_log.last_attempt_at is not None

    # Email delivered (locmem)
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.subject == "Test Subject"
    assert msg.to == [verified_user.email]
    assert msg.from_email == settings.DEFAULT_FROM_EMAIL

    # Metric incremented
    sent_after = get_metric_value(emails_sent_total, status="sent")
    assert sent_after == sent_before + 1


@pytest.mark.django_db
def test_send_email_task_retries_on_exception(
    monkeypatch: pytest.MonkeyPatch,
    settings: Any,
    verified_user: Any,
) -> None:
    """
    When send_mail raises an error, task marks FAILED and increments metrics.
    The exception surfaced is RuntimeError because track_celery_task wraps the task.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "system@example.com"

    email_log = EmailLog.objects.create(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=verified_user.email,
        user=verified_user,
        subject="Test Failure",
        plain_message="Plain",
        html_message="<p>HTML</p>",
    )

    def failing_send_mail(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(f"{MONKEYPATCH_FILE}.send_mail", failing_send_mail)

    failed_before = get_metric_value(emails_sent_total, status="failed")

    # Due to the decorator, this raises RuntimeError, not Retry
    with pytest.raises(RuntimeError) as exc:
        send_email_task.run(email_log.id)

    assert "boom" in str(exc.value)

    email_log.refresh_from_db()

    # State updated
    assert email_log.status == EmailStatus.FAILED
    assert email_log.retries == 1
    assert "boom" in email_log.error_message

    failed_after = get_metric_value(emails_sent_total, status="failed")
    assert failed_after == failed_before + 1


@pytest.mark.django_db
def test_send_email_task_email_log_not_found(caplog: pytest.LogCaptureFixture) -> None:
    """If the log does not exist, task logs an error and does nothing else."""
    caplog.set_level(logging.ERROR)

    send_email_task.run(999999)

    assert "does not exist" in caplog.text
