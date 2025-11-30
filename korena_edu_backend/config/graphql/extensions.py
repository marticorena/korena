from typing import Any, List

from strawberry.exceptions import GraphQLError as StrawberryGraphQLError
from strawberry.extensions import FieldExtension, QueryDepthLimiter, SchemaExtension
from strawberry.types import ExecutionContext, Info

from apps.core.endpoints.utils import resolve_error_code
from apps.core.metrics import track_graphql_operation
from config.graphql.messages import (
    APOLLO_INTERNAL_ERROR,
)


class ApolloErrorExtension(SchemaExtension):
    """Normalize errors to Apollo-style codes in `extensions.code`.

    Uses the same centralized logic as REST helpers, so error messages
    and codes stay consistent across the whole backend.
    """

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
            existing_ext = dict(error.extensions or {})

            # Centralized resolver: explicit code → message map → exception map.
            resolved_code = resolve_error_code(
                message=error.message or "",
                original_error=original,
                code=existing_ext.get("code"),
            )

            formatted.append(
                StrawberryGraphQLError(
                    message=error.message or APOLLO_INTERNAL_ERROR,
                    nodes=error.nodes,
                    source=error.source,
                    positions=error.positions,
                    path=error.path,
                    original_error=original,
                    extensions={**existing_ext, "code": resolved_code},
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
    """Return default schema-level extensions for Strawberry.

    Returns:
        list[SchemaExtension]: Extensions to be applied to the schema.
    """
    return [
        QueryDepthLimiter(max_depth=10),
        ApolloErrorExtension(),
    ]
