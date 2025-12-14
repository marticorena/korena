import strawberry

from apps.accounts.graphql.mutations import AccountMutations
from apps.accounts.graphql.queries import AccountsQuery
from apps.core.graphql.queries import HealthQueries
from apps.documents.graphql.mutations import DocumentMutations
from apps.documents.graphql.queries import DocumentQueries
from config.graphql.extensions import get_default_extensions


@strawberry.type
class Query(AccountsQuery, DocumentQueries, HealthQueries):
    """Root query combining all app-level queries."""

    pass


@strawberry.type
class Mutation(AccountMutations, DocumentMutations):
    """Root mutation combining all app-level mutations."""

    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=get_default_extensions(),
)
