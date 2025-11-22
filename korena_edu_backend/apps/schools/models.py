from django.db import models
from django.utils import timezone


class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name
