from django.http import HttpRequest


class GraphQLContext:
    """Context object passed to all Strawberry resolvers.

    Contains the Django request so resolvers and permissions
    can access request.user, headers, cookies, etc.
    """

    def __init__(self, request: HttpRequest) -> None:
        self.request = request  # Django request object


def get_context(request: HttpRequest) -> GraphQLContext:
    """Factory used by Strawberry to create the per-request context.

    Args:
        request: The incoming Django HttpRequest.

    Returns:
        GraphQLContext: Context used in resolvers.
    """
    return GraphQLContext(request)
