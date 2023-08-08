"""CLI utilities to use with ez-cqrs."""
from __future__ import annotations

import asyncio
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def coro(f: Any) -> Callable[[Any], Any]:  # noqa: ANN401
    """Run CLI command as a coroutine."""

    @wraps(f)
    def wrapper(  # type:ignore[no-untyped-def]
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> Any:  # noqa: ANN401
        return asyncio.run(f(*args, **kwargs))

    return wrapper
