import graphene


class HealthStatusType(graphene.ObjectType):
    """GraphQL type representing application health."""

    status = graphene.String(required=True)
    db_ok = graphene.Boolean()
    redis_ok = graphene.Boolean()
    details = graphene.String()


class FieldErrorType(graphene.ObjectType):
    """GraphQL type for field-level validation errors."""

    field = graphene.String()
    message = graphene.String()
    code = graphene.String()
