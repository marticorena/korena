from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailStatus(models.TextChoices):
    """Enumeration of possible email delivery states."""

    PENDING = "PENDING", "Pendiente"
    SENT = "SENT", "Enviado"
    FAILED = "FAILED", "Fallido"


class EmailLog(models.Model):
    """Stores a snapshot of an email sent by the system."""

    from_email = models.EmailField()
    to_email = models.EmailField()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )

    subject = models.CharField(max_length=255)
    plain_message = models.TextField()
    html_message = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
    )
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return a readable representation of the email log."""

        return f"{self.to_email} - {self.subject} [{self.status}]"
