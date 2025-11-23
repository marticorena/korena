from typing import Any, Optional

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for handling user creation.

    Provides user and superuser creation logic. Normalizes emails and
    ensures required flags for admin accounts are set.
    """

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        """Create a standard user.

        Args:
            email (str): User email (required).
            password (Optional[str]): Raw password to set.
            extra_fields (Any): Additional fields for the model.

        Raises:
            ValueError: If email is missing.

        Returns:
            User: Newly created user instance.
        """
        if not email:
            raise ValueError("Users must have an email address.")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user: User = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        """Create a superuser.

        Args:
            email (str): Email for the superuser.
            password (Optional[str]): Raw password.
            extra_fields (Any): Additional fields.

        Raises:
            ValueError: If superuser flags are incorrect.

        Returns:
            User: Superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Main user model for the Korena system.

    Extends Django's AbstractBaseUser and PermissionsMixin.
    Email is used as the unique identifier for authentication.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)

    class Role(models.TextChoices):
        """Different roles available in the system."""

        TEACHER = "TEACHER", "Teacher"
        SCHOOL_ADMIN = "SCHOOL_ADMIN", "School admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super admin"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.TEACHER,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS: list[str] = []

    objects: UserManager = UserManager()

    def __str__(self) -> str:
        """Return the string representation of the user."""
        return self.email
