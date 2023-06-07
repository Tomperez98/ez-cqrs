"""Error base class."""
from __future__ import annotations

import abc
import sys
from typing import TYPE_CHECKING, Union

if sys.version_info >= (3, 8):
    from typing import final
else:
    from typing_extensions import final
if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias


class DomainError(abc.ABC, Exception):
    """
    Raised when a user violates a business rule.

    This is the error returned when a user violates a business rule. The payload passed
    should be used to inform the user of the nature of a problem.

    This translates into a `Bad Request` status.
    """


@final
class DatabaseError(Exception):
    """Raised whwne that's an error interacting with system's database."""

    def __init__(self, database_error: Exception) -> None:  # noqa: D107
        super().__init__(f"An error ocurred with database {database_error}")


@final
class UnexpectedError(Exception):
    """
    Raised when an unexpected error was encountered.

    A technical error was encountered teht prevented the command from being applied to
    the aggregate. In general the accompanying message should be logged for
    investigation rather than returned to the user.
    """

    def __init__(self, unexpected_error: Exception) -> None:  # noqa: D107
        super().__init__(f"Unexpected error {unexpected_error}")


ExecutionError: TypeAlias = Union[
    DomainError,
    DatabaseError,
    UnexpectedError,
]
