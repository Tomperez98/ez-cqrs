"""CQRS core components."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from mashumaro import DataClassDictMixin

if TYPE_CHECKING:
    from result import Result


@dataclass(frozen=True)
class Command(DataClassDictMixin):
    """
    Command baseclass.

    In order to make changes to our system we'll need commands. These
    are the simplest components of any CQRS system and consist of little more than
    packaged data.
    """


class Services:
    """
    Services baseclass.

    Business logic doesn't exist in a vacuum and external services may be needed for
    a variety of reasons.
    """


class DomainError(Exception):
    """
    DomainError baseclass.

    These type of errors indicate violation of buisness rules.
    """


@dataclass(frozen=True)
class DomainEvent(ABC, DataClassDictMixin):
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

    @abstractmethod
    def event_type(self) -> str:
        """Event name, used for event upcasting."""

    @abstractmethod
    def event_version(self) -> str:
        """Event type version, used for event upcasting."""


C = TypeVar("C", bound=Command)
E = TypeVar("E", bound=DomainEvent)
S = TypeVar("S", bound=Services)
ERR = TypeVar("ERR", bound=DomainError)


class Aggregate(Generic[C, E, ERR, S]):
    """
    Aggregate base class.

    In CQRS (and Domain Driven Design) an `Aggregate` is the fundamental component that
    encapsulates the state and application logic (aka business rules) for the application.
    An `Aggregate` is always composed of a [DDD entity](https://docs.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model#the-domain-entity-pattern)
    along with all entities and [value objects](https://docs.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model#the-value-object-pattern)
    associated with it.
    """  # noqa: E501

    @abstractmethod
    def aggregate_type(self) -> str:
        """
        Uused as the unique indetifier for this aggregate and its events.

        This is used for persisting the events and snapshots to a database.
        """

    @abstractmethod
    async def handle(
        self,
        command: C,
        services: S | None,
    ) -> Result[list[E], ERR]:
        """
        Consume and process commands.

        The result should be either a vector of events if the command is successful,
        or an error is the command is rejected.

        _All business logic belongs in this method_.
        """

    @abstractmethod
    def apply(self, event: E) -> None:
        """
        Update the aggregate's state once an event has been commited.

        Any events returned from the `handle` method will be applied using this method
        in order to populate the state of the aggregate instance.

        The source of truth used in the CQRS framework determines when the events are
        applied to an aggregate:
        - event sourced - All events are applied every time the aggregate is loaded.
        - aggregate sourced - Events are applied immediately after they are returned
        from `handle` (and before they are committed) and the resulting aggregate
        instance is serilized and persisted.
        - snapshots - Uses a combination of the above patterns.

        _No business logic should be placed here_, this is only used for updating the
        aggregate state.
        """
