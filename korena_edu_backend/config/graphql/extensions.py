from typing import Any, List

from strawberry.exceptions import GraphQLError as StrawberryGraphQLError
from strawberry.extensions import FieldExtension, QueryDepthLimiter, SchemaExtension
from strawberry.types import ExecutionContext, Info

from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import track_graphql_operation
from config.graphql.messages import (
    APOLLO_INTERNAL_ERROR,
)


class ApolloErrorExtension(SchemaExtension):
    """Normalize errors to Apollo-style codes in `extensions.code`."""

    def on_operation(self):
        """Run after operation and rewrite errors if needed."""
        yield

        execution_context: ExecutionContext = self.execution_context
        result = execution_context.result

        if not getattr(result, "errors", None):
            return

        formatted: List[StrawberryGraphQLError] = []

        for error in result.errors:
            original = getattr(error, "original_error", None)
            existing_ext = error.extensions or {}

            code = existing_ext.get("code")

            if code is None:
                if error.message == ERROR_MESSAGES["auth.not_authenticated"]:
                    code = "UNAUTHENTICATED"
                elif error.message == ERROR_MESSAGES["auth.not_verified"]:
                    code = "FORBIDDEN"
                elif isinstance(original, PermissionError):
                    code = "FORBIDDEN"
                elif isinstance(original, ValueError):
                    code = "BAD_USER_INPUT"
                else:
                    code = "INTERNAL_SERVER_ERROR"

            formatted.append(
                StrawberryGraphQLError(
                    message=error.message or APOLLO_INTERNAL_ERROR,
                    nodes=error.nodes,
                    source=error.source,
                    positions=error.positions,
                    path=error.path,
                    original_error=original,
                    extensions={**existing_ext, "code": code},
                )
            )

        result.errors = formatted


class GraphQLOperationMetricsExtension(FieldExtension):
    """Field-level extension to track operation duration with Prometheus."""

    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name

    def resolve(self, next_, source, info: Info, *args: Any, **kwargs: Any):
        with track_graphql_operation(self.operation_name):
            return next_(source, info, *args, **kwargs)


def get_default_extensions() -> list[SchemaExtension]:
    return [
        QueryDepthLimiter(max_depth=10),
        ApolloErrorExtension(),
    ]
