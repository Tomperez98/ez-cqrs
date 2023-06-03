"""Cqrs framework implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic

from ez_cqrs.aggregate import A, Services
from ez_cqrs.event import E

if TYPE_CHECKING:
    from ez_cqrs.query import Query
    from ez_cqrs.store import EventStore


@dataclass(repr=False, eq=False)
class CqrsFramework(Generic[A, E]):
    """
    Base framework for applying commands to produce events.

    In [Domain Driven Design](https://en.wikipedia.org/wiki/Domain-driven_design) we
    require that changes are made only after loading the entire `Aggregate` in order to
    ensure that the full context is understood.

    With event-sourcing this means:
    1. Loading all previous events for the aggregate instance.
    2. Applying these events, in order, to a new `Aggregate` in order to reach the
    correct state.
    3. Using the recreated `Aggregate` to handle the inbound `Command` producing events
    or an error.
    4. Persisting any generated events or roll-back in the event of an error.

    To manage these tasks we use the `CqrsFramework`.
    """

    store: EventStore[A, E]
    queries: list[Query[E]]
    service: Services

    def append_query(self, query: Query[E]) -> None:
        """Append an additional query to the framework."""
        self.queries.append(query)
