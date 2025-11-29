import graphene
import graphql_jwt

from apps.accounts.schema.mutations import AccountMutations, GetToken
from apps.accounts.schema.queries import AccountsQuery
from apps.core.schema.queries import HealthQueries
from apps.documents.schema.mutations import DocumentMutations
from apps.documents.schema.queries import DocumentQueries
from apps.planning.schema.queries import PlanningQuery


class Query(
    AccountsQuery, PlanningQuery, DocumentQueries, HealthQueries, graphene.ObjectType
):
    """Root query combining all app-level queries."""

    pass


class Mutation(
    AccountMutations,
    DocumentMutations,
    graphene.ObjectType,
):
    """Root mutation combining all app-level mutations."""

    get_token = GetToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
