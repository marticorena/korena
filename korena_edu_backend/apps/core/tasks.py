from collections.abc import Callable
from typing import Any

from django.db import transaction


def dispatch_after_commit(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Run a callable only after the current DB transaction commits.

    This is typically used to enqueue Celery tasks that depend on
    recently-created/updated DB rows.

    Example:
        dispatch_after_commit(my_task.delay, instance.id)
    """

    def _wrapper() -> None:
        func(*args, **kwargs)

        return

    transaction.on_commit(_wrapper)

    return
