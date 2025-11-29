from typing import Optional

from django.contrib.auth import authenticate, get_user_model

import graphene
from graphql import GraphQLError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)

from apps.accounts.schema.types import UserType  # Asumiendo que ya lo tienes
from apps.core.messages import ERROR_MESSAGES

User = get_user_model()


class TokenPairType(graphene.ObjectType):
    """GraphQL type wrapping access and refresh tokens."""

    access = graphene.String(required=True)
    refresh = graphene.String(required=True)


class ObtainJSONWebToken(graphene.Mutation):
    """Authenticate user and return a SimpleJWT token pair."""

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.Field(TokenPairType)
    user = graphene.Field(UserType)

    @classmethod
    def mutate(
        cls,
        root: Optional[object],
        info: graphene.ResolveInfo,
        email: str,
        password: str,
        **kwargs: object,
    ) -> "ObtainJSONWebToken":
        """Validate credentials and issue JWT access/refresh tokens.

        Args:
            root: Root resolver (unused).
            info: GraphQL resolve info.
            email: User email.
            password: User password.
            **kwargs: Extra args.

        Raises:
            GraphQLError: If credentials are invalid or user is inactive.

        Returns:
            ObtainJSONWebToken: Mutation payload with token pair and user.
        """
        user = authenticate(request=info.context, email=email, password=password)

        if user is None:
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_credentials"])

        if not user.is_active:
            raise GraphQLError(ERROR_MESSAGES["auth.user_not_found"])

        serializer = TokenObtainPairSerializer(
            data={"email": email, "password": password},
            context={"request": info.context},
        )
        if not serializer.is_valid():
            raise GraphQLError(ERROR_MESSAGES["auth.invalid_credentials"])

        token_data = serializer.validated_data

        token_pair = TokenPairType(
            access=str(token_data["access"]),
            refresh=str(token_data["refresh"]),
        )

        return ObtainJSONWebToken(token=token_pair, user=user)


class RefreshJSONWebToken(graphene.Mutation):
    """Refresh the access token using a refresh token."""

    class Arguments:
        refresh = graphene.String(required=True)

    token = graphene.Field(TokenPairType)

    @classmethod
    def mutate(
        cls,
        root: Optional[object],
        info: graphene.ResolveInfo,
        refresh: str,
        **kwargs: object,
    ) -> "RefreshJSONWebToken":
        """Refresh access token.

        Args:
            root: Root resolver.
            info: GraphQL resolve info.
            refresh: Refresh token string.
            **kwargs: Extra args.

        Raises:
            GraphQLError: If token is invalid or expired.

        Returns:
            RefreshJSONWebToken: Payload with new token pair.
        """
        serializer = TokenRefreshSerializer(data={"refresh": refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise GraphQLError(ERROR_MESSAGES["auth.token_invalid"])

        data = serializer.validated_data

        token_pair = TokenPairType(
            access=str(data["access"]),
            refresh=str(refresh),
        )

        return RefreshJSONWebToken(token=token_pair)


class VerifyJSONWebToken(graphene.Mutation):
    """Verify that a token is valid."""

    class Arguments:
        token = graphene.String(required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate(
        cls,
        root: Optional[object],
        info: graphene.ResolveInfo,
        token: str,
        **kwargs: object,
    ) -> "VerifyJSONWebToken":
        """Verify a given JWT token.

        Args:
            root: Root resolver.
            info: GraphQL resolve info.
            token: Token to verify.
            **kwargs: Extra args.

        Raises:
            GraphQLError: If token is invalid.

        Returns:
            VerifyJSONWebToken: Payload with ok=True if valid.
        """
        serializer = TokenVerifySerializer(data={"token": token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise GraphQLError(ERROR_MESSAGES["auth.token_invalid"])

        return VerifyJSONWebToken(ok=True)
