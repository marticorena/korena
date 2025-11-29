from functools import wraps
from typing import Any, Callable, TypeVar, cast

from graphql import GraphQLError

from apps.core.messages import ERROR_MESSAGES

ResolverFn = TypeVar("ResolverFn", bound=Callable[..., Any])


def verified_required(func: ResolverFn) -> ResolverFn:
    """Decorator to ensure the user is authenticated and verified.

    This decorator is meant to wrap GraphQL resolvers or mutation methods that
    should only be accessible to users who are both authenticated and have a
    verified account.

    Args:
        func: Resolver or mutation function to wrap.

    Raises:
        GraphQLError: If the user is anonymous or not verified.

    Returns:
        ResolverFn: Wrapped resolver that enforces verification.
    """

    @wraps(func)
    def wrapper(root: Any, info: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapper enforcing authentication and verification."""
        user = getattr(info.context, "user", None)

        if user is None or getattr(user, "is_anonymous", True):
            raise GraphQLError(ERROR_MESSAGES["auth.not_authenticated"])

        if not getattr(user, "is_verified", False):
            raise GraphQLError(ERROR_MESSAGES["auth.not_verified"])

        return func(root, info, *args, **kwargs)

    return cast(ResolverFn, wrapper)
