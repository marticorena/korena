from typing import Any, List

from graphql import GraphQLError
from graphql.language import DocumentNode, FieldNode
from graphql.language.visitor import Visitor, visit
from strawberry.exceptions import GraphQLError as StrawberryGraphQLError
from strawberry.extensions import FieldExtension, QueryDepthLimiter, SchemaExtension
from strawberry.types import ExecutionContext, Info

from apps.core.graphql.messages import (
    APOLLO_INTERNAL_ERROR,
    QUERY_TOO_COMPLEX,
)
from apps.core.metrics import track_graphql_operation


class _FieldCountingVisitor(Visitor):
    def __init__(self) -> None:
        self.cost = 0

    def enter_field(self, node: FieldNode, *args: Any) -> None:
        self.cost += 1


class SimpleCostAnalyzer(SchemaExtension):
    """Naive cost analyzer based on number of requested fields."""

    max_cost: int = 300

    def on_validate(self):
        """Validate query complexity before execution."""
        execution_context: ExecutionContext = self.execution_context
        document: DocumentNode | None = getattr(execution_context, "document", None)

        if not document:
            yield

            return

        visitor = _FieldCountingVisitor()
        visit(document, visitor)

        if visitor.cost > self.max_cost:
            raise GraphQLError(
                QUERY_TOO_COMPLEX,
                extensions={
                    "code": "QUERY_TOO_COMPLEX",
                    "cost": visitor.cost,
                    "maxCost": self.max_cost,
                },
            )

        yield


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

            code = existing_ext.get("code") or "INTERNAL_SERVER_ERROR"

            if isinstance(original, PermissionError):
                code = "FORBIDDEN"
            elif isinstance(original, ValueError):
                code = "BAD_USER_INPUT"
            elif original is None:
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
        SimpleCostAnalyzer(),
        ApolloErrorExtension(),
    ]
