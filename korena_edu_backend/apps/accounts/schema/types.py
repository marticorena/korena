from graphene_django import DjangoObjectType

from apps.accounts.models import User


class UserType(DjangoObjectType):
    """GraphQL type representing the User model."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role")
