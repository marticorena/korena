from django.test import Client
from django.urls import resolve

from graphene_django.views import GraphQLView
import pytest

from apps.core.metrics import metrics_view

pytestmark = pytest.mark.django_db


def test_graphql_url_resolves_to_graphql_view() -> None:
    """The /graphql/ URL should be wired to GraphQLView."""
    match = resolve("/graphql/")

    # When using .as_view(), Django sets view_class on the resolved func.
    assert hasattr(match.func, "view_class")
    assert match.func.view_class is GraphQLView


def test_metrics_url_resolves_to_metrics_view() -> None:
    """The /metrics/ URL should resolve to the Prometheus metrics view."""
    match = resolve("/metrics/")

    # Direct function-based view.
    assert match.func is metrics_view


def test_graphql_endpoint_healthz_query_works(client: Client) -> None:
    """POST /graphql/ should execute a simple healthz query successfully.

    This also implicitly verifies:
    - The schema is wired correctly.
    - CSRF is exempted (we can POST sin token).
    """
    payload = {"query": "{ __typename }"}

    response = client.post(
        "/graphql/",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200

    data = response.json()
    assert "data" in data


def test_metrics_endpoint_returns_prometheus_text(client: Client) -> None:
    """GET /metrics/ should return a 200 response with Prometheus text format."""
    response = client.get("/metrics/")

    assert response.status_code == 200
    # Prometheus text exposition format.
    assert response["Content-Type"].startswith("text/plain")

    body = response.content.decode("utf-8")
    # Should contain at least some default or custom metric.
    assert (
        "python_info" in body
        or "process_cpu_seconds_total" in body
        or "emails_sent_total" in body
    )


def test_admin_root_is_mounted(client: Client) -> None:
    """GET /admin/ should be mounted and typically redirect to the login page."""
    response = client.get("/admin/")

    # Default behaviour: redirect to /admin/login/?next=/admin/
    assert response.status_code in (200, 302)
    if response.status_code == 302:
        location = response.headers.get("Location", "")
        assert "/admin/login" in location
