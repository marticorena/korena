from graphql_jwt.utils import get_payload, get_user_by_payload


def get_user_from_request(request) -> object:
    """Extract and validate user from JWT in request.

    Args:
        request: The HTTP request object.

    Returns:
        object: The user object if authenticated, None otherwise.
    """
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("JWT "):

        return None

    token = auth.split(" ")[1]

    try:
        payload = get_payload(token, context=request)
        user = get_user_by_payload(payload)
        if user and user.is_active:

            return user
    except Exception:

        return None

    return None


def get_metric_value(counter, **labels: str) -> float:
    """Return the value of a labeled Prometheus counter."""
    for metric in counter.collect():
        for sample in metric.samples:
            if sample.labels == labels:
                return float(sample.value)

    return 0.0
