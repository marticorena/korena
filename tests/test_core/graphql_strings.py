"""Core GraphQL operation strings for health/readiness checks in tests."""

HEALTHZ_QUERY = """
query Healthz {
  healthz {
    status
    dbOk
    redisOk
    details
  }
}
"""

READYZ_QUERY = """
query Readyz {
  readyz {
    status
    dbOk
    redisOk
    details
  }
}
"""

__all__ = [
    "HEALTHZ_QUERY",
    "READYZ_QUERY",
]
