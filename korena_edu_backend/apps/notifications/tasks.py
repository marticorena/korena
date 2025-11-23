import logging

from apps.core.metrics import emails_sent_total, track_celery_task
from apps.notifications.models import EmailLog, EmailStatus
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@track_celery_task("send_email_task")
def send_email_task(self, email_log_id: int) -> None:
    """Send an email asynchronously and update the EmailLog entry.

    Args:
        self: Celery task instance (used for retry logic).
        email_log_id (int): Primary key of the EmailLog to process.

    Raises:
        self.retry: Re-raised when an email fails, triggering a retry.
    """
    try:
        log: EmailLog = EmailLog.objects.get(pk=email_log_id)
    except EmailLog.DoesNotExist:
        logger.error("EmailLog with id=%s does not exist.", email_log_id)
        return

    try:
        # Send the email using Django's email backend
        send_mail(
            subject=log.subject,
            message=log.body_snapshot,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[log.to_email],
        )

        # Update success state
        now = timezone.now()
        log.status = EmailStatus.SENT
        log.sent_at = now
        log.last_attempt_at = now
        log.save(update_fields=["status", "sent_at", "last_attempt_at"])

        # Mark email as successfully sent
        emails_sent_total.labels(status="sent").inc()

    except Exception as exc:
        # Update failure state
        now = timezone.now()
        log.status = EmailStatus.FAILED
        log.retries += 1
        log.error_message = str(exc)
        log.last_attempt_at = now
        log.save(
            update_fields=["status", "retries", "error_message", "last_attempt_at"]
        )

        # Mark email as failed
        emails_sent_total.labels(status="failed").inc()

        logger.exception(
            "Error sending email (EmailLog id=%s). Attempt #%s",
            email_log_id,
            log.retries,
        )

        # Retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)
