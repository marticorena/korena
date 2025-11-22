import graphene

from apps.accounts.schema import Query as AccountsQuery
from apps.planning.graphql_schema import PlanningQuery


class Query(AccountsQuery, PlanningQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
