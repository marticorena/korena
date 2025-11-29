from typing import Any

from django.contrib.auth import authenticate, get_user_model

import graphene
from graphql import GraphQLError
import graphql_jwt
from graphql_jwt.decorators import login_required

from apps.accounts.forms import ChangePasswordForm, RegisterForm, UpdateUserForm
from apps.accounts.schema.types import GetTokenType
from apps.accounts.utils import generate_token_and_email, verify_token
from apps.core.messages import ERROR_MESSAGES
from apps.core.schema.utils import build_form_errors
from apps.notifications.tasks import send_email_task

User = get_user_model()


class GetToken(graphene.Mutation):
    """
    Custom login mutation that replaces graphql_jwt.ObtainJSONWebToken.
    Returns the same structure, but with custom error codes/messages.
    """

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = GetTokenType

    def mutate(
        self, info: graphene.ResolveInfo, email: str, password: str
    ) -> GetTokenType:
        """Authenticate user and return JWT + refresh token."""
        user = authenticate(email=email, password=password)

        if not user:
            # Custom error message
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_credentials"])

        if not user.is_active:
            raise GraphQLError(ERROR_MESSAGES["auth.not_authenticated"])

        # Generate JWT tokens using graphql_jwt util
        payload = graphql_jwt.utils.jwt_payload(user)
        token = graphql_jwt.utils.jwt_encode(payload)

        # Refresh token (graphene-jwt internal)
        refresh_token_obj = (
            graphql_jwt.refresh_token.models.RefreshToken.objects.create(user=user)
        )
        refresh_token = refresh_token_obj.get_token()

        # Return data matching EXACT graphql-jwt shape
        return GetTokenType(
            token=token,
            refreshToken=refresh_token,
        )


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

    email = graphene.String()

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
        """Update the user's password.

        Raises:
            GraphQLError: If validation fails.
        """
        user = info.context.user

        if not user.check_password(current_password):
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_current_password"])

        form = ChangePasswordForm(
            {
                "password1": password1,
                "password2": password2,
            }
        )

        if not form.is_valid():
            errors = build_form_errors(form)

            raise GraphQLError(
                ERROR_MESSAGES["validation.error"],
                extensions={"fields": errors},
            )

        new_password = form.cleaned_data["password1"]
        user.set_password(new_password)
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
