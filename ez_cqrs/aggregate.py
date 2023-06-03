"""Aggregate base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from mashumaro import DataClassDictMixin

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.event import DomainEvent


@dataclass(frozen=True)
class Command(ABC, DataClassDictMixin):
    """
    Command base class.

    In order to make changes to our system we'll need commands.
    These are the simplest components of any CQRS system and consist
    of little more than packaged data.

    When designing commands an easy mental model to use is that of an
    HTTP API. Each virtual endpoint would receive just the data needed to
    operate that function.
    """


class Services:
    """
    Services base class.

    Business logic doesn't exist in a vacuum and external services
    may be needed for a variety of reasons.
    """


@dataclass(frozen=False)
class Aggregate(ABC, DataClassDictMixin):
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
        command: Command,
        services: Services,
    ) -> Result[list[DomainEvent], Exception]:
        """
        Consume and process commands.

        The result should be either a vector of events if the command is successful,
        or an error is the command is rejected.

        _All business logic belongs in this method_.
        """

    @abstractmethod
    def apply(self, event: DomainEvent) -> None:
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


A = TypeVar("A", bound=Aggregate)
