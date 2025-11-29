from typing import Any, List, Optional

from django.contrib.auth import get_user_model

import graphene

from apps.core.schema.types import FieldErrorType

User = get_user_model()


class BaseMutation(graphene.Mutation):
    """Base mutation with common response fields.

    All mutations inheriting from this class will expose:
    - success: Boolean flag indicating if the mutation was successful.
    - message: Human readable message summarizing the result.
    - errors: Optional list of structured field errors.
    """

    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(FieldErrorType)

    @classmethod
    def build_error_response(
        cls,
        message: str,
        errors: Optional[List[FieldErrorType]] = None,
    ) -> "BaseMutation":
        """Helper to build a standardized error response.

        Args:
            message: Summary message for the error.
            errors: Optional list of FieldErrorType instances.

        Returns:
            BaseMutation: An instance of the mutation with success=False.
        """
        if errors is None:
            errors = []

        return cls(
            success=False,
            message=message,
            errors=errors,
        )

    @classmethod
    def build_success_response(
        cls,
        message: str = "",
        **extra_fields: Any,
    ) -> "BaseMutation":
        """Helper to build a standardized success response.

        Args:
            message: Summary message for the success case.
            **extra_fields: Extra fields specific to the subclass mutation.

        Returns:
            BaseMutation: An instance of the mutation with success=True.
        """
        return cls(
            success=True,
            message=message,
            errors=[],
            **extra_fields,
        )

    def mutate(self, info: graphene.ResolveInfo, **kwargs: Any):
        """
        Must be overridden by each mutation class inheriting from BaseMutation.
        """
        pass
