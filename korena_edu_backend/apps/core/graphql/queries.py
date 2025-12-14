from django.db import connection

from django_redis import get_redis_connection
import strawberry
from strawberry.types import Info

from apps.core.graphql.types import HealthStatusType


def _check_db() -> tuple[bool, str | None]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return True, None
    except Exception:
        return False, "DB error"


def _check_redis() -> tuple[bool, str | None]:
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()

        return True, None
    except Exception:
        return False, "Redis error"


@strawberry.type
class HealthQueries:
    """GraphQL health and readiness probes."""

    @strawberry.field(description="Liveness probe.")
    def healthz(self, info: Info) -> HealthStatusType:
        """Liveness probe: app is running."""

        return HealthStatusType(
            status="ok",
            db_ok=None,
            redis_ok=None,
            details="Service is alive",
        )

    @strawberry.field(description="Readiness probe.")
    def readyz(self, info: Info) -> HealthStatusType:
        """Readiness: DB + Redis must be ready."""
        errors: list[str] = []

        db_ok, db_error = _check_db()
        if db_error:
            errors.append(db_error)

        redis_ok, redis_error = _check_redis()
        if redis_error:
            errors.append(redis_error)

        overall_status = "ok" if db_ok and redis_ok else "error"

        return HealthStatusType(
            status=overall_status,
            db_ok=db_ok,
            redis_ok=redis_ok,
            details="; ".join(errors) or "All systems operational",
        )
