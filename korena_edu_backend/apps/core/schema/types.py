import graphene


class HealthStatusType(graphene.ObjectType):
    """GraphQL type representing application health."""

    status = graphene.String(required=True)
    db_ok = graphene.Boolean()
    redis_ok = graphene.Boolean()
    details = graphene.String()
