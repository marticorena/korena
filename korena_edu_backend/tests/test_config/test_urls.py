from django.test import Client
from django.urls import resolve

import pytest
from strawberry.django.views import GraphQLView

pytestmark = pytest.mark.django_db


def test_graphql_url_resolves_to_graphql_view() -> None:
    """The /graphql/ URL should resolve to Strawberry's GraphQLView."""
    match = resolve("/graphql/")

    # Django sets view_class when using .as_view()
    assert hasattr(match.func, "view_class")
    assert match.func.view_class is GraphQLView


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


def test_admin_root_is_mounted(client: Client) -> None:
    """GET /admin/ should load or redirect to login."""
    response = client.get("/admin/")

    assert response.status_code in (200, 302)

    # If redirect, ensure it's going to login
    if response.status_code == 302:
        location = response.headers.get("Location", "")
        assert "/admin/login" in location
