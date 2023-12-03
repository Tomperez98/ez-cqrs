"""CQRS core components."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar, Union, final

from ez_cqrs._typing import T

if TYPE_CHECKING:
    from pydantic import ValidationError
    from result import Result
    from typing_extensions import TypeAlias


@final
@dataclass
class StateChanges(Generic[T]):
    """
    Operations registry.

    The intended use case for `StateChanges` is to act as an ephemeral
    record of update operations against a database in the execution of a command.

    These update operations would be commited as a single, ACID, transaction agains the
    database before the command execution returns the events recorded.
    """

    max_lenght: int
    _storage: list[T] = field(default_factory=list, init=False)

    def is_empty(self) -> bool:
        """Check `StateChanges` storage is empty."""
        return self.storage_length() == 0

    def add(self, value: T) -> None:
        """Add new value to the storage registry."""
        if len(self._storage) >= self.max_lenght:
            msg = "StateChanges capacity exceeded."
            raise RuntimeError(msg)
        self._storage.append(value)

    def prune_storage(self) -> None:
        """Prune storage."""
        self._storage.clear()

    def storage_snapshot(self) -> list[T]:
        """Get an snapshot of the storage."""
        return self._storage.copy()

    def storage_length(self) -> int:
        """Get storage length."""
        return len(self._storage)


class ACID(abc.ABC, Generic[T]):
    """
    Repository gives acces to the system database layer.

    A database must support transaction operations.

    Besides being the client between the core layer and the persistence layer,
    a system repository is intended to be used right before a command handling
    returns. Before events are returned to the client to be propagated to other
    systems, all update operations recorded during the command execution must be
    commited.
    """

    @abc.abstractmethod
    def commit_as_transaction(
        self,
        ops_registry: StateChanges[T],
    ) -> Result[None, DatabaseError]:
        """
        Commit update operations stored in an `StateChanges`.

        The operation is executed as a transaction againts the database.

        After the commit the ops_registry must be pruned.
        """


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
