from django.test import Client
from django.urls import resolve

import pytest
from strawberry.django.views import GraphQLView

from apps.core.metrics import metrics_view

pytestmark = pytest.mark.django_db


def test_graphql_url_resolves_to_graphql_view() -> None:
    """The /graphql/ URL should resolve to Strawberry's GraphQLView."""
    match = resolve("/graphql/")

    # Django sets view_class when using .as_view()
    assert hasattr(match.func, "view_class")
    assert match.func.view_class is GraphQLView


def test_metrics_url_resolves_to_metrics_view() -> None:
    """The /metrics/ URL should resolve to the Prometheus metrics endpoint."""
    match = resolve("/metrics/")

    assert match.func is metrics_view


def test_graphql_endpoint_basic_query_works(client: Client) -> None:
    """POST /graphql/ should accept JSON and execute a basic query.

    Confirms:
    - schema is loaded
    - endpoint is mounted
    - CSRF exemption works
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
    assert data["data"]["__typename"] == "Query"


def test_metrics_endpoint_returns_prometheus_text(client: Client) -> None:
    """GET /metrics/ must return Prometheus text exposition format."""
    response = client.get("/metrics/")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")

    body = response.content.decode("utf-8")

    # Look for any default or custom metric
    assert (
        "python_info" in body
        or "process_cpu_seconds_total" in body
        or "emails_sent_total" in body
        or "documents_created_total" in body
    )


def test_admin_root_is_mounted(client: Client) -> None:
    """GET /admin/ should load or redirect to login."""
    response = client.get("/admin/")

    assert response.status_code in (200, 302)

    # If redirect, ensure it's going to login
    if response.status_code == 302:
        location = response.headers.get("Location", "")
        assert "/admin/login" in location
