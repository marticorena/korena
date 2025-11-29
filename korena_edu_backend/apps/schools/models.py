from django.db import models
from django.utils import timezone


class School(models.Model):
    """Represents an educational institution within the Korena ecosystem.

    A school can be linked to multiple users and documents. Schools may optionally
    be verified, indicating that their data has been validated by the system
    or through an administrative process.
    """

    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional school code, such as a local or national registry identifier.",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Indicates whether the school has been validated/approved.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the school's name as its string representation."""

        return self.name
