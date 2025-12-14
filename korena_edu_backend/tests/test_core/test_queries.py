from typing import Any, Dict

import pytest

from tests.test_core.graphql_strings import HEALTHZ_QUERY, READYZ_QUERY

pytestmark = pytest.mark.django_db


def test_healthz_returns_ok_without_dependencies(exec_gql) -> None:
    result: Dict[str, Any] = exec_gql(HEALTHZ_QUERY)

    data = result["data"]["healthz"]

    assert data["status"] == "ok"
    assert data["dbOk"] is None
    assert data["redisOk"] is None
    assert data["details"] == "Service is alive"


def test_readyz_returns_ok_when_db_and_redis_ok(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRedisConn:
        def ping(self) -> None:
            return

    def fake_get_redis_connection(alias: str) -> FakeRedisConn:
        return FakeRedisConn()

    monkeypatch.setattr(
        "apps.core.graphql.queries.get_redis_connection",
        fake_get_redis_connection,
    )

    result: Dict[str, Any] = exec_gql(READYZ_QUERY)

    data = result["data"]["readyz"]

    assert data["status"] == "ok"
    assert data["dbOk"] is True
    assert data["redisOk"] is True
    assert data["details"] == "All systems operational"


def test_readyz_returns_error_when_db_fails(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_cursor(*args: Any, **kwargs: Any):
        raise Exception("DB unavailable")

    monkeypatch.setattr(
        "apps.core.graphql.queries.connection.cursor",
        failing_cursor,
    )

    class FakeRedisConn:
        def ping(self) -> None:
            return

    def fake_get_redis_connection(alias: str) -> FakeRedisConn:
        return FakeRedisConn()

    monkeypatch.setattr(
        "apps.core.graphql.queries.get_redis_connection",
        fake_get_redis_connection,
    )

    result: Dict[str, Any] = exec_gql(READYZ_QUERY)

    data = result["data"]["readyz"]

    print(data)

    assert data["status"] == "error"
    assert data["dbOk"] is False
    assert data["redisOk"] is True
    assert "DB error" in data["details"]


def test_readyz_returns_error_when_redis_fails(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_get_redis_connection(alias: str) -> None:
        raise Exception("Redis unavailable")

    monkeypatch.setattr(
        "apps.core.graphql.queries.get_redis_connection",
        failing_get_redis_connection,
    )

    result: Dict[str, Any] = exec_gql(READYZ_QUERY)

    data = result["data"]["readyz"]

    print(data)

    assert data["status"] == "error"
    assert data["dbOk"] is True
    assert data["redisOk"] is False
    assert "Redis error" in data["details"]
