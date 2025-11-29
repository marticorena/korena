from django.contrib.auth import authenticate, get_user_model

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
import strawberry
from strawberry.types import Info

from apps.accounts.forms import (
    ChangePasswordForm,
    RegisterForm,
    UpdateUserForm,
)
from apps.accounts.graphql.types import TokenPair, UserType
from apps.accounts.utils import generate_token_and_email, verify_token
from apps.core.graphql.permissions import IsAuthenticated, IsVerified
from apps.core.graphql.utils import build_form_errors
from apps.core.messages import ERROR_MESSAGES
from apps.notifications.tasks import send_email_task

User = get_user_model()


@strawberry.type
class AuthMutations:
    """Mutations for authentication using SimpleJWT."""

    @strawberry.mutation
    def token_auth(self, info: Info, email: str, password: str) -> TokenPair:
        """Authenticate user and return an access + refresh token pair."""
        user = authenticate(email=email, password=password)

        if not user:
            raise Exception(ERROR_MESSAGES["auth.invalid_credentials"])

        if not user.is_active:
            raise Exception(ERROR_MESSAGES["auth.not_authenticated"])

        if not getattr(user, "is_verified", False):
            raise Exception(ERROR_MESSAGES["auth.not_verified"])

        serializer = TokenObtainPairSerializer(
            data={"email": email, "password": password},
            context={"request": info.context.request},
        )

        if not serializer.is_valid():
            raise Exception(ERROR_MESSAGES["auth.invalid_credentials"])

        tokens = serializer.validated_data

        return TokenPair(access=str(tokens["access"]), refresh=str(tokens["refresh"]))

    @strawberry.mutation
    def refresh_token(self, info: Info, refresh: str) -> TokenPair:
        """Refresh the access token."""
        serializer = TokenRefreshSerializer(data={"refresh": refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise Exception(ERROR_MESSAGES["auth.token_invalid"])

        data = serializer.validated_data
        new_access = str(data["access"])

        return TokenPair(access=new_access, refresh=refresh)

    @strawberry.mutation
    def verify_token(self, info: Info, token: str) -> bool:
        """Verify the validity of a JWT token."""
        serializer = TokenVerifySerializer(data={"token": token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise Exception(ERROR_MESSAGES["auth.token_invalid"])

        return True


@strawberry.type
class RegistrationMutations:
    """Registration and email verification."""

    @strawberry.mutation
    def register_user(
        self,
        info: Info,
        email: str,
        password1: str,
        password2: str,
        first_name: str,
        last_name: str,
    ) -> str:
        """Register a user and send verification email."""
        form = RegisterForm(
            {
                "email": email,
                "password1": password1,
                "password2": password2,
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        if not form.is_valid():
            errors = build_form_errors(form)
            raise Exception(
                ERROR_MESSAGES["validation.error"],
                {"fields": errors},
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

        return token

    @strawberry.mutation
    def verify_email(self, info: Info, token: str) -> str:
        """Verify user account using email token."""
        email = verify_token(token)

        if not email:
            raise Exception(ERROR_MESSAGES["auth.token_invalid"])

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise Exception(ERROR_MESSAGES["auth.user_not_found"])

        user.is_verified = True
        user.is_active = True
        user.save()

        return email


@strawberry.type
class ProfileMutations:
    """Mutations for managing user profile."""

    @strawberry.mutation(permission_classes=[IsAuthenticated, IsVerified])
    def update_user(
        self,
        info: Info,
        first_name: str,
        last_name: str,
    ) -> UserType:
        """Update the authenticated user's profile."""
        user = info.context.request.user

        form = UpdateUserForm(
            {"first_name": first_name, "last_name": last_name},
            instance=user,
        )

        if not form.is_valid():
            errors = build_form_errors(form)
            raise Exception(
                ERROR_MESSAGES["validation.error"],
                {"fields": errors},
            )

        updated_user = form.save()

        return updated_user

    @strawberry.mutation(permission_classes=[IsAuthenticated, IsVerified])
    def change_password(
        self,
        info: Info,
        current_password: str,
        password1: str,
        password2: str,
    ) -> str:
        """Change password for authenticated user."""
        user = info.context.request.user

        if not user.check_password(current_password):
            raise Exception(ERROR_MESSAGES["auth.invalid_current_password"])

        form = ChangePasswordForm({"password1": password1, "password2": password2})

        if not form.is_valid():
            errors = build_form_errors(form)
            raise Exception(
                ERROR_MESSAGES["validation.error"],
                {"fields": errors},
            )

        new_password = form.cleaned_data["password1"]
        user.set_password(new_password)
        user.save()

        return user.email

    @strawberry.mutation(permission_classes=[IsAuthenticated, IsVerified])
    def delete_account(
        self,
        info: Info,
        current_password: str,
    ) -> str:
        """Permanently delete the user account."""
        user = info.context.request.user

        if not user.check_password(current_password):
            raise Exception(ERROR_MESSAGES["auth.invalid_current_password"])

        deleted_email = user.email
        user.delete()

        return deleted_email


@strawberry.type
class AccountMutations:
    """Root mutation entry for accounts."""

    auth: AuthMutations = strawberry.field(default_factory=AuthMutations)
    registration: RegistrationMutations = strawberry.field(
        default_factory=RegistrationMutations
    )
    profile: ProfileMutations = strawberry.field(default_factory=ProfileMutations)
