from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

import graphene
from graphql_jwt.shortcuts import get_token
from premailer import transform

from apps.accounts.forms import RegisterForm
from apps.accounts.utils import generate_verification_token, verify_token
from apps.core.messages import (
    EMAIL_ALREADY_REGISTERED,
    EMAIL_VERIFIED,
    USER_NOT_FOUND,
    VERIFICATION_TOKEN_INVALID_OR_EXPIRED,
)
from apps.notifications.models import EmailLog
from apps.notifications.tasks import send_email_task

User = get_user_model()


class UserDataArguments:
    """Common arguments for user-related mutations.

    Provides fields for basic user information that is used across multiple mutations.
    """

    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)


class RegisterUser(graphene.Mutation):
    """Mutation to register a new user.

    Creates a new user account, sends a verification email, and returns a token
    for email verification.
    """

    success = graphene.Boolean()
    message = graphene.String()

    class Arguments(UserDataArguments):
        """Arguments for the RegisterUser mutation."""

        email = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    @staticmethod
    def _generate_token_and_email(user):
        token = generate_verification_token(user.email)
        encoded_token = quote(token)

        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={encoded_token}"
        html_message = render_to_string(
            "users/email_verification.html",
            {"user": user, "verify_url": verify_url},
        )
        html_message = transform(html_message)
        plain_message = f"Hola {user.first_name}, verifica tu cuenta aquí: {verify_url}"
        subject = "Korena - Verifica tu cuenta"
        email = EmailLog.objects.create(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=user.email,
            user=user,
            subject=subject,
            plain_message=plain_message,
            html_message=html_message,
        )

        return token, email

    def mutate(self, info, **kwargs) -> "RegisterUser":
        """Register a new user with the provided information.

        Args:
            info: GraphQL execution info.
            **kwargs: User registration data including name, email, password, etc.

        Returns:
            RegisterUser: Mutation result with success status and message.
        """
        form = RegisterForm(kwargs)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                is_active=False,
            )
            token, email_log = self._generate_token_and_email(user)

            send_email_task.delay(email_log.id)

            return RegisterUser(success=True, message=token)
        else:
            errors = form.errors.get_json_data()
            messages = []

            for field, field_errors in errors.items():
                for err in field_errors:
                    msg = err["message"]
                    if field == "email" and "already exists" in msg.lower():
                        msg = EMAIL_ALREADY_REGISTERED
                    messages.append(msg)

            return RegisterUser(success=False, message="\n".join(messages))


class VerifyEmail(graphene.Mutation):
    """Mutation to verify a user's email address using a token.

    Validates the token, activates the user account, and returns a JWT token
    for authentication if successful.
    """

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()

    class Arguments:
        """Arguments for the VerifyEmail mutation."""

        token = graphene.String(required=True)

    def mutate(self, info, token) -> "VerifyEmail":
        """Verify a user's email address using a token.

        Args:
            info: GraphQL execution info.
            token: The verification token sent to the user's email.

        Returns:
            VerifyEmail: Mutation result with success status, message, and JWT token.
        """
        email = verify_token(token)
        if email:
            try:
                user = User.objects.get(email=email)
                user.is_verified = True
                user.is_active = True
                user.save()
                jwt_token = get_token(user)

                return VerifyEmail(
                    success=True,
                    message=EMAIL_VERIFIED,
                    token=jwt_token,
                )
            except User.DoesNotExist:

                return VerifyEmail(success=False, message=USER_NOT_FOUND, token=None)
        else:

            return VerifyEmail(
                success=False, message=VERIFICATION_TOKEN_INVALID_OR_EXPIRED, token=None
            )
