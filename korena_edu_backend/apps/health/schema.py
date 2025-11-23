from typing import Any

import graphene
from django.db import connection
from django_redis import get_redis_connection
from graphql import GraphQLResolveInfo


class HealthStatusType(graphene.ObjectType):
    """GraphQL type representing the application's health status."""

    status = graphene.String(required=True)
    db_ok = graphene.Boolean()
    redis_ok = graphene.Boolean()


class HealthQueries(graphene.ObjectType):
    """GraphQL queries exposing health and readiness probes."""

    healthz = graphene.Field(
        HealthStatusType,
        description="Liveness probe: if this endpoint responds, the app is alive.",
    )
    readyz = graphene.Field(
        HealthStatusType,
        description="Readiness probe: checks database and Redis availability.",
    )

    def resolve_healthz(
        self,
        info: GraphQLResolveInfo,
        **kwargs: Any,
    ) -> HealthStatusType:
        """Return a basic liveness response.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver information.
            **kwargs (Any): Additional resolver arguments (unused).

        Returns:
            HealthStatusType: A minimal health status object.
        """

        return HealthStatusType(status="ok", db_ok=None, redis_ok=None)

    def resolve_readyz(
        self,
        info: GraphQLResolveInfo,
        **kwargs: Any,
    ) -> HealthStatusType:
        """Check readiness by verifying DB and Redis connectivity.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver information.
            **kwargs (Any): Additional resolver arguments (unused).

        Returns:
            HealthStatusType: A detailed readiness status.
        """
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_ok = True
        except Exception:
            db_ok = False

        # Check Redis connection
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

        status = "ok" if db_ok and redis_ok else "error"

        return HealthStatusType(status=status, db_ok=db_ok, redis_ok=redis_ok)
