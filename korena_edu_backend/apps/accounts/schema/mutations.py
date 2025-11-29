from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

import graphene
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from apps.accounts.forms import RegisterForm, UpdateUserForm
from apps.accounts.schema.types import UserType
from apps.accounts.utils import generate_token_and_email, verify_token
from apps.accounts.validators import password_validator
from apps.core.messages import (
    CURRENT_PASSWORD_INCORRECT,
    PASSWORDS_DONT_MATCH,
    USER_NOT_FOUND,
    VALIDATION_ERROR,
    VERIFICATION_TOKEN_INVALID_OR_EXPIRED,
)
from apps.core.schema.utils import build_form_errors
from apps.notifications.tasks import send_email_task

User = get_user_model()


class UserDataArguments:
    """Common arguments for user-related mutations."""

    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)


class RegisterUser(graphene.Mutation):
    """Registers a user and sends verification email."""

    class Arguments(UserDataArguments):
        email = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    token = graphene.String()

    def mutate(self, info: graphene.ResolveInfo, **kwargs: Any) -> "RegisterUser":
        """Register a new user.

        Raises:
            GraphQLError: If validation fails.
        """
        form = RegisterForm(kwargs)

        if not form.is_valid():
            errors = build_form_errors(form)
            raise GraphQLError(
                VALIDATION_ERROR,
                extensions={"fields": errors},
            )

        user = User.objects.create_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            is_active=False,
        )

        token, email_log = generate_token_and_email(user)
        send_email_task.delay(email_log.id)

        return RegisterUser(token=token)


class VerifyEmail(graphene.Mutation):
    """Verifies email using token."""

    class Arguments:
        token = graphene.String(required=True)

    email = graphene.String()

    def mutate(self, info: graphene.ResolveInfo, token: str) -> "VerifyEmail":
        """Verify email and activate user.

        Raises:
            GraphQLError: If token invalid or user missing.
        """
        email = verify_token(token)

        if not email:
            raise GraphQLError(VERIFICATION_TOKEN_INVALID_OR_EXPIRED)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError(USER_NOT_FOUND)

        user.is_verified = True
        user.is_active = True
        user.save()

        return VerifyEmail(email=email)


class UpdateUser(graphene.Mutation):
    """Updates user profile information."""

    class Arguments(UserDataArguments):
        pass

    email = graphene.Field(UserType)

    @login_required
    def mutate(self, info: graphene.ResolveInfo, **kwargs: Any) -> "UpdateUser":
        """Update authenticated user.

        Raises:
            GraphQLError: If validation fails.
        """
        user = info.context.user

        form = UpdateUserForm(kwargs, instance=user)

        if not form.is_valid():
            errors = build_form_errors(form)
            raise GraphQLError(
                VALIDATION_ERROR,
                extensions={"fields": errors},
            )

        updated_user = form.save()

        return UpdateUser(email=updated_user.email)


class ChangePassword(graphene.Mutation):
    """Changes the user's password."""

    class Arguments:
        current_password = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    email = graphene.String()

    @login_required
    def mutate(
        self,
        info: graphene.ResolveInfo,
        current_password: str,
        password1: str,
        password2: str,
    ) -> "ChangePassword":
        """Change authenticated user's password.

        Raises:
            GraphQLError: If validation fails.
        """
        user = info.context.user

        if not user.check_password(current_password):
            raise GraphQLError(CURRENT_PASSWORD_INCORRECT)

        if password1 != password2:
            raise GraphQLError(PASSWORDS_DONT_MATCH)

        try:
            password_validator(password1)
        except ValidationError as e:
            message = e.messages[0] if e.messages else str(e)
            raise GraphQLError(message)

        user.set_password(password1)
        user.save()

        return ChangePassword(email=user.email)


class DeleteAccount(graphene.Mutation):
    """Deletes the authenticated user's account."""

    class Arguments:
        current_password = graphene.String(required=True)

    email = graphene.String()

    @login_required
    def mutate(
        self,
        info: graphene.ResolveInfo,
        current_password: str,
    ) -> "DeleteAccount":
        """Delete user account.

        Raises:
            GraphQLError: If password incorrect.
        """
        user = info.context.user

        if not user.check_password(current_password):
            raise GraphQLError(CURRENT_PASSWORD_INCORRECT)

        deleted_email = user.email
        user.delete()

        return DeleteAccount(email=deleted_email)


class AccountMutations(graphene.ObjectType):
    """Root mutation group."""

    register_user = RegisterUser.Field()
    verify_email = VerifyEmail.Field()
    update_user = UpdateUser.Field()
    change_password = ChangePassword.Field()
    delete_account = DeleteAccount.Field()
