"""Error base class."""
from __future__ import annotations

import sys
from typing import Union

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias  # noqa: TCH002


class UserError(Exception):
    """
    Raised when a user violates a business rule.

    This is the error returned when a user violates a business rule. The payload passed
    should be used to inform the user of the nature of a problem.

    This translates into a `Bad Request` status.
    """

    def __init__(self, business_violation: Exception) -> None:  # noqa: D107
        super().__init__(business_violation)


class AggregateConflictError(Exception):
    """
    Raised when there's another command on the same aggregate instance.

    This is handled by optimistic locking in systems backed by an RDBMS.

    In a Restful app this translates into a `Too Many Requests` or `Service Unavailable`
    response status, often with a [Retry-After response header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After)
    indicating that the user should try again.
    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()


class DatabaseConnectionError(Exception):
    """Raised when an error ocurred while attempting to read/write from a database."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__()


class DeserializationError(Exception):
    """Raised when a deserialization error ocurred due to invalid JSON."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__()


class UnexpectedError(Exception):
    """
    Raised when an unexpected error was encountered.

    A technical error was encountered teht prevented the command from being applied to
    the aggregate. In general the accompanying message should be logged for
    investigation rather than returned to the user.
    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()


AggregateError: TypeAlias = Union[
    UserError,
    AggregateConflictError,
    DatabaseConnectionError,
    DeserializationError,
    UnexpectedError,
]
