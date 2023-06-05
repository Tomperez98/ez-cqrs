"""Event store definition."""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic

from ez_cqrs.aggregate import ERR, Aggregate, C, E, S

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.error import AggregateError
    from ez_cqrs.event import EventEnvelope


class AggregateContext(Generic[C, E, ERR, S]):
    """
    Aggregate as well as the context around it.

    This is used internally within the `EventStore` to persist and aggregate instance
    and events with the correct context after it has beed loaded and modified.
    """

    @abc.abstractmethod
    def aggregate(self) -> Aggregate[C, E, ERR, S]:
        """Aggregate instance with all state loaded."""


class EventStore(Generic[C, E, ERR, S]):
    """The abstract central source for loading past events and committing new events."""

    @abc.abstractmethod
    async def load_events(
        self,
        aggregate_id: str,
    ) -> Result[EventEnvelope[E], AggregateError]:
        """Load all events for a particular `aggregate_id`."""

    @abc.abstractmethod
    async def load_aggregate(
        self,
        aggregate_id: str,
    ) -> Result[AggregateContext[C, E, ERR, S], AggregateError]:
        """Load aggregate at current state."""

    @abc.abstractmethod
    async def commit(
        self,
        events: list[E],
        context: AggregateContext[C, E, ERR, S],
        metadata: dict[str, str],
    ) -> Result[list[EventEnvelope[E]], AggregateError]:
        """Commit new events."""
