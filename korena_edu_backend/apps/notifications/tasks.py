import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from apps.notifications.models import EmailLog, EmailStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_log_id: int) -> None:
    log = EmailLog.objects.get(pk=email_log_id)

    try:
        send_mail(
            subject=log.subject,
            message=log.body_snapshot,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[log.to_email],
        )
        log.status = EmailStatus.SENT
        log.sent_at = timezone.now()
        log.last_attempt_at = log.sent_at
        log.save(update_fields=["status", "sent_at", "last_attempt_at"])
    except Exception as exc:
        log.status = EmailStatus.FAILED
        log.retries += 1
        log.error_message = str(exc)
        log.last_attempt_at = timezone.now()
        log.save(update_fields=["status", "retries", "error_message", "last_attempt_at"])

        logger.exception("Error sending email (EmailLog id=%s).", email_log_id)
        raise self.retry(exc=exc, countdown=60)
