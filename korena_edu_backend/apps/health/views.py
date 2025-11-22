from django.db import connection
from django.http import JsonResponse
from django_redis import get_redis_connection


def healthz(request):
    """
    Liveness probe: if this responds 200, app is alive.
    """
    return JsonResponse({"status": "ok"})


def readyz(request):
    """
    Readiness probe: checks DB and Redis.
    """
    # Check DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        db_ok = True
    except Exception:
        db_ok = False

    # Check Redis
    try:
        r = get_redis_connection("default")
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    status_code = 200 if db_ok and redis_ok else 503

    return JsonResponse(
        {
            "status": "ok" if status_code == 200 else "error",
            "db_ok": db_ok,
            "redis_ok": redis_ok,
        },
        status=status_code,
    )
