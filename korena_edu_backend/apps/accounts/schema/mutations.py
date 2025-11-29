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
from apps.core.messages import ERROR_MESSAGES
from apps.core.schema.utils import build_form_errors
from apps.notifications.tasks import send_email_task

User = get_user_model()


class UserDataArguments:
    """Common input arguments for user-related mutations."""

    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)


class RegisterUser(graphene.Mutation):
    """Creates a new user and sends a verification email."""

    class Arguments(UserDataArguments):
        email = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    token = graphene.String()

    def mutate(self, info: graphene.ResolveInfo, **kwargs: Any) -> "RegisterUser":
        """Register a user and trigger a verification email.

        Raises:
            GraphQLError: If validation fails.
        """
        form = RegisterForm(kwargs)

        if not form.is_valid():
            errors = build_form_errors(form)
            raise GraphQLError(
                ERROR_MESSAGES["validation.error"],
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
    """Verifies the user's email using a token."""

    class Arguments:
        token = graphene.String(required=True)

    email = graphene.String()

    def mutate(self, info: graphene.ResolveInfo, token: str) -> "VerifyEmail":
        """Activate user account if the token is valid.

        Raises:
            GraphQLError: If token is invalid or user not found.
        """
        email = verify_token(token)

        if not email:
            raise GraphQLError(ERROR_MESSAGES["auth.token_invalid"])

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError(ERROR_MESSAGES["auth.user_not_found"])

        user.is_verified = True
        user.is_active = True
        user.save()

        return VerifyEmail(email=email)


class UpdateUser(graphene.Mutation):
    """Updates the authenticated user's profile information."""

    class Arguments(UserDataArguments):
        pass

    user = graphene.Field(UserType)

    @login_required
    def mutate(self, info: graphene.ResolveInfo, **kwargs: Any) -> "UpdateUser":
        """Update the user's first and last name.

        Raises:
            GraphQLError: If validation fails.
        """
        user = info.context.user
        form = UpdateUserForm(kwargs, instance=user)

        if not form.is_valid():
            errors = build_form_errors(form)
            raise GraphQLError(
                ERROR_MESSAGES["validation.error"],
                extensions={"fields": errors},
            )

        updated_user = form.save()

        return UpdateUser(user=updated_user)


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
        """Update the user's password.

        Raises:
            GraphQLError: If validation fails.
        """
        user = info.context.user

        if not user.check_password(current_password):
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_current_password"])

        if password1 != password2:
            raise GraphQLError(ERROR_MESSAGES["auth.password_mismatch"])

        try:
            password_validator(password1)
        except ValidationError as e:
            # Map validator error code to a centralized message if available.
            raw_message = e.messages[0] if e.messages else str(e)
            code = getattr(e, "code", "invalid")
            field_code_key = f"password1.{code}"
            message = ERROR_MESSAGES.get(
                field_code_key,
                ERROR_MESSAGES.get(code, raw_message),
            )
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
        """Permanently delete the user account.

        Raises:
            GraphQLError: If password is incorrect.
        """
        user = info.context.user

        if not user.check_password(current_password):
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_current_password"])

        deleted_email = user.email
        user.delete()

        return DeleteAccount(email=deleted_email)


class AccountMutations(graphene.ObjectType):
    """Root mutation group for account-related operations."""

    register_user = RegisterUser.Field()
    verify_email = VerifyEmail.Field()
    update_user = UpdateUser.Field()
    change_password = ChangePassword.Field()
    delete_account = DeleteAccount.Field()
