"""Event store."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from ez_cqrs.aggregate import A
from ez_cqrs.event import DomainEvent, E, EventEnvelope

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.error import AggregateError


class AggregateContext(ABC, Generic[A]):
    """
    Aggegate as well as the context around it.

    This is used internally within the `EventStore` to persist and aggregate instance
    and events with the correct context after it has beed loaded and modified.
    """

    @abstractmethod
    def aggregate(self) -> A:
        """Aggregate instance with all state loaded."""


class EventStore(ABC, Generic[A, E]):
    """Abstract central source for loading past events and committing new events."""

    @abstractmethod
    async def load_events(
        self,
        aggregate_id: str,
    ) -> Result[EventEnvelope[E], AggregateError]:
        """Load the events for a particular `aggregate_id`."""

    @abstractmethod
    async def load_aggregate(
        self,
        aggregate_id: str,
    ) -> Result[AggregateContext[A], AggregateError]:
        """Load aggregate at current state."""

    @abstractmethod
    async def commit(
        self,
        events: list[DomainEvent],
        context: AggregateContext[A],
        metadata: dict[str, str],
    ) -> Result[list[EventEnvelope[E]], AggregateError]:
        """Commit new events."""
