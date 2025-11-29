from typing import Optional

import strawberry


@strawberry.type
class HealthStatusType:
    """GraphQL type representing application health."""

    status: str
    db_ok: Optional[bool]
    redis_ok: Optional[bool]
    details: Optional[str]
