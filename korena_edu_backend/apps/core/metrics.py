from contextlib import contextmanager
from time import perf_counter
from typing import Callable

from django.http import HttpRequest, HttpResponse

from prometheus_client import Counter, Histogram, generate_latest

# DOCUMENT METRICS
documents_created_total = Counter(
    "documents_created_total",
    "Total number of documents created",
)

document_versions_uploaded_total = Counter(
    "document_versions_uploaded_total",
    "Total number of document versions uploaded",
)

documents_by_type_total = Counter(
    "documents_by_type_total",
    "Documents created by type",
    ["type"],
)

documents_by_level_total = Counter(
    "documents_by_level_total",
    "Documents created by level",
    ["level"],
)

document_upload_duration_seconds = Histogram(
    "document_upload_duration_seconds",
    "Time spent processing document uploads",
)


# USER / AUTH METRICS
logins_total = Counter(
    "logins_total",
    "User login attempts",
    ["status"],  # success / failed
)

users_by_role_total = Counter(
    "users_by_role_total",
    "Users created by role",
    ["role"],  # TEACHER / SCHOOL_ADMIN / SUPER_ADMIN
)

emails_sent_total = Counter(
    "emails_sent_total",
    "Emails sent by system",
    ["status"],  # sent / failed
)


# PLANNING METRICS
planning_sheets_created_total = Counter(
    "planning_sheets_created_total",
    "Total number of planning sheets created",
    ["level"],  # TEACHER / CLASSROOM
)

planning_rows_added_total = Counter(
    "planning_rows_added_total",
    "Total number of rows added to planning sheets",
)


# INFRA / CELERY METRICS
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Celery tasks executed",
    ["task_name", "status"],  # success / failed
)

db_errors_total = Counter(
    "db_errors_total",
    "Database operation failures",
)

permission_denied_total = Counter(
    "permission_denied_total",
    "Access attempts denied due to missing permissions",
)


# GRAPHQL PERFORMANCE METRICS
graphql_request_duration_seconds = Histogram(
    "graphql_request_duration_seconds",
    "GraphQL request duration in seconds",
    ["operation"],
)


# AI METRICS (future)
ai_summaries_generated_total = Counter(
    "ai_summaries_generated_total",
    "Total number of AI-generated document summaries",
)

ai_recommendation_queries_total = Counter(
    "ai_recommendation_queries_total",
    "Number of AI recommendation queries",
    ["source"],  # requirement_stage / final_recommendation
)


@contextmanager
def track_graphql_operation(operation_name: str):
    """Context manager to track GraphQL operation duration.

    Args:
        operation_name: Logical name of the GraphQL operation.
    """
    start = perf_counter()
    try:
        yield
    finally:
        duration = perf_counter() - start
        graphql_request_duration_seconds.labels(
            operation=operation_name,
        ).observe(duration)


def track_celery_task(task_name: str) -> Callable:
    """Decorator to track Celery task execution success/failure."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(task_name=task_name, status="success").inc()

                return result
            except Exception:
                celery_tasks_total.labels(task_name=task_name, status="failed").inc()

                raise

        return wrapper

    return decorator


def metrics_view(_request: HttpRequest) -> HttpResponse:
    """Expose Prometheus metrics endpoint."""
    data = generate_latest()

    return HttpResponse(
        data,
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )
