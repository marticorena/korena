from typing import Optional

import strawberry


@strawberry.type
class HealthStatusType:
    """Purely recursive type to test QueryDepthLimiter."""

    status: str
    db_ok: Optional[bool]
    redis_ok: Optional[bool]
    details: Optional[str]
