from typing import Any, Dict

import pytest

from tests.test_core.graphql_strings import HEALTHZ_QUERY, READYZ_QUERY

pytestmark = pytest.mark.django_db


def test_healthz_returns_ok_without_dependencies(exec_gql) -> None:
    """healthz should report service alive without checking DB/Redis."""
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
    """readyz should return ok when DB and Redis are healthy."""

    # DB: we trust the test DB connection; no patch needed.
    # Redis: fake a healthy connection with a no-op ping.
    class FakeRedisConn:
        """Fake Redis connection with successful ping."""

        def ping(self) -> None:
            """Simulate successful ping."""

            return

    def fake_get_redis_connection(alias: str) -> FakeRedisConn:
        """Return a fake Redis connection."""
        assert alias == "default"

        return FakeRedisConn()

    monkeypatch.setattr(
        "apps.core.schema.queries.get_redis_connection",
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
    """readyz should report error when DB check fails."""

    def failing_cursor(*args: Any, **kwargs: Any):
        """Simulate DB failure when acquiring cursor."""
        raise Exception("DB unavailable")

    # Patch DB cursor to fail.
    monkeypatch.setattr(
        "apps.core.schema.queries.connection.cursor",
        failing_cursor,
    )

    # Redis: pretend it is healthy so only DB failure matters.
    class FakeRedisConn:
        def ping(self) -> None:
            return

    def fake_get_redis_connection(alias: str) -> FakeRedisConn:
        assert alias == "default"

        return FakeRedisConn()

    monkeypatch.setattr(
        "apps.core.schema.queries.get_redis_connection",
        fake_get_redis_connection,
    )

    result: Dict[str, Any] = exec_gql(READYZ_QUERY)

    data = result["data"]["readyz"]
    assert data["status"] == "error"
    assert data["dbOk"] is False
    assert data["redisOk"] is True
    assert "DB error:" in data["details"]


def test_readyz_returns_error_when_redis_fails(
    exec_gql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """readyz should report error when Redis check fails."""

    # DB: let real connection work.
    # Redis: simulate failure.
    def failing_get_redis_connection(alias: str) -> None:
        raise Exception("Redis unavailable")

    monkeypatch.setattr(
        "apps.core.schema.queries.get_redis_connection",
        failing_get_redis_connection,
    )

    result: Dict[str, Any] = exec_gql(READYZ_QUERY)

    data = result["data"]["readyz"]
    assert data["status"] == "error"
    assert data["dbOk"] is True
    assert data["redisOk"] is False
    assert "Redis error:" in data["details"]
