from typing import Any

import graphene
from django.db import connection
from django_redis import get_redis_connection
from graphql import GraphQLResolveInfo


class HealthStatusType(graphene.ObjectType):
    """GraphQL type representing application health."""

    status = graphene.String(required=True)
    db_ok = graphene.Boolean()
    redis_ok = graphene.Boolean()
    details = graphene.String()


class HealthQueries(graphene.ObjectType):
    """GraphQL health and readiness probes."""

    healthz = graphene.Field(
        HealthStatusType,
        description="Liveness probe.",
    )
    readyz = graphene.Field(
        HealthStatusType,
        description="Readiness probe.",
    )

    def resolve_healthz(
        self, info: GraphQLResolveInfo, **kwargs: Any
    ) -> HealthStatusType:
        """Liveness probe: app is running."""
        return HealthStatusType(
            status="ok",
            db_ok=None,
            redis_ok=None,
            details="Service is alive",
        )

    def resolve_readyz(
        self, info: GraphQLResolveInfo, **kwargs: Any
    ) -> HealthStatusType:
        """Readiness: DB + Redis must be ready."""
        errors = []

        # DB check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_ok = True
        except Exception as exc:
            db_ok = False
            errors.append(f"DB error: {exc}")

        # Redis check
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            redis_ok = True
        except Exception as exc:
            redis_ok = False
            errors.append(f"Redis error: {exc}")

        overall_status = "ok" if db_ok and redis_ok else "error"

        return HealthStatusType(
            status=overall_status,
            db_ok=db_ok,
            redis_ok=redis_ok,
            details="; ".join(errors) or "All systems operational",
        )
