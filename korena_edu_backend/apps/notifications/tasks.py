import logging

from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

from apps.notifications.models import EmailLog, EmailStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_log_id: int) -> None:
    """Send an email asynchronously and update the EmailLog entry."""
    try:
        log = EmailLog.objects.get(pk=email_log_id)
    except EmailLog.DoesNotExist:
        logger.error("EmailLog with id=%s does not exist.", email_log_id)

        return

    try:
        send_mail(
            subject=log.subject,
            message=log.plain_message,
            from_email=log.from_email,
            recipient_list=[log.to_email],
            html_message=log.html_message or None,
        )

        log.status = EmailStatus.SENT
        log.sent_at = timezone.now()
        log.error_message = ""
        log.save(update_fields=["status", "sent_at", "error_message"])

    except Exception as exc:
        log.status = EmailStatus.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])

        attempt = getattr(self.request, "retries", 0) + 1
        logger.exception(
            "Error sending email (EmailLog id=%s). Attempt #%s",
            email_log_id,
            attempt,
        )

        raise self.retry(exc=exc, countdown=30)
