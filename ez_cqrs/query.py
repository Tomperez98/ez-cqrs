"""Query related definition."""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic

from ez_cqrs.aggregate import E

if TYPE_CHECKING:
    from ez_cqrs.event import EventEnvelope


class Query(abc.ABC, Generic[E]):
    """
    Queries read events as they are committed and provide insight into the system state.

    Each CQRS platform should have one or more queries where it will distribute
    committed events.

    Some examples of tasks that queries commonly provide:
    - update materialized views
    - publish events to messaging service
    - trigger a command on another aggregate
    """

    @abc.abstractmethod
    async def dispatch(self, events: list[EventEnvelope[E]]) -> None:
        """Event will be dispatched here immediately after being committed."""


class View(abc.ABC, Generic[E]):
    """
    A `View` represents a materialized view.

    Generally serialized for persistency, that is updated by a query.

    This is a read element in a CQRS system.
    """

    @abc.abstractmethod
    def update(self, event: EventEnvelope[E]) -> None:
        """
        Each implemented view is responsible for updating its state.

        The events are passed via this method.
        """
