"""Aggregate base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mashumaro import DataClassDictMixin

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.command import Command
    from ez_cqrs.events import DomainEvent
    from ez_cqrs.services import Services


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

    @property
    @abstractmethod
    def aggregate_type(self) -> str:
        """
        The aggregate type is used as the unique indetifier for this aggregate and its events.

        This is used for persisting the events and snapshots to a database.
        """  # noqa: E501

    @abstractmethod
    async def handle(
        self,
        command: Command,
        services: Services | None,
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
