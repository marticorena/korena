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
