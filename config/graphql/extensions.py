from strawberry.exceptions import GraphQLError as StrawberryGraphQLError
from strawberry.extensions import QueryDepthLimiter, SchemaExtension

from apps.core.endpoints.utils import resolve_error_code
from config.graphql.messages import APOLLO_INTERNAL_ERROR


class ApolloErrorExtension(SchemaExtension):
    """Normalize errors to Apollo-style codes in `extensions.code`."""

    def on_operation(self):
        yield

        result = self.execution_context.result

        if not getattr(result, "errors", None):

            return

        formatted: list[StrawberryGraphQLError] = []

        for error in result.errors:
            original = getattr(error, "original_error", None)
            existing_ext = dict(error.extensions or {})

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


def get_default_extensions() -> list[SchemaExtension]:
    """Return default schema-level extensions for Strawberry."""

    return [
        QueryDepthLimiter(max_depth=10),
        ApolloErrorExtension(),
    ]
