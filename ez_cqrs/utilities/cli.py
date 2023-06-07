"""CLI utilities to use with ez-cqrs."""
from __future__ import annotations

import asyncio
from functools import wraps
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


class Callback(Protocol):
    """
    Callback protocol for CLI commands.

    See: https://mypy.readthedocs.io/en/latest/protocols.html#callback-protocols
    """

    def __call__(  # type:ignore[no-untyped-def]  # noqa: D102
        self,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> Coroutine[Any, Any, None]:
        ...


def coro(f: Callback) -> Callable[[Any], Any]:
    """Run CLI command as a coroutine."""

    @wraps(f)
    def wrapper(  # type:ignore[no-untyped-def]
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> Any:  # noqa: ANN401
        return asyncio.run(f(*args, **kwargs))

    return wrapper
