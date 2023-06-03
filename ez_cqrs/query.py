"""Query and view base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from ez_cqrs.event import E, EventEnvelope


class Query(ABC, Generic[E]):
    """
    Queries read events as they are committed and provide insight into the system state.

    Each CQRS platform should have one or more queries where it will distribute
    committed events.

    Some examples of tasks that queries commonly provide:
    - update materialized views
    - publish events to messaging service
    - trigger a command on another aggregate
    """

    @abstractmethod
    async def dispatch(self, aggregate_id: str, events: list[EventEnvelope[E]]) -> None:
        """Event will be dispatched here immediately after being committed."""


class View(ABC, Generic[E]):
    """
    A `View` represents a materialized view.

    Generally serialized for persistency, that is updated by a query.

    This is a read element in a CQRS system.
    """

    @abstractmethod
    def update(self, event: EventEnvelope[E]) -> None:
        """
        Each implemented view is responsible for updating its state.

        The events are passed via this method.
        """
