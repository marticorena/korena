import graphene
import graphql_jwt
from apps.accounts.schema import Query as AccountsQuery
from apps.documents.schema import DocumentMutations, DocumentQueries
from apps.health.schema import HealthQueries
from apps.planning.schema import PlanningQuery


class Query(
    AccountsQuery, PlanningQuery, DocumentQueries, HealthQueries, graphene.ObjectType
):
    """Root query combining all app-level queries."""

    pass


class Mutation(
    DocumentMutations,
    graphene.ObjectType,
):
    """Root mutation combining all app-level mutations."""

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
