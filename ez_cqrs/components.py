"""CQRS core components."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar, Union, final

from ez_cqrs._typing import T

if TYPE_CHECKING:
    from pydantic import ValidationError
    from result import Result
    from typing_extensions import TypeAlias

    from ez_cqrs._framework import StateChanges


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


ExecutionError: TypeAlias = Union[DomainError, UnexpectedError, DatabaseError]


@dataclass(frozen=True)
class UseCaseResponse:
    """UseCase Output container."""


R = TypeVar("R", bound=UseCaseResponse)


@dataclass(frozen=True)
class DomainEvent(abc.ABC):
    """
    Domain Event base class.

    A `DomainEvent` represents any business change in the state of an `Aggregate`.
    `DomainEvents` are inmutable, and when [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
    is used they are the single source of truth.

    The name of a `DomainEvent` should always be in the past tense, e.g.,
    - AdminPrivilegesGranted
    - EmailAddressChanged
    - DependencyAdded

    To simplify serialization, an event should be an enum, and each variant should carry
    any important information.
    """

    @abc.abstractmethod
    async def publish(self) -> None:
        """Define how to handle the event."""


E = TypeVar("E", bound=DomainEvent)


@dataclass(frozen=True)
class Command(Generic[E, R, T], abc.ABC):
    """
    Command baseclass.

    In order to make changes to our system we'll need commands. These
    are the simplest components of any CQRS system and consist of little more than
    packaged data.
    """

    @abc.abstractmethod
    def validate(self) -> Result[None, ValidationError]:
        """Validate command using a pydantic schema."""

    @abc.abstractmethod
    async def execute(
        self, events: list[E], state_changes: StateChanges[T]
    ) -> Result[R, ExecutionError]:
        """Execute command."""
